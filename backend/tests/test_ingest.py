from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace

import pytest
from conftest import SEED_DIR
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowpilot.core.ingestion import service
from flowpilot.core.ingestion.runner import run_source
from flowpilot.core.ingestion.service import ingest
from flowpilot.core.ingestion.sources.seed import SeedSource
from flowpilot.core.ingestion.types import IncomingAttachment, IncomingEmail
from flowpilot.core.models import Attachment, AuditEvent, Email, EmailStatus, ParseStatus
from flowpilot.core.storage import MemoryStorage


def _email(**overrides: object) -> IncomingEmail:
    base = IncomingEmail(
        message_id="<m1@ozkanrulman.example>",
        from_addr="satis@ozkanrulman.example",
        to_addrs=["satinalma@atlas-endustri.example"],
        subject="Teklif",
        body_text="Teklifimiz ektedir.",
        attachments=[IncomingAttachment("liste.csv", "text/csv", b"Kod;Fiyat\nA;1\n")],
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def _count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_ingest_saves_email_attachments_and_audit(session: Session) -> None:
    storage = MemoryStorage()
    result = ingest(session, storage, _email(), source="test")

    assert result.created
    email = session.get(Email, result.email.id)
    assert email is not None
    assert email.status is EmailStatus.RECEIVED
    assert email.to_addrs == ["satinalma@atlas-endustri.example"]
    [attachment] = email.attachments
    assert attachment.parse_status is ParseStatus.OK
    assert attachment.extracted_text == "Kod\tFiyat\nA\t1"
    assert storage.get(attachment.storage_key) == b"Kod;Fiyat\nA;1\n"

    [event] = session.scalars(select(AuditEvent)).all()
    assert (event.action, event.actor, event.entity_id) == (
        "email.received",
        "system",
        str(email.id),
    )


def test_same_message_id_twice_creates_one_record(session: Session) -> None:
    """Başarı kriteri 6: aynı e-posta iki kez gelince tek kayıt."""
    storage = MemoryStorage()
    first = ingest(session, storage, _email(), source="test")
    second = ingest(session, storage, _email(body_text="farklı gövde"), source="test")

    assert not second.created
    assert second.email.id == first.email.id
    assert _count(session, Email) == 1
    assert _count(session, Attachment) == 1
    actions = session.scalars(select(AuditEvent.action).order_by(AuditEvent.id)).all()
    assert actions == ["email.received", "email.duplicate_ignored"]


def test_same_content_without_message_id_creates_one_record(session: Session) -> None:
    storage = MemoryStorage()
    first = ingest(session, storage, _email(message_id=None), source="imap")
    second = ingest(
        session,
        storage,
        _email(message_id=None, body_text="  Teklifimiz\n ektedir. "),
        source="imap",
    )

    assert first.email.message_id.endswith("@flowpilot.invalid>")
    assert not second.created
    assert _count(session, Email) == 1


def test_same_content_with_new_message_id_is_duplicate(session: Session) -> None:
    storage = MemoryStorage()
    ingest(session, storage, _email(), source="imap")
    second = ingest(session, storage, _email(message_id="<forward@x.example>"), source="imap")
    assert not second.created
    assert _count(session, Email) == 1


def test_different_attachment_is_a_new_email(session: Session) -> None:
    storage = MemoryStorage()
    ingest(session, storage, _email(), source="test")
    other = _email(
        message_id="<m2@x.example>",
        attachments=[IncomingAttachment("liste.csv", "text/csv", b"Kod;Fiyat\nA;2\n")],
    )
    assert ingest(session, storage, other, source="test").created
    assert _count(session, Email) == 2


def test_concurrent_duplicate_returns_existing(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ön kontrolü geçen eşzamanlı bir kopya, tekil kısıtta yakalanır."""
    storage = MemoryStorage()
    first = ingest(session, storage, _email(), source="test")

    real = service._find_duplicate
    calls = iter([None])
    monkeypatch.setattr(
        service, "_find_duplicate", lambda s, m, d: next(calls, None) or real(s, m, d)
    )
    second = ingest(session, storage, _email(), source="test")

    assert not second.created
    assert second.email.id == first.email.id
    assert _count(session, Email) == 1


def test_seed_run_twice_is_idempotent(session: Session) -> None:
    @contextmanager
    def scope() -> Iterator[Session]:
        with session.begin_nested():
            yield session

    storage = MemoryStorage()
    source = SeedSource(SEED_DIR)
    first = run_source(source, scope, storage)
    second = run_source(source, scope, storage)

    assert first.failed == [] and second.failed == []
    assert first.created == 15 and first.duplicates == 0
    assert second.created == 0 and second.duplicates == 15
    assert _count(session, Email) == 15

    statuses = dict(session.execute(select(Attachment.filename, Attachment.parse_status)).all())
    assert statuses["irsaliye-taramasi-HL-55120.png"] is ParseStatus.UNSUPPORTED
    assert statuses["teklif-ozkan-rulman-TK-2611-07.pdf"] is ParseStatus.OK
    assert statuses["teklif-anadolu-rulman-AR-26-1184.xlsx"] is ParseStatus.OK
