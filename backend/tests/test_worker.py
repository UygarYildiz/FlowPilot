"""İşleyici (ADR-017): sürekli açık posta kutusu, IDLE ile bekleme ve uçtan uca bir tur."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_decision_engine import ScriptedLLM, _decision, route
from test_proposals import Applier, ScriptedAgent, make_department, make_registry, note

from flowpilot.core.decision.engine import LLMClassifier
from flowpilot.core.ingestion.sources.imap import ImapError, ImapMailbox
from flowpilot.core.models import Email, EmailStatus, Proposal
from flowpilot.core.storage import MemoryStorage
from flowpilot.evals.latency import collect, percentile
from flowpilot.worker import known_message_ids, run_cycle, run_worker

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)


def _raw(n: int, *, subject: str | None = None) -> bytes:
    message = EmailMessage()
    message["From"] = "satis@tedarikci.example"
    message["Subject"] = subject or f"Teklif {n}"
    message["Message-ID"] = f"<w{n}@tedarikci.example>"
    message["Date"] = "Fri, 20 Nov 2026 11:59:30 +0000"
    message.set_content(f"Teklifimiz ektedir ({n}).")
    return message.as_bytes()


class FakeConn:
    """imaplib.IMAP4 yerine: UID'li mesajlar, UIDVALIDITY, isteğe bağlı IDLE."""

    def __init__(self, messages: dict[int, bytes], *, idle: bool = True, validity: bytes = b"1"):
        self.messages = messages
        self.capabilities = ("IMAP4REV1", "IDLE") if idle else ("IMAP4REV1",)
        self.validity = validity
        self.commands: list[tuple[Any, ...]] = []
        self.sent: list[bytes] = []
        self.incoming: list[bytes] = []
        self.sock = object()
        self.logged_out = False
        self._tag = 0

    def login(self, user: str, password: str) -> tuple[str, list[bytes]]:
        return "OK", [b""]

    def select(self, folder: str, readonly: bool = False) -> tuple[str, list[bytes]]:
        self.commands.append(("SELECT", folder, readonly))
        return "OK", [str(len(self.messages)).encode()]

    def response(self, code: str) -> tuple[str, list[bytes | None]]:
        return code, [self.validity]

    def uid(self, command: str, *args: Any) -> tuple[str, list[Any]]:
        self.commands.append((command, *args))
        if command == "SEARCH":
            uids = sorted(self.messages)
            if args[0] == "UID":
                start = int(args[1].split(":")[0])
                # Gerçek sunucular gibi: "n:*" en az son mesajı döndürür.
                uids = [u for u in uids if u >= start] or uids[-1:]
            return "OK", [b" ".join(str(u).encode() for u in uids)]
        raw = self.messages[int(args[0])]
        if "HEADER.FIELDS" in args[1]:
            raw = raw.split(b"\n\n", 1)[0] + b"\n\n"
        return "OK", [(b"1 (UID " + args[0] + b" BODY[] {0}", raw), b")"]

    def _new_tag(self) -> bytes:
        self._tag += 1
        return f"T{self._tag}".encode()

    def send(self, data: bytes) -> None:
        self.sent.append(data)
        if data.endswith(b" IDLE\r\n"):
            self.incoming.append(b"+ idling\r\n")
        elif data == b"DONE\r\n":
            self.incoming.append(f"T{self._tag} OK IDLE terminated\r\n".encode())

    def readline(self) -> bytes:
        return self.incoming.pop(0) if self.incoming else b""

    def logout(self) -> None:
        self.logged_out = True


def _mailbox(conn: FakeConn, **kwargs: Any) -> ImapMailbox:
    return ImapMailbox(
        host="imap.example",
        user="u",
        password="p",
        connect=lambda host, port: conn,
        readable=lambda sock, timeout: bool(conn.incoming),
        now=lambda: NOW,
        **kwargs,
    )


def _fetches(conn: FakeConn) -> list[str]:
    return [c[2] for c in conn.commands if c[0] == "FETCH"]


def test_first_scan_skips_known_by_header_then_fetches_only_new_uids() -> None:
    conn = FakeConn({11: _raw(1), 12: _raw(2)})
    mailbox = _mailbox(conn, is_known=lambda mid: mid == "<w1@tedarikci.example>")

    first = list(mailbox.fetch())
    assert [e.subject for e in first] == ["Teklif 2"]
    assert ("SELECT", "INBOX", True) in conn.commands
    assert ("SEARCH", "SINCE", "13-Nov-2026") in conn.commands
    assert all("PEEK" in spec for spec in _fetches(conn))  # okundu işareti konmaz
    assert mailbox.last_uid == 12

    conn.commands.clear()
    assert list(mailbox.fetch()) == []  # "13:*" yalnızca 12'yi döndürür → yeni değil
    assert ("SEARCH", "UID", "13:*") in conn.commands and _fetches(conn) == []

    conn.messages[13] = _raw(3)
    assert [e.subject for e in mailbox.fetch()] == ["Teklif 3"]
    assert _fetches(conn) == ["(BODY.PEEK[])"]  # yeni e-postada başlık ön kontrolü yok


def test_empty_mailbox_then_first_email_arrives() -> None:
    conn = FakeConn({})
    mailbox = _mailbox(conn)
    assert list(mailbox.fetch()) == [] and mailbox.last_uid == 0
    conn.messages[1] = _raw(1)
    assert [e.subject for e in mailbox.fetch()] == ["Teklif 1"]


def test_uidvalidity_change_rescans_from_scratch() -> None:
    conn = FakeConn({5: _raw(1)})
    mailbox = _mailbox(conn)
    list(mailbox.fetch())
    mailbox.close()
    conn.validity = b"2"
    mailbox.open()
    assert mailbox.last_uid is None


def test_idle_returns_when_server_reports_new_mail() -> None:
    conn = FakeConn({})
    mailbox = _mailbox(conn)
    mailbox.open()
    real_send = conn.send

    def send(data: bytes) -> None:
        real_send(data)
        if data.endswith(b" IDLE\r\n"):
            conn.incoming.append(b"* 1 EXISTS\r\n")

    conn.send = send  # type: ignore[method-assign]
    assert mailbox.wait(5) is True
    assert conn.sent[-1] == b"DONE\r\n" and conn.incoming == []


def test_idle_times_out_and_ends_cleanly() -> None:
    conn = FakeConn({})
    mailbox = _mailbox(conn)
    mailbox.open()
    assert mailbox.wait(0.05) is False
    assert conn.sent == [b"T1 IDLE\r\n", b"DONE\r\n"]


def test_idle_dropped_connection_raises() -> None:
    conn = FakeConn({})
    mailbox = ImapMailbox(
        host="h",
        user="u",
        password="p",
        connect=lambda host, port: conn,
        readable=lambda sock, timeout: True,  # okunacak var ama satır boş: bağlantı kapandı
    )
    mailbox.open()
    with pytest.raises(ImapError):
        mailbox.wait(5)


def test_without_idle_support_wait_polls(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []
    monkeypatch.setattr("flowpilot.core.ingestion.sources.imap.time.sleep", slept.append)
    mailbox = _mailbox(FakeConn({}, idle=False))
    mailbox.open()
    assert mailbox.wait(300, poll_seconds=60) is False and slept == [60]


def test_percentile_nearest_rank() -> None:
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert percentile([4, 1, 3], 50) == 3


# ---------- Veritabanıyla ----------


@pytest.fixture
def scope(session: Session):  # noqa: ANN201
    @contextmanager
    def _scope() -> Iterator[Session]:
        with session.begin_nested():
            yield session

    return _scope


def test_cycle_takes_new_mail_to_a_pending_proposal(session: Session, scope: Any) -> None:
    conn = FakeConn({1: _raw(1)})
    mailbox = _mailbox(conn, is_known=known_message_ids(scope))
    registry = make_registry(make_department(ScriptedAgent([note()]), Applier()))
    llm = ScriptedLLM(_decision(route("test_dept", "note_it", 0.95)))
    classifier = LLMClassifier(llm, registry, "m")

    report = run_cycle(
        mailbox,
        session_scope=scope,
        storage=MemoryStorage(),
        classifier=classifier,
        registry=registry,
    )
    assert report.ingest.created == 1 and report.classify.routed == 1
    assert report.agents.succeeded == 1 and report.agents.proposals == 1

    email = session.scalars(select(Email).where(Email.message_id == "<w1@tedarikci.example>")).one()
    assert email.source == "imap" and email.status is EmailStatus.AWAITING_APPROVAL
    assert session.scalars(select(Proposal).where(Proposal.email_id == email.id)).one()

    rows = [r for r in collect(session) if r.subject == "Teklif 1"]
    assert rows and rows[0].to_decision is not None and rows[0].to_proposal is not None

    # Yeniden başlatılan işleyici kayıtlı e-postayı başlığından tanır, gövdesini indirmez.
    conn2 = FakeConn({1: _raw(1)})
    restarted = _mailbox(conn2, is_known=known_message_ids(scope))
    again = run_cycle(
        restarted,
        session_scope=scope,
        storage=MemoryStorage(),
        classifier=classifier,
        registry=registry,
    )
    assert again.ingest.created == 0 and not again.did_work
    assert _fetches(conn2) == ["(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"]


def test_worker_reconnects_after_connection_error(session: Session, scope: Any) -> None:
    conns = [FakeConn({}), FakeConn({1: _raw(7)})]
    opened: list[FakeConn] = []

    def connect(host: str, port: int) -> FakeConn:
        conn = conns.pop(0)
        opened.append(conn)
        return conn

    mailbox = ImapMailbox(
        host="h",
        user="u",
        password="p",
        connect=connect,
        readable=lambda sock, timeout: True,  # ilk IDLE'da bağlantı kopar
        now=lambda: NOW,
    )
    registry = make_registry(make_department(ScriptedAgent([note()]), Applier()))
    llm = ScriptedLLM(_decision(route("test_dept", "note_it", 0.95)))
    slept: list[float] = []

    def should_stop() -> bool:
        # İkinci bağlantıda bir tur atıldıysa dur.
        return len(opened) == 2 and any(c[0] == "FETCH" for c in opened[1].commands)

    run_worker(
        mailbox,
        session_scope=scope,
        storage=MemoryStorage(),
        classifier=LLMClassifier(llm, registry, "m"),
        registry=registry,
        should_stop=should_stop,
        sleep=slept.append,
    )
    assert slept == [5.0] and opened[0].logged_out and opened[1].logged_out
    assert session.scalars(select(Email).where(Email.message_id == "<w7@tedarikci.example>")).one()
