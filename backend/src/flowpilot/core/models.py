"""Çekirdek tabloları (v1 kapsamı, bölüm 5).

Departmanların kendi tabloları kendi paketlerindedir.
"""

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Index, String, Text
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


class Priority(enum.StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RouteOrigin(enum.StrEnum):
    AI = "ai"
    MANUAL = "manual"


class RouteStatus(enum.StrEnum):
    OPEN = "open"
    DONE = "done"


class AgentRunStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProposalStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    DEPARTMENT_USER = "department_user"


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
    # Geçerli karar: en son verilen (AI ya da manuel düzeltme). Eski kararlar geçmiş olarak kalır.
    current_decision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "decision.id", ondelete="SET NULL", use_alter=True, name="fk_email_current_decision"
        )
    )

    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="email", cascade="all, delete-orphan", order_by="Attachment.position"
    )
    decisions: Mapped[list["Decision"]] = relationship(
        back_populates="email",
        cascade="all, delete-orphan",
        order_by="Decision.created_at",
        foreign_keys="Decision.email_id",
    )
    current_decision: Mapped["Decision | None"] = relationship(
        foreign_keys=[current_decision_id], post_update=True
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


class Decision(Base):
    """Decision Engine'in bir e-posta için kararı. Silinmez; düzeltme yeni rota ekler."""

    __tablename__ = "decision"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    model: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(32))
    reasoning: Mapped[str] = mapped_column(Text, default="")
    needs_review: Mapped[bool]
    review_reason: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int]
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    email: Mapped[Email] = relationship(back_populates="decisions", foreign_keys=[email_id])
    routes: Mapped[list["Route"]] = relationship(
        back_populates="decision", cascade="all, delete-orphan", order_by="Route.position"
    )

    __table_args__ = (Index("ix_decision_email_id", "email_id"),)


class Route(Base):
    __tablename__ = "route"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decision.id", ondelete="CASCADE"))
    position: Mapped[int]
    department: Mapped[str] = mapped_column(String(64))
    intent: Mapped[str | None] = mapped_column(String(64))
    priority: Mapped[Priority] = mapped_column(_enum(Priority))
    confidence: Mapped[float] = mapped_column(Float)
    suggested_action: Mapped[str] = mapped_column(Text, default="")
    origin: Mapped[RouteOrigin] = mapped_column(_enum(RouteOrigin), default=RouteOrigin.AI)
    status: Mapped[RouteStatus] = mapped_column(_enum(RouteStatus), default=RouteStatus.OPEN)
    done_by: Mapped[str | None] = mapped_column(String(320))
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    decision: Mapped[Decision] = relationship(back_populates="routes")

    __table_args__ = (
        Index("ix_route_decision_id", "decision_id"),
        Index("ix_route_department", "department"),
    )


class AgentRun(Base):
    """Bir departman ajanının bir rota için çalışması (ADR-014). Rota başına bir tane."""

    __tablename__ = "agent_run"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email.id", ondelete="CASCADE"))
    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("route.id", ondelete="CASCADE"), unique=True
    )
    department: Mapped[str] = mapped_column(String(64))
    status: Mapped[AgentRunStatus] = mapped_column(_enum(AgentRunStatus))
    attempts: Mapped[int] = mapped_column(default=1)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    proposals: Mapped[list["Proposal"]] = relationship(
        back_populates="agent_run", order_by="Proposal.created_at"
    )

    __table_args__ = (Index("ix_agent_run_email_id", "email_id"),)


class Proposal(Base):
    """Ajanın önerisi. Yalnızca `core/proposals.execute` uygular; tam bir kez (ADR-014)."""

    __tablename__ = "proposal"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_run.id", ondelete="CASCADE"))
    email_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email.id", ondelete="CASCADE"))
    department: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[ProposalStatus] = mapped_column(_enum(ProposalStatus))
    requires_approval: Mapped[bool] = mapped_column(default=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    decided_by: Mapped[str | None] = mapped_column(String(320))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)

    agent_run: Mapped[AgentRun] = relationship(back_populates="proposals")

    __table_args__ = (
        Index("ix_proposal_email_id", "email_id"),
        Index("ix_proposal_status", "status"),
    )


class Correction(Base):
    """Bir kullanıcının yönlendirme düzeltmesi; değerlendirme setine aday örnektir."""

    __tablename__ = "correction"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email.id", ondelete="CASCADE"))
    from_decision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("decision.id", ondelete="SET NULL")
    )
    to_decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decision.id", ondelete="CASCADE"))
    user_email: Mapped[str] = mapped_column(String(320))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (Index("ix_correction_email_id", "email_id"),)


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(_enum(UserRole))
    departments: Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def can_see(self, department: str) -> bool:
        return self.role is UserRole.ADMIN or department in self.departments


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
