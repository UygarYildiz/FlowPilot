"""Yönlendirilmiş e-postaların açık rotalarında departman ajanlarını çalıştırır (ADR-014)."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from flowpilot.core.models import (
    AgentRun,
    AgentRunStatus,
    Email,
    EmailStatus,
    Route,
    RouteStatus,
)
from flowpilot.core.proposals import run_agent
from flowpilot.core.registry import DepartmentRegistry
from flowpilot.llm import LLMUnavailableError


@dataclass
class AgentReport:
    succeeded: int = 0
    proposals: int = 0
    failed: list[str] = field(default_factory=list)


def run_pending_agents(
    session_scope: Callable[[], AbstractContextManager[Session]],
    *,
    registry: DepartmentRegistry,
    limit: int | None = None,
) -> AgentReport:
    """Ajanı olan departmanların henüz çalışmamış (ya da başarısız) açık rotalarını işler.

    Her rota ayrı işlemde. Model erişilemezse kalanlar sonraki çalıştırmaya kalır.
    """
    departments = [d.key for d in registry if d.agent is not None]
    report = AgentReport()
    if not departments:
        return report
    with session_scope() as session:
        query = (
            select(Route.id)
            .join(Email, Email.current_decision_id == Route.decision_id)
            .outerjoin(AgentRun, AgentRun.route_id == Route.id)
            .where(
                Route.department.in_(departments),
                Route.status == RouteStatus.OPEN,
                Email.status.in_([EmailStatus.ROUTED, EmailStatus.AWAITING_APPROVAL]),
                or_(AgentRun.id.is_(None), AgentRun.status == AgentRunStatus.FAILED),
            )
            .order_by(Email.received_at)
            .limit(limit)
        )
        route_ids = list(session.scalars(query))

    for route_id in route_ids:
        try:
            with session_scope() as session:
                run = run_agent(session, session.get_one(Route, route_id), registry=registry)
                outcome = (run.status, len(run.proposals), run.error) if run else None
        except LLMUnavailableError as exc:
            report.failed.append(f"{route_id}: {exc} — kalan rotalar sonraki çalıştırmaya kaldı")
            break
        except Exception as exc:
            report.failed.append(f"{route_id}: {exc}")
            continue
        if outcome is None:
            continue
        status, count, error = outcome
        if status is AgentRunStatus.SUCCEEDED:
            report.succeeded += 1
            report.proposals += count
        else:
            report.failed.append(f"{route_id}: {error}")
    return report
