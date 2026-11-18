from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Any

import pytest

from flowpilot.core.ingestion.sources.imap import ImapError, ImapSource, imap_date


def _raw(subject: str) -> bytes:
    message = EmailMessage()
    message["From"] = "operasyon@hizlilojistik.example"
    message["Subject"] = subject
    message["Message-ID"] = f"<{subject}@hizlilojistik.example>"
    message.set_content("Sevkiyat gecikti.")
    return message.as_bytes()


class FakeImap:
    def __init__(self, messages: dict[bytes, bytes], login_ok: bool = True) -> None:
        self.messages = messages
        self.login_ok = login_ok
        self.commands: list[tuple[Any, ...]] = []
        self.logged_out = False

    def login(self, user: str, password: str) -> tuple[str, list[bytes]]:
        return ("OK" if self.login_ok else "NO", [b""])

    def select(self, folder: str, readonly: bool = False) -> tuple[str, list[bytes]]:
        self.commands.append(("SELECT", folder, readonly))
        return "OK", [b"2"]

    def uid(self, command: str, *args: Any) -> tuple[str, list[Any]]:
        self.commands.append((command, *args))
        if command == "SEARCH":
            return "OK", [b" ".join(self.messages)]
        uid = args[0]
        return "OK", [(b"1 (UID " + uid + b" BODY[] {0}", self.messages[uid]), b")"]

    def logout(self) -> None:
        self.logged_out = True


def _source(conn: FakeImap) -> ImapSource:
    return ImapSource(
        host="imap.example",
        user="u",
        password="p",
        since_days=7,
        connect=lambda host, port: conn,
        now=datetime(2026, 11, 18, tzinfo=UTC),
    )


def test_fetches_read_only_without_marking_seen() -> None:
    conn = FakeImap({b"11": _raw("HL-1"), b"12": _raw("HL-2")})
    emails = list(_source(conn).fetch())

    assert [e.subject for e in emails] == ["HL-1", "HL-2"]
    assert ("SELECT", "INBOX", True) in conn.commands
    assert ("SEARCH", "SINCE", "11-Nov-2026") in conn.commands
    assert all(c[2] == "(BODY.PEEK[])" for c in conn.commands if c[0] == "FETCH")
    assert conn.logged_out


def test_failed_login_raises_and_logs_out() -> None:
    conn = FakeImap({}, login_ok=False)
    with pytest.raises(ImapError):
        list(_source(conn).fetch())
    assert conn.logged_out


def test_imap_date_is_locale_independent() -> None:
    assert imap_date(datetime(2026, 3, 5)) == "05-Mar-2026"
