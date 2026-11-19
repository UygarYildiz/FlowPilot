from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from sqlalchemy import ColumnElement, and_, exists, func, or_, select
from sqlalchemy.orm import selectinload

from flowpilot.api.deps import (
    SESSION_USER_KEY,
    AdminUser,
    CurrentUser,
    Db,
    Registry,
    Storage,
)
from flowpilot.api.schemas import (
    AttachmentOut,
    CorrectionIn,
    CountsOut,
    DecisionOut,
    DepartmentOut,
    EmailDetail,
    EmailListItem,
    EmailListOut,
    EventOut,
    IntentOut,
    LoginIn,
    ReasonIn,
    RouteOut,
    UserOut,
)
from flowpilot.core.models import (
    Attachment,
    AuditEvent,
    Decision,
    Email,
    EmailStatus,
    Route,
    RouteStatus,
    User,
    UserRole,
)
from flowpilot.core.users import authenticate
from flowpilot.core.workflow import (
    RouteInput,
    WorkflowError,
    correct_routes,
    dismiss,
    mark_route_done,
)

router = APIRouter(prefix="/api")

TEXT_PREVIEW_CHARS = 6000
SNIPPET_CHARS = 140


# ---------- Giriş ----------


def _user_out(user: User) -> UserOut:
    return UserOut(email=user.email, name=user.name, role=user.role, departments=user.departments)


@router.post("/auth/login")
def login(body: LoginIn, request: Request, db: Db) -> UserOut:
    user = authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-posta veya şifre hatalı.")
    request.session.clear()
    request.session[SESSION_USER_KEY] = str(user.id)
    return _user_out(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> None:
    request.session.clear()


@router.get("/auth/me")
def me(user: CurrentUser) -> UserOut:
    return _user_out(user)


# ---------- Görünürlük ----------


def _route_on_current(*conditions: ColumnElement[bool]) -> ColumnElement[bool]:
    return exists(
        select(Route.id).where(Route.decision_id == Email.current_decision_id, *conditions)
    )


def _visible(user: User) -> list[ColumnElement[bool]]:
    """Departman kullanıcısı yalnızca kendi departmanına yönlenmiş, incelemede olmayanları görür."""
    if user.role is UserRole.ADMIN:
        return []
    return [
        Email.status != EmailStatus.NEEDS_REVIEW,
        _route_on_current(Route.department.in_(user.departments)),
    ]


def _get_visible_email(db: Db, email_id: UUID, user: User) -> Email:
    email = db.scalars(select(Email).where(Email.id == email_id, *_visible(user))).first()
    if email is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "E-posta bulunamadı.")
    return email


# ---------- Departmanlar ve sayaçlar ----------


@router.get("/counts")
def counts(user: CurrentUser, db: Db, registry: Registry) -> CountsOut:
    visible = _visible(user)
    total = db.scalar(select(func.count()).select_from(Email).where(*visible)) or 0
    review = 0
    if user.role is UserRole.ADMIN:
        review = (
            db.scalar(
                select(func.count())
                .select_from(Email)
                .where(Email.status == EmailStatus.NEEDS_REVIEW)
            )
            or 0
        )
    open_by_department = dict(
        db.execute(
            select(Route.department, func.count())
            .join(Email, Email.current_decision_id == Route.decision_id)
            .where(Route.status == RouteStatus.OPEN, Email.status != EmailStatus.NEEDS_REVIEW)
            .group_by(Route.department)
        ).all()
    )
    departments = [
        DepartmentOut(
            key=d.key,
            name=d.name,
            description=d.description,
            intents=[
                IntentOut(key=i.key, label=i.label or i.key, description=i.description)
                for i in d.intents
            ],
            open_count=open_by_department.get(d.key, 0),
        )
        for d in registry
        if user.can_see(d.key)
    ]
    return CountsOut(all=total, needs_review=review, departments=departments)


# ---------- E-postalar ----------


def _route_out(route: Route) -> RouteOut:
    return RouteOut.model_validate(route, from_attributes=True)


def _decision_out(decision: Decision) -> DecisionOut:
    return DecisionOut(
        id=decision.id,
        created_at=decision.created_at,
        model=decision.model,
        prompt_version=decision.prompt_version,
        reasoning=decision.reasoning,
        needs_review=decision.needs_review,
        review_reason=decision.review_reason,
        routes=[_route_out(r) for r in decision.routes],
    )


@router.get("/emails")
def list_emails(
    user: CurrentUser,
    db: Db,
    view: Literal["all", "review", "department"] = "all",
    department: str | None = None,
    route_status: Literal["open", "done", "any"] = "open",
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> EmailListOut:
    conditions = _visible(user)
    if view == "review":
        if user.role is not UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "İnceleme kuyruğu yöneticiler içindir.")
        conditions.append(Email.status == EmailStatus.NEEDS_REVIEW)
    elif view == "department":
        if not department or not user.can_see(department):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Departman bulunamadı.")
        route_conditions = [Route.department == department]
        if route_status != "any":
            route_conditions.append(Route.status == RouteStatus(route_status))
        conditions += [
            Email.status != EmailStatus.NEEDS_REVIEW,
            _route_on_current(and_(*route_conditions)),
        ]
    if q:
        pattern = f"%{q.strip()}%"
        conditions.append(
            or_(
                Email.subject.ilike(pattern),
                Email.from_addr.ilike(pattern),
                Email.body_text.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(Email).where(*conditions)) or 0
    emails = db.scalars(
        select(Email)
        .where(*conditions)
        .options(
            selectinload(Email.current_decision).selectinload(Decision.routes),
            selectinload(Email.attachments),
        )
        .order_by(Email.received_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    items = [
        EmailListItem(
            id=e.id,
            from_addr=e.from_addr,
            subject=e.subject,
            snippet=" ".join(e.body_text.split())[:SNIPPET_CHARS],
            received_at=e.received_at,
            status=e.status,
            attachment_count=len(e.attachments),
            routes=[
                _route_out(r) for r in (e.current_decision.routes if e.current_decision else [])
            ],
        )
        for e in emails
    ]
    return EmailListOut(items=items, total=total)


@router.get("/emails/{email_id}")
def email_detail(email_id: UUID, user: CurrentUser, db: Db) -> EmailDetail:
    email = _get_visible_email(db, email_id, user)
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.entity_type == "email", AuditEvent.entity_id == str(email.id))
        .order_by(AuditEvent.at, AuditEvent.id)
    ).all()
    current = email.current_decision
    return EmailDetail(
        id=email.id,
        message_id=email.message_id,
        source=email.source,
        from_addr=email.from_addr,
        to_addrs=email.to_addrs,
        cc_addrs=email.cc_addrs,
        subject=email.subject,
        body_text=email.body_text,
        received_at=email.received_at,
        status=email.status,
        attachments=[
            AttachmentOut(
                id=a.id,
                filename=a.filename,
                mime=a.mime,
                size=a.size,
                parse_status=a.parse_status,
                parse_error=a.parse_error,
                text_preview=a.extracted_text[:TEXT_PREVIEW_CHARS] if a.extracted_text else None,
                text_truncated=bool(
                    a.extracted_text and len(a.extracted_text) > TEXT_PREVIEW_CHARS
                ),
            )
            for a in email.attachments
        ],
        current_decision=_decision_out(current) if current else None,
        previous_decisions=[
            _decision_out(d)
            for d in reversed(email.decisions)
            if current is None or d.id != current.id
        ],
        events=[EventOut(at=e.at, actor=e.actor, action=e.action, data=e.data) for e in events],
    )


@router.get("/emails/{email_id}/attachments/{attachment_id}")
def download_attachment(
    email_id: UUID, attachment_id: UUID, user: CurrentUser, db: Db, storage: Storage
) -> Response:
    email = _get_visible_email(db, email_id, user)
    attachment = next((a for a in email.attachments if a.id == attachment_id), None)
    if attachment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ek bulunamadı.")
    return _file_response(attachment, storage.get(attachment.storage_key))


def _file_response(attachment: Attachment, data: bytes) -> Response:
    from urllib.parse import quote

    return Response(
        content=data,
        media_type=attachment.mime or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(attachment.filename)}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/emails/{email_id}/correction")
def correct(
    email_id: UUID, body: CorrectionIn, user: CurrentUser, db: Db, registry: Registry
) -> EmailDetail:
    email = _get_visible_email(db, email_id, user)
    try:
        correct_routes(
            db,
            email,
            [
                RouteInput(r.department, r.intent, r.priority, r.suggested_action)
                for r in body.routes
            ],
            reason=body.reason,
            user=user,
            registry=registry,
        )
    except WorkflowError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    db.flush()
    db.expire(email)
    return email_detail(email_id, user, db)


@router.post("/emails/{email_id}/dismiss")
def dismiss_email(email_id: UUID, body: ReasonIn, user: AdminUser, db: Db) -> EmailDetail:
    email = _get_visible_email(db, email_id, user)
    try:
        dismiss(db, email, reason=body.reason, user=user)
    except WorkflowError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    db.flush()
    return email_detail(email_id, user, db)


@router.post("/routes/{route_id}/done")
def route_done(route_id: UUID, body: ReasonIn, user: CurrentUser, db: Db) -> EmailDetail:
    route = db.get(Route, route_id)
    if route is None or not user.can_see(route.department):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rota bulunamadı.")
    try:
        mark_route_done(db, route, user=user, note=body.reason)
    except WorkflowError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    db.flush()
    return email_detail(route.decision.email_id, user, db)
