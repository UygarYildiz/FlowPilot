"""Çekirdek tabloları (v1 kapsamı, bölüm 5).

Departmanların kendi tabloları kendi paketlerindedir.
"""

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flowpilot.core.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


def _enum(cls: type[enum.Enum]) -> Enum:
    # Veritabanına üye adları değil değerleri yazılır; yeni değer için göç yeterli.
    return Enum(cls, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e])


class EmailStatus(enum.StrEnum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    ROUTED = "routed"
    NEEDS_REVIEW = "needs_review"
    PROCESSING = "processing"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"


class ParseStatus(enum.StrEnum):
    OK = "ok"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class Email(Base):
    __tablename__ = "email"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[str] = mapped_column(String(998), unique=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(32))
    from_addr: Mapped[str] = mapped_column(String(320))
    to_addrs: Mapped[list[str]] = mapped_column(ARRAY(String(320)), default=list)
    cc_addrs: Mapped[list[str]] = mapped_column(ARRAY(String(320)), default=list)
    subject: Mapped[str] = mapped_column(Text, default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    status: Mapped[EmailStatus] = mapped_column(_enum(EmailStatus), default=EmailStatus.RECEIVED)

    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="email", cascade="all, delete-orphan", order_by="Attachment.position"
    )


class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email.id", ondelete="CASCADE"))
    position: Mapped[int]
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(255))
    size: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(512))
    parse_status: Mapped[ParseStatus] = mapped_column(_enum(ParseStatus))
    parse_error: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)

    email: Mapped[Email] = relationship(back_populates="attachments")

    __table_args__ = (Index("ix_attachment_email_id", "email_id"),)


class AuditEvent(Base):
    """Denetim kaydı: yalnızca eklenir, güncellenmez ve silinmez."""

    __tablename__ = "audit_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    __table_args__ = (Index("ix_audit_event_entity", "entity_type", "entity_id"),)
