from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from flowpilot.core.models import (
    AgentRunStatus,
    EmailStatus,
    ParseStatus,
    Priority,
    ProposalStatus,
    RouteOrigin,
    RouteStatus,
    UserRole,
)


class UserOut(BaseModel):
    email: str
    name: str
    role: UserRole
    departments: list[str]


class LoginIn(BaseModel):
    email: str
    password: str


class IntentOut(BaseModel):
    key: str
    label: str
    description: str


class DepartmentOut(BaseModel):
    key: str
    name: str
    description: str
    intents: list[IntentOut]
    open_count: int


class CountsOut(BaseModel):
    all: int
    needs_review: int
    awaiting_approval: int
    departments: list[DepartmentOut]


class RouteOut(BaseModel):
    id: UUID
    department: str
    intent: str | None
    priority: Priority
    confidence: float
    suggested_action: str
    origin: RouteOrigin
    status: RouteStatus
    done_by: str | None
    done_at: datetime | None


class EmailListItem(BaseModel):
    id: UUID
    from_addr: str
    subject: str
    snippet: str
    received_at: datetime
    status: EmailStatus
    attachment_count: int
    routes: list[RouteOut]


class EmailListOut(BaseModel):
    items: list[EmailListItem]
    total: int


class AttachmentOut(BaseModel):
    id: UUID
    filename: str
    mime: str
    size: int
    parse_status: ParseStatus
    parse_error: str | None
    text_preview: str | None
    text_truncated: bool


class DecisionOut(BaseModel):
    id: UUID
    created_at: datetime
    model: str
    prompt_version: str
    reasoning: str
    needs_review: bool
    review_reason: str | None
    routes: list[RouteOut]


class EventOut(BaseModel):
    at: datetime
    actor: str
    action: str
    data: dict[str, Any]


class ProposalOut(BaseModel):
    id: UUID
    department: str
    type: str
    type_label: str
    summary: str
    payload: dict[str, Any]
    status: ProposalStatus
    requires_approval: bool
    created_at: datetime
    decided_by: str | None
    decided_at: datetime | None
    reason: str | None
    executed_at: datetime | None
    attempts: int
    result: dict[str, Any] | None
    error: str | None
    current: bool


class AgentRunOut(BaseModel):
    id: UUID
    department: str
    status: AgentRunStatus
    attempts: int
    error: str | None
    started_at: datetime
    finished_at: datetime | None


class EmailDetail(BaseModel):
    id: UUID
    message_id: str
    source: str
    from_addr: str
    to_addrs: list[str]
    cc_addrs: list[str]
    subject: str
    body_text: str
    received_at: datetime
    status: EmailStatus
    attachments: list[AttachmentOut]
    current_decision: DecisionOut | None
    previous_decisions: list[DecisionOut]
    agent_runs: list[AgentRunOut]
    proposals: list[ProposalOut]
    events: list[EventOut]


class RouteIn(BaseModel):
    department: str
    intent: str
    priority: Priority = Priority.NORMAL
    suggested_action: str = ""


class CorrectionIn(BaseModel):
    routes: list[RouteIn] = Field(min_length=1)
    reason: str


class ReasonIn(BaseModel):
    reason: str = ""


class AuditItem(BaseModel):
    id: int
    at: datetime
    actor: str
    action: str
    entity_type: str
    entity_id: str
    email_subject: str | None
    data: dict[str, Any]


class AuditOut(BaseModel):
    items: list[AuditItem]
    total: int
