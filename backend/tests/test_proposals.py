"""Öneri yaşam döngüsü ve tek yürütücü (ADR-014).

Başarı kriteri 7: onaylanan öneri tam bir kez uygulanır, reddedilen hiç uygulanmaz.
Başarı kriteri 9 (sözleşme sınavı): ajanlı bir test departmanı çekirdeğe dokunmadan eklenir,
çalışır ve kaldırılır.
"""

import threading
import uuid
from dataclasses import dataclass, field

import pytest
from pydantic import BaseModel
from sqlalchemy import Engine, delete, func, select
from sqlalchemy.orm import Session

from flowpilot.bootstrap import DEPARTMENTS
from flowpilot.core import audit
from flowpilot.core.agent_runner import run_pending_agents
from flowpilot.core.ingestion.service import ingest
from flowpilot.core.ingestion.types import IncomingEmail
from flowpilot.core.models import (
    AgentRun,
    AgentRunStatus,
    AuditEvent,
    Decision,
    Email,
    EmailStatus,
    Priority,
    Proposal,
    ProposalStatus,
    Route,
    User,
    UserRole,
)
from flowpilot.core.proposals import (
    ProposalError,
    approve,
    execute,
    reject,
    retry,
    run_agent,
)
from flowpilot.core.registry import (
    AgentContext,
    ApplyContext,
    Department,
    DepartmentRegistry,
    Intent,
    ProposalDraft,
    ProposalType,
    RegistryError,
)
from flowpilot.core.storage import MemoryStorage
from flowpilot.core.workflow import RouteInput, correct_routes

# ---------- Test departmanı (yalnızca bu dosyada; çekirdekte iz yok) ----------


class Note(BaseModel):
    text: str
    amount: int


@dataclass
class Applier:
    """`apply`: kendi kaydını yazar (burada bir denetim olayı) ve sayar."""

    fail_times: int = 0
    calls: int = 0

    def __call__(self, ctx: ApplyContext, payload: Note) -> dict:
        self.calls += 1
        audit.record(
            ctx.session,
            actor=ctx.actor,
            action="test.applied",
            entity_type="test",
            entity_id=ctx.idempotency_key,
            data={"text": payload.text},
        )
        if self.fail_times:
            self.fail_times -= 1
            raise RuntimeError("dış sistem kapalı")
        return {"saved": payload.text}


@dataclass
class ScriptedAgent:
    drafts: list[ProposalDraft]
    contexts: list[AgentContext] = field(default_factory=list)

    def handle(self, context: AgentContext) -> list[ProposalDraft]:
        self.contexts.append(context)
        return self.drafts


def note(text: str = "teklifi kaydet", amount: int = 42) -> ProposalDraft:
    return ProposalDraft("note", {"text": text, "amount": amount}, f"Not: {text}")


def make_department(
    agent: ScriptedAgent, applier: Applier, *, requires_approval: bool = True
) -> Department:
    return Department(
        key="test_dept",
        name="Test",
        description="Sözleşme sınavı için test departmanı.",
        intents=(Intent("note_it", "Not alınacak e-posta."),),
        agent=agent,
        proposal_types=(
            ProposalType("note", "Not", Note, applier, requires_approval=requires_approval),
        ),
    )


def make_registry(department: Department) -> DepartmentRegistry:
    registry = DepartmentRegistry(DEPARTMENTS)
    registry.register(department)
    return registry


def routed_email(session: Session, department: str = "test_dept") -> Route:
    incoming = IncomingEmail(
        message_id=f"<{uuid.uuid4()}@x.example>",
        from_addr="satis@tedarikci.example",
        subject="Teklif",
        body_text=f"Teklifimiz ektedir. ({uuid.uuid4().hex[:8]})",
    )
    email = ingest(session, MemoryStorage(), incoming, source="test").email
    decision = Decision(email=email, model="m", prompt_version="v", needs_review=False, attempts=1)
    route = Route(
        position=0,
        department=department,
        intent="note_it",
        priority=Priority.NORMAL,
        confidence=0.9,
    )
    decision.routes.append(route)
    session.add(decision)
    email.current_decision = decision
    email.status = EmailStatus.ROUTED
    session.flush()
    return route


def make_user(
    session: Session, role: UserRole = UserRole.ADMIN, departments: list[str] | None = None
) -> User:
    user = User(
        email=f"{uuid.uuid4().hex[:8]}@atlas.example",
        name="Deneme",
        role=role,
        departments=departments or [],
        password_hash="-",
    )
    session.add(user)
    session.flush()
    return user


def applied_count(session: Session) -> int:
    return (
        session.scalar(
            select(func.count()).select_from(AuditEvent).where(AuditEvent.action == "test.applied")
        )
        or 0
    )


def ran(session: Session, route: Route, registry: DepartmentRegistry) -> AgentRun:
    run = run_agent(session, route, registry=registry)
    assert run is not None
    return run


def actions(session: Session, email: Email) -> list[str]:
    return list(
        session.scalars(
            select(AuditEvent.action)
            .where(AuditEvent.entity_type == "email", AuditEvent.entity_id == str(email.id))
            .order_by(AuditEvent.id)
        )
    )


# ---------- Sözleşme ----------


def test_agent_needs_proposal_types_and_type_keys_are_unique() -> None:
    agent, applier = ScriptedAgent([]), Applier()
    with pytest.raises(RegistryError, match="öneri tipi"):
        DepartmentRegistry([Department("x", "X", "x", (Intent("i", "i"),), agent=agent)])
    ptype = ProposalType("note", "Not", Note, applier)
    with pytest.raises(RegistryError, match="Tekrarlanan öneri tipi"):
        DepartmentRegistry([Department("x", "X", "x", (Intent("i", "i"),), agent, (ptype, ptype))])


def test_test_department_is_added_and_removed_without_touching_core(session: Session) -> None:
    applier = Applier()
    registry = make_registry(make_department(ScriptedAgent([note()]), applier))
    assert registry.get("test_dept") is not None and len(registry) == len(DEPARTMENTS) + 1

    run = run_agent(session, routed_email(session), registry=registry)
    assert run is not None and run.status is AgentRunStatus.SUCCEEDED

    registry.unregister("test_dept")
    assert registry.keys() == [d.key for d in DEPARTMENTS]
    # Kaldırılmış departmanın onaylı önerisi uygulanamaz ama sistem çökmez: başarısız olur.
    proposal = run.proposals[0]
    approved = approve(session, proposal, user=make_user(session), registry=registry)
    assert approved.status is ProposalStatus.FAILED and "kayıtlı değil" in (approved.error or "")
    assert applier.calls == 0


# ---------- Ajan çalıştırma ----------


def test_agent_run_stores_pending_proposals_and_awaits_approval(session: Session) -> None:
    agent = ScriptedAgent([note("a"), note("b"), note("a")])  # tekrar eden öneri bir kez
    registry = make_registry(make_department(agent, Applier()))
    route = routed_email(session)

    run = run_agent(session, route, registry=registry)

    assert run is not None and [p.summary for p in run.proposals] == ["Not: a", "Not: b"]
    assert all(p.status is ProposalStatus.PENDING for p in run.proposals)
    email = route.decision.email
    assert email.status is EmailStatus.AWAITING_APPROVAL
    assert agent.contexts[0].subject == "Teklif" and agent.contexts[0].department == "test_dept"
    assert actions(session, email)[-3:] == ["agent.ran", "proposal.created", "proposal.created"]

    # İkinci çalıştırma yeni öneri üretmez.
    assert run_agent(session, route, registry=registry) is run
    assert len(agent.contexts) == 1


def test_department_without_agent_is_skipped(session: Session) -> None:
    registry = DepartmentRegistry(DEPARTMENTS)
    route = routed_email(session, department="finance")
    assert run_agent(session, route, registry=registry) is None


def test_invalid_agent_output_fails_the_run_without_proposals(session: Session) -> None:
    agent = ScriptedAgent([note(), ProposalDraft("note", {"text": "x"}, "eksik alan")])
    registry = make_registry(make_department(agent, Applier()))
    route = routed_email(session)

    run = run_agent(session, route, registry=registry)
    assert run is not None and run.status is AgentRunStatus.FAILED and run.proposals == []
    assert "şemaya uymuyor" in (run.error or "")
    assert route.decision.email.status is EmailStatus.ROUTED

    agent.drafts = [ProposalDraft("bilinmeyen", {}, "?")]
    run = ran(session, route, registry)
    assert run.status is AgentRunStatus.FAILED and "bilinmeyen öneri tipi" in (run.error or "")

    agent.drafts = [note()]  # düzelince aynı çalışma yeniden denenir
    run = ran(session, route, registry)
    assert run.status is AgentRunStatus.SUCCEEDED and run.attempts == 3 and len(run.proposals) == 1


def test_agent_crash_is_recorded_as_failed_run(session: Session) -> None:
    class Crashing:
        def handle(self, context: AgentContext) -> list[ProposalDraft]:
            raise ValueError("PDF okunamadı")

    department = make_department(ScriptedAgent([]), Applier())
    department = Department(**{**department.__dict__, "agent": Crashing()})
    route = routed_email(session)
    run = run_agent(session, route, registry=make_registry(department))
    assert run is not None and run.status is AgentRunStatus.FAILED
    assert "PDF okunamadı" in (run.error or "")
    assert "agent.failed" in actions(session, route.decision.email)


# ---------- Kriter 7: tam bir kez / hiç ----------


def test_approved_proposal_is_applied_exactly_once(session: Session) -> None:
    applier = Applier()
    registry = make_registry(make_department(ScriptedAgent([note()]), applier))
    route = routed_email(session)
    proposal = ran(session, route, registry).proposals[0]
    user = make_user(session)

    done = approve(session, proposal, user=user, registry=registry)
    assert done.status is ProposalStatus.EXECUTED and done.result == {"saved": "teklifi kaydet"}
    assert done.decided_by == f"user:{user.email}" and done.attempts == 1

    # Aynı öneri tekrar yürütülse de, tekrar onaylanmaya çalışılsa da ikinci kez uygulanmaz.
    execute(session, proposal, registry=registry, actor="system")
    with pytest.raises(ProposalError, match="onay beklemiyor"):
        approve(session, proposal, user=user, registry=registry)
    assert applier.calls == 1 and applied_count(session) == 1
    assert route.decision.email.status is EmailStatus.ROUTED
    email_actions = actions(session, route.decision.email)
    assert email_actions[-2:] == ["proposal.approved", "proposal.executed"]


def test_rejected_or_pending_proposal_is_never_applied(session: Session) -> None:
    applier = Applier()
    registry = make_registry(make_department(ScriptedAgent([note("a"), note("b")]), applier))
    route = routed_email(session)
    first, second = ran(session, route, registry).proposals
    user = make_user(session)

    with pytest.raises(ProposalError, match="onaylanmış"):
        execute(session, first, registry=registry, actor="system")  # bekleyen uygulanmaz
    with pytest.raises(ProposalError, match="gerekçe"):
        reject(session, first, user=user, reason="  ")
    rejected = reject(session, first, user=user, reason="Fiyat yanlış okunmuş")
    assert rejected.status is ProposalStatus.REJECTED and rejected.reason == "Fiyat yanlış okunmuş"
    with pytest.raises(ProposalError):
        execute(session, first, registry=registry, actor="system")
    with pytest.raises(ProposalError):
        approve(session, first, user=user, registry=registry)
    assert route.decision.email.status is EmailStatus.AWAITING_APPROVAL  # ikincisi bekliyor

    reject(session, second, user=user, reason="Gerek yok")
    assert applier.calls == 0 and applied_count(session) == 0
    assert route.decision.email.status is EmailStatus.ROUTED


def test_failed_apply_is_rolled_back_and_retried_once_successfully(session: Session) -> None:
    applier = Applier(fail_times=1)
    registry = make_registry(make_department(ScriptedAgent([note()]), applier))
    proposal = ran(session, routed_email(session), registry).proposals[0]
    user = make_user(session)

    failed = approve(session, proposal, user=user, registry=registry)
    assert failed.status is ProposalStatus.FAILED and "dış sistem kapalı" in (failed.error or "")
    assert applied_count(session) == 0  # yarım kalan yazım geri alındı

    done = retry(session, proposal, user=user, registry=registry)
    assert done.status is ProposalStatus.EXECUTED and done.attempts == 2 and done.error is None
    assert applied_count(session) == 1
    with pytest.raises(ProposalError, match="başarısız"):
        retry(session, proposal, user=user, registry=registry)


def test_proposal_without_approval_requirement_is_applied_by_system(session: Session) -> None:
    applier = Applier()
    department = make_department(ScriptedAgent([note()]), applier, requires_approval=False)
    route = routed_email(session)
    proposal = ran(session, route, make_registry(department)).proposals[0]
    assert proposal.status is ProposalStatus.EXECUTED and proposal.decided_by == "system"
    assert applier.calls == 1 and route.decision.email.status is EmailStatus.ROUTED


def test_only_users_of_the_department_can_decide(session: Session) -> None:
    registry = make_registry(make_department(ScriptedAgent([note()]), Applier()))
    proposal = ran(session, routed_email(session), registry).proposals[0]
    outsider = make_user(session, UserRole.DEPARTMENT_USER, ["finance"])
    with pytest.raises(ProposalError, match="yetkiniz yok"):
        approve(session, proposal, user=outsider, registry=registry)
    insider = make_user(session, UserRole.DEPARTMENT_USER, ["test_dept"])
    assert approve(session, proposal, user=insider, registry=registry).status is (
        ProposalStatus.EXECUTED
    )


def test_rerouting_makes_old_proposals_stale(session: Session) -> None:
    applier = Applier()
    registry = make_registry(make_department(ScriptedAgent([note()]), applier))
    route = routed_email(session)
    proposal = ran(session, route, registry).proposals[0]
    email = route.decision.email
    user = make_user(session)

    correct_routes(
        session,
        email,
        [RouteInput("finance", "invoice_received")],
        reason="Fatura",
        user=user,
        registry=registry,
    )
    assert email.status is EmailStatus.ROUTED
    with pytest.raises(ProposalError, match="geçerli değil"):
        approve(session, proposal, user=user, registry=registry)
    assert applier.calls == 0


def test_runner_processes_open_routes_of_agent_departments(session: Session) -> None:
    from contextlib import contextmanager

    registry = make_registry(make_department(ScriptedAgent([note()]), Applier()))
    routed_email(session)
    routed_email(session, department="finance")  # ajansız: atlanır

    @contextmanager
    def scope():  # noqa: ANN202
        with session.begin_nested():
            yield session

    report = run_pending_agents(scope, registry=registry)
    assert (report.succeeded, report.proposals, report.failed) == (1, 1, [])
    assert run_pending_agents(scope, registry=registry).succeeded == 0  # ikinci kez çalışmaz


# ---------- Eşzamanlı onay: iki işlem aynı anda yürütse de tek uygulama ----------


def test_concurrent_execution_applies_once(engine: Engine) -> None:
    applier = Applier()
    registry = make_registry(make_department(ScriptedAgent([note()]), applier))
    with Session(engine) as s, s.begin():
        route = routed_email(s)
        proposal = ran(s, route, registry).proposals[0]
        proposal.status = ProposalStatus.APPROVED
        email_id, proposal_id = route.decision.email_id, proposal.id

    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def worker() -> None:
        try:
            with Session(engine) as s, s.begin():
                barrier.wait()
                execute(s, s.get_one(Proposal, proposal_id), registry=registry, actor="system")
        except Exception as exc:  # pragma: no cover - hata testi bozar
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    try:
        assert errors == []
        with Session(engine) as s:
            stored = s.get_one(Proposal, proposal_id)
            assert stored.status is ProposalStatus.EXECUTED and stored.attempts == 1
            assert applier.calls == 1
            assert applied_count(s) == 1
    finally:
        with Session(engine) as s, s.begin():
            s.delete(s.get_one(Email, email_id))
            s.execute(delete(AuditEvent).where(AuditEvent.action == "test.applied"))
            s.execute(delete(AuditEvent).where(AuditEvent.entity_id == str(email_id)))
