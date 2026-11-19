"""Panelden yapılan işlemler: rota düzeltme, rotayı işlendi olarak kapatma, e-postayı yok sayma.

Her işlem denetim kaydına yazılır. Kararlar silinmez: düzeltme yeni bir (manuel) karar ekler ve
e-postanın geçerli kararı olur; eski karar geçmişte kalır.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from flowpilot.core import audit
from flowpilot.core.models import (
    Correction,
    Decision,
    Email,
    EmailStatus,
    Priority,
    Route,
    RouteOrigin,
    RouteStatus,
    User,
)
from flowpilot.core.registry import DepartmentRegistry

MANUAL_MODEL = "manual"


class WorkflowError(ValueError):
    """Kullanıcıya gösterilebilecek iş kuralı hatası."""


@dataclass(frozen=True)
class RouteInput:
    department: str
    intent: str
    priority: Priority = Priority.NORMAL
    suggested_action: str = ""


def _actor(user: User) -> str:
    return f"user:{user.email}"


def correct_routes(
    session: Session,
    email: Email,
    routes: list[RouteInput],
    *,
    reason: str,
    user: User,
    registry: DepartmentRegistry,
) -> Decision:
    if not reason.strip():
        raise WorkflowError("Düzeltme için gerekçe yazılmalı.")
    if not routes:
        raise WorkflowError(
            "En az bir departman seçilmeli. İlgisiz e-posta için 'Yok say' kullanın."
        )
    if len({r.department for r in routes}) != len(routes):
        raise WorkflowError("Aynı departman iki kez seçilemez.")
    for route in routes:
        department = registry.get(route.department)
        if department is None:
            raise WorkflowError(f"Bilinmeyen departman: {route.department}")
        if route.intent not in department.intent_keys():
            raise WorkflowError(f"{department.name} için geçersiz e-posta türü: {route.intent}")

    previous = email.current_decision
    decision = Decision(
        email=email,
        model=MANUAL_MODEL,
        prompt_version="-",
        reasoning=reason.strip(),
        needs_review=False,
        review_reason=None,
        attempts=0,
    )
    for position, route in enumerate(routes):
        decision.routes.append(
            Route(
                position=position,
                department=route.department,
                intent=route.intent,
                priority=route.priority,
                confidence=1.0,
                suggested_action=route.suggested_action,
                origin=RouteOrigin.MANUAL,
            )
        )
    session.add(decision)
    email.current_decision = decision
    email.status = EmailStatus.ROUTED
    session.flush()

    session.add(
        Correction(
            email_id=email.id,
            from_decision_id=previous.id if previous else None,
            to_decision_id=decision.id,
            user_email=user.email,
            reason=reason.strip(),
        )
    )
    audit.record(
        session,
        actor=_actor(user),
        action="email.rerouted",
        entity_type="email",
        entity_id=email.id,
        data={
            "from": [
                {"department": r.department, "intent": r.intent}
                for r in (previous.routes if previous else [])
            ],
            "to": [{"department": r.department, "intent": r.intent} for r in routes],
            "reason": reason.strip(),
        },
    )
    return decision


def mark_route_done(session: Session, route: Route, *, user: User, note: str = "") -> None:
    email = route.decision.email
    if email.current_decision_id != route.decision_id:
        raise WorkflowError("Bu rota artık geçerli değil (yönlendirme düzeltilmiş).")
    if not user.can_see(route.department):
        raise WorkflowError("Bu departmanın işini kapatma yetkiniz yok.")
    if route.status is RouteStatus.DONE:
        return
    route.status = RouteStatus.DONE
    route.done_by = user.email
    route.done_at = datetime.now(UTC)
    if all(r.status is RouteStatus.DONE for r in route.decision.routes):
        email.status = EmailStatus.DONE
    audit.record(
        session,
        actor=_actor(user),
        action="route.done",
        entity_type="email",
        entity_id=email.id,
        data={"route_id": str(route.id), "department": route.department, "note": note},
    )


def dismiss(session: Session, email: Email, *, reason: str, user: User) -> None:
    """İlgisiz e-postayı (reklam, iş başvurusu…) hiçbir departmana göndermeden kapatır."""
    if not reason.strip():
        raise WorkflowError("Yok saymak için gerekçe yazılmalı.")
    email.status = EmailStatus.DONE
    audit.record(
        session,
        actor=_actor(user),
        action="email.dismissed",
        entity_type="email",
        entity_id=email.id,
        data={"reason": reason.strip()},
    )
