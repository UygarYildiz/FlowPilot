from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from flowpilot.core.models import (
    EmailStatus,
    ParseStatus,
    Priority,
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
