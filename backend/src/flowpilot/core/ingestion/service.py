"""E-postayı ekleriyle tek bir işlemde kaydeder; aynı e-posta ikinci kez kayıt açmaz."""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flowpilot.core import audit
from flowpilot.core.ingestion.extract import extract_text
from flowpilot.core.ingestion.types import IncomingEmail
from flowpilot.core.models import Attachment, Email
from flowpilot.core.storage import AttachmentStorage

_SEPARATOR = chr(31)  # birim ayırıcı: alan içeriklerinde geçmez


@dataclass(frozen=True)
class IngestResult:
    email: Email
    created: bool


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(incoming: IncomingEmail) -> str:
    """Tarihten bağımsız içerik özeti: gönderen, konu, gövde ve eklerin özetleri."""
    parts = [
        incoming.from_addr.strip().lower(),
        incoming.subject.strip(),
        " ".join(incoming.body_text.split()),
        *sorted(sha256(a.content) for a in incoming.attachments),
    ]
    return sha256(_SEPARATOR.join(parts).encode("utf-8"))


def _find_duplicate(session: Session, message_id: str, digest: str) -> Email | None:
    query = select(Email).where(or_(Email.message_id == message_id, Email.content_hash == digest))
    return session.scalars(query.limit(1)).first()


def ingest(
    session: Session, storage: AttachmentStorage, incoming: IncomingEmail, *, source: str
) -> IngestResult:
    """Tekrar önleme: aynı `Message-ID` ya da aynı içerik özeti varsa mevcut kayıt döner.

    `Message-ID` yoksa içerik özetinden kararlı bir kimlik üretilir.
    Ekler içerik adresli saklanır (`sha256/...`): yarım kalan bir kayıt depoda zararsız
    bir dosya bırakır ve aynı ek iki kez yazılmaz.
    """
    digest = content_hash(incoming)
    message_id = incoming.message_id or f"<{digest}@flowpilot.invalid>"

    if (existing := _find_duplicate(session, message_id, digest)) is not None:
        audit.record(
            session,
            actor=audit.SYSTEM,
            action="email.duplicate_ignored",
            entity_type="email",
            entity_id=existing.id,
            data={"source": source, "message_id": message_id},
        )
        return IngestResult(existing, created=False)

    email = Email(
        id=uuid.uuid4(),
        message_id=message_id,
        content_hash=digest,
        source=source,
        from_addr=incoming.from_addr,
        to_addrs=list(incoming.to_addrs),
        cc_addrs=list(incoming.cc_addrs),
        subject=incoming.subject,
        body_text=incoming.body_text,
        received_at=incoming.received_at or datetime.now(UTC),
    )
    for position, item in enumerate(incoming.attachments):
        file_hash = sha256(item.content)
        key = f"sha256/{file_hash[:2]}/{file_hash}"
        storage.put(key, item.content)
        extraction = extract_text(item.filename, item.mime, item.content)
        email.attachments.append(
            Attachment(
                position=position,
                filename=item.filename,
                mime=item.mime,
                size=len(item.content),
                sha256=file_hash,
                storage_key=key,
                parse_status=extraction.status,
                parse_error=extraction.error,
                extracted_text=extraction.text,
            )
        )

    try:
        with session.begin_nested():
            session.add(email)
            session.flush()
    except IntegrityError:
        # Aynı e-posta eşzamanlı başka bir işlemle kaydedildi.
        session.expunge(email)
        existing = _find_duplicate(session, message_id, digest)
        if existing is None:
            raise
        return IngestResult(existing, created=False)

    audit.record(
        session,
        actor=audit.SYSTEM,
        action="email.received",
        entity_type="email",
        entity_id=email.id,
        data={
            "source": source,
            "message_id": message_id,
            "attachments": [
                {"filename": a.filename, "parse_status": a.parse_status.value}
                for a in email.attachments
            ],
        },
    )
    return IngestResult(email, created=True)
