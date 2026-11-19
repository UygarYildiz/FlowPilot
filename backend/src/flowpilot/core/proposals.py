"""Ajan çalıştırma, öneri yaşam döngüsü ve tek yürütücü (ADR-014, v1 kapsamı 3.4).

    pending → approved → executed
    pending → rejected
    approved → failed → (yeniden dene) → executed

Kurallar:
- Ajan veriyi değiştirmez; yalnızca `ProposalDraft` döndürür. Kaydı burası yapar.
- `execute` tek yürütücüdür: satırı kilitler, `executed` ise hiçbir şey yapmaz, `apply`'ı
  durum değişikliğiyle aynı işlemde (SAVEPOINT) çalıştırır. Onaylanan tam bir kez uygulanır;
  reddedilen ve bekleyen hiç uygulanmaz (başarı kriteri 7).
"""

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot.core import audit
from flowpilot.core.models import (
    AgentRun,
    AgentRunStatus,
    Email,
    EmailStatus,
    Proposal,
    ProposalStatus,
    Route,
    User,
)
from flowpilot.core.registry import (
    AgentContext,
    ApplyContext,
    AttachmentText,
    DepartmentRegistry,
    NoTools,
    ProposalDraft,
    Tool,
    Tools,
)
from flowpilot.llm import LLMUnavailableError

SYSTEM_ACTOR = "system"


class ProposalError(ValueError):
    """Kullanıcıya gösterilebilecek öneri iş kuralı hatası."""


def _now() -> datetime:
    return datetime.now(UTC)


def _user_actor(user: User) -> str:
    return f"user:{user.email}"


def idempotency_key(route_id: object, draft: ProposalDraft) -> str:
    canonical = json.dumps(draft.payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(f"{route_id}|{draft.type}|{canonical}".encode()).hexdigest()


class ToolBox:
    """Departman araçlarını salt-okunur çalıştırır: her çağrı geri alınan SAVEPOINT içindedir."""

    def __init__(self, session: Session, tools: Iterable[Tool]) -> None:
        self._session = session
        self._tools = {tool.name: tool for tool in tools}
        self.calls: list[str] = []

    def call(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Araç yok: {name}")
        self.calls.append(name)
        nested = self._session.begin_nested()
        try:
            return tool.fn(self._session, **kwargs)
        finally:
            nested.rollback()


def agent_context(route: Route, tools: Tools | None = None) -> AgentContext:
    email = route.decision.email
    return AgentContext(
        email_id=str(email.id),
        from_addr=email.from_addr,
        to_addrs=tuple(email.to_addrs),
        cc_addrs=tuple(email.cc_addrs),
        subject=email.subject,
        body_text=email.body_text,
        attachments=tuple(AttachmentText(a.filename, a.extracted_text) for a in email.attachments),
        department=route.department,
        intent=route.intent,
        priority=route.priority.value,
        tools=tools or NoTools(),
    )


# ---------- Ajan çalıştırma ----------


def run_agent(session: Session, route: Route, *, registry: DepartmentRegistry) -> AgentRun | None:
    """Rotanın departman ajanını çalıştırır ve önerileri kaydeder.

    Ajanı olmayan departman için `None`. Rota için başarılı bir çalışma varsa onu döndürür
    (yeniden çalıştırmaz); başarısız çalışma yeniden denenir. Model erişilemezse
    (`LLMUnavailableError`) hata yukarı çıkar ve çağıranın işlemi geri alınır.
    """
    department = registry.get(route.department)
    if department is None or department.agent is None:
        return None
    email = route.decision.email
    if email.current_decision_id != route.decision_id:
        raise ProposalError("Bu rota artık geçerli değil (yönlendirme düzeltilmiş).")

    run = session.scalars(select(AgentRun).where(AgentRun.route_id == route.id)).first()
    if run is not None and run.status is not AgentRunStatus.FAILED:
        return run
    if run is None:
        run = AgentRun(
            email_id=email.id,
            route_id=route.id,
            department=department.key,
            status=AgentRunStatus.RUNNING,
            attempts=1,
        )
        session.add(run)
    else:
        run.status, run.attempts, run.error, run.started_at = (
            AgentRunStatus.RUNNING,
            run.attempts + 1,
            None,
            _now(),
        )
    session.flush()
    actor = f"agent:{department.key}"

    try:
        toolbox = ToolBox(session, department.tools)
        drafts = department.agent.handle(agent_context(route, toolbox))
    except LLMUnavailableError:
        raise
    except Exception as exc:  # ajan departman kodudur; hatası akışı durdurmaz
        return _fail_run(session, run, email, actor, f"ajan hatası: {exc}")

    problems, prepared = [], []
    seen: set[str] = set()
    for draft in drafts:
        ptype = department.proposal_type(draft.type)
        if ptype is None:
            problems.append(f"bilinmeyen öneri tipi: {draft.type}")
            continue
        try:
            payload = ptype.schema.model_validate(draft.payload).model_dump(mode="json")
        except ValidationError as exc:
            problems.append(f"{draft.type}: veri şemaya uymuyor ({exc.error_count()} hata)")
            continue
        normalized = ProposalDraft(draft.type, payload, draft.summary)
        key = idempotency_key(route.id, normalized)
        if key not in seen:
            seen.add(key)
            prepared.append((ptype, normalized, key))
    if problems:
        return _fail_run(session, run, email, actor, "; ".join(problems))

    existing = set(
        session.scalars(select(Proposal.idempotency_key).where(Proposal.idempotency_key.in_(seen)))
    )
    created: list[Proposal] = []
    for ptype, draft, key in prepared:
        if key in existing:
            continue
        proposal = Proposal(
            agent_run=run,
            email_id=email.id,
            department=department.key,
            type=draft.type,
            summary=draft.summary,
            payload=draft.payload,
            status=ProposalStatus.PENDING,
            requires_approval=ptype.requires_approval,
            idempotency_key=key,
        )
        session.add(proposal)
        created.append(proposal)
    run.status, run.finished_at = AgentRunStatus.SUCCEEDED, _now()
    session.flush()

    audit.record(
        session,
        actor=actor,
        action="agent.ran",
        entity_type="email",
        entity_id=email.id,
        data={"agent_run_id": str(run.id), "route_id": str(route.id), "proposals": len(created)},
    )
    for proposal in created:
        audit.record(
            session,
            actor=actor,
            action="proposal.created",
            entity_type="email",
            entity_id=email.id,
            data=_proposal_data(proposal),
        )
        if not proposal.requires_approval:
            _decide(session, proposal, ProposalStatus.APPROVED, SYSTEM_ACTOR, None)
            execute(session, proposal, registry=registry, actor=SYSTEM_ACTOR)
    refresh_email_status(session, email)
    return run


def _fail_run(session: Session, run: AgentRun, email: Email, actor: str, error: str) -> AgentRun:
    run.status, run.error, run.finished_at = AgentRunStatus.FAILED, error[:2000], _now()
    session.flush()
    audit.record(
        session,
        actor=actor,
        action="agent.failed",
        entity_type="email",
        entity_id=email.id,
        data={"agent_run_id": str(run.id), "route_id": str(run.route_id), "error": run.error},
    )
    return run


# ---------- Onay / ret ----------


def _lock(session: Session, proposal: Proposal) -> Proposal:
    return session.execute(
        select(Proposal)
        .where(Proposal.id == proposal.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one()


def _proposal_data(proposal: Proposal, **extra: Any) -> dict[str, Any]:
    return {
        "proposal_id": str(proposal.id),
        "department": proposal.department,
        "type": proposal.type,
        "summary": proposal.summary,
        **extra,
    }


def _decide(
    session: Session, proposal: Proposal, status: ProposalStatus, actor: str, reason: str | None
) -> None:
    proposal.status, proposal.decided_by, proposal.decided_at, proposal.reason = (
        status,
        actor,
        _now(),
        reason,
    )
    action = "proposal.approved" if status is ProposalStatus.APPROVED else "proposal.rejected"
    audit.record(
        session,
        actor=actor,
        action=action,
        entity_type="email",
        entity_id=proposal.email_id,
        data=_proposal_data(proposal, reason=reason),
    )


def _check_access(session: Session, proposal: Proposal, user: User) -> None:
    if not user.can_see(proposal.department):
        raise ProposalError("Bu departmanın önerileri için yetkiniz yok.")
    if not is_current(session, proposal):
        raise ProposalError("Bu öneri artık geçerli değil (yönlendirme düzeltilmiş).")


def is_current(session: Session, proposal: Proposal) -> bool:
    """Öneri, e-postanın geçerli kararındaki bir rotaya mı ait?"""
    return (
        session.scalar(
            select(Route.id)
            .join(AgentRun, AgentRun.route_id == Route.id)
            .join(Email, Email.id == AgentRun.email_id)
            .where(
                AgentRun.id == proposal.agent_run_id,
                Route.decision_id == Email.current_decision_id,
            )
        )
        is not None
    )


def approve(
    session: Session, proposal: Proposal, *, user: User, registry: DepartmentRegistry
) -> Proposal:
    _check_access(session, proposal, user)
    proposal = _lock(session, proposal)
    if proposal.status is not ProposalStatus.PENDING:
        raise ProposalError("Bu öneri artık onay beklemiyor.")
    _decide(session, proposal, ProposalStatus.APPROVED, _user_actor(user), None)
    return execute(session, proposal, registry=registry, actor=_user_actor(user))


def reject(session: Session, proposal: Proposal, *, user: User, reason: str) -> Proposal:
    _check_access(session, proposal, user)
    if not reason.strip():
        raise ProposalError("Reddetmek için gerekçe yazılmalı.")
    proposal = _lock(session, proposal)
    if proposal.status is not ProposalStatus.PENDING:
        raise ProposalError("Bu öneri artık onay beklemiyor.")
    _decide(session, proposal, ProposalStatus.REJECTED, _user_actor(user), reason.strip())
    refresh_email_status(session, _email(session, proposal))
    return proposal


def retry(
    session: Session, proposal: Proposal, *, user: User, registry: DepartmentRegistry
) -> Proposal:
    _check_access(session, proposal, user)
    if proposal.status is not ProposalStatus.FAILED:
        raise ProposalError("Yalnızca başarısız öneriler yeniden denenebilir.")
    return execute(session, proposal, registry=registry, actor=_user_actor(user))


# ---------- Tek yürütücü ----------


def execute(
    session: Session, proposal: Proposal, *, registry: DepartmentRegistry, actor: str
) -> Proposal:
    """Onaylanmış (ya da başarısız olmuş) öneriyi uygular; tam bir kez."""
    proposal = _lock(session, proposal)
    if proposal.status is ProposalStatus.EXECUTED:
        return proposal  # zaten uygulandı: ikinci kez uygulanmaz
    if proposal.status not in (ProposalStatus.APPROVED, ProposalStatus.FAILED):
        raise ProposalError("Yalnızca onaylanmış öneriler uygulanabilir.")

    proposal.attempts += 1
    department = registry.get(proposal.department)
    ptype = department.proposal_type(proposal.type) if department else None
    try:
        if ptype is None:
            raise ProposalError(f"öneri tipi kayıtlı değil: {proposal.department}/{proposal.type}")
        payload = ptype.schema.model_validate(proposal.payload)
        context = ApplyContext(
            session=session,
            proposal_id=str(proposal.id),
            idempotency_key=proposal.idempotency_key,
            department=proposal.department,
            email_id=str(proposal.email_id),
            actor=actor,
        )
        with session.begin_nested():
            result = ptype.apply(context, payload)
    except Exception as exc:
        proposal.status, proposal.error = ProposalStatus.FAILED, str(exc)[:2000]
        session.flush()
        audit.record(
            session,
            actor=actor,
            action="proposal.failed",
            entity_type="email",
            entity_id=proposal.email_id,
            data=_proposal_data(proposal, error=proposal.error, attempts=proposal.attempts),
        )
    else:
        proposal.status, proposal.executed_at = ProposalStatus.EXECUTED, _now()
        proposal.result, proposal.error = result, None
        session.flush()
        audit.record(
            session,
            actor=actor,
            action="proposal.executed",
            entity_type="email",
            entity_id=proposal.email_id,
            data=_proposal_data(proposal, result=result, attempts=proposal.attempts),
        )
    refresh_email_status(session, _email(session, proposal))
    return proposal


def _email(session: Session, proposal: Proposal) -> Email:
    return session.get_one(Email, proposal.email_id)


def refresh_email_status(session: Session, email: Email) -> None:
    """Geçerli rotalarda bekleyen öneri varsa `awaiting_approval`; kalmadıysa `routed`'a döner."""
    pending = session.scalar(
        select(Proposal.id)
        .join(AgentRun, AgentRun.id == Proposal.agent_run_id)
        .join(Route, Route.id == AgentRun.route_id)
        .where(
            Proposal.email_id == email.id,
            Proposal.status == ProposalStatus.PENDING,
            Route.decision_id == email.current_decision_id,
        )
        .limit(1)
    )
    if pending is not None and email.status in (EmailStatus.ROUTED, EmailStatus.PROCESSING):
        email.status = EmailStatus.AWAITING_APPROVAL
    elif pending is None and email.status is EmailStatus.AWAITING_APPROVAL:
        email.status = EmailStatus.ROUTED
