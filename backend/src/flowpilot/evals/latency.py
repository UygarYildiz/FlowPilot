"""Kriter 10: e-postanın gelişinden yönlendirmeye ve öneriye geçen süre (veritabanından).

Geliş zamanı e-postanın `Date` başlığıdır (`Email.received_at`); gönderenin saatine bağlıdır,
saniye düzeyinde kaba bir ölçüdür.
"""

import math
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowpilot.core.models import Decision, Email, Proposal


@dataclass(frozen=True)
class LatencyRow:
    subject: str
    received_at: datetime
    to_decision: float | None
    to_proposal: float | None


def percentile(values: list[float], p: float) -> float:
    """En yakın sıra yöntemiyle yüzdelik (p95 için küçük örneklerde tutucu)."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p / 100 * len(ordered)) - 1)]


def collect(session: Session, *, source: str = "imap") -> list[LatencyRow]:
    first_decision = (
        select(Decision.email_id, func.min(Decision.created_at).label("at"))
        .group_by(Decision.email_id)
        .subquery()
    )
    first_proposal = (
        select(Proposal.email_id, func.min(Proposal.created_at).label("at"))
        .group_by(Proposal.email_id)
        .subquery()
    )
    query = (
        select(Email.subject, Email.received_at, first_decision.c.at, first_proposal.c.at)
        .outerjoin(first_decision, first_decision.c.email_id == Email.id)
        .outerjoin(first_proposal, first_proposal.c.email_id == Email.id)
        .where(Email.source == source)
        .order_by(Email.received_at)
    )

    def seconds(at: datetime | None, start: datetime) -> float | None:
        return (at - start).total_seconds() if at is not None else None

    return [
        LatencyRow(subject, received, seconds(decided, received), seconds(proposed, received))
        for subject, received, decided, proposed in session.execute(query)
    ]


def render(rows: list[LatencyRow]) -> str:
    lines = [f"{len(rows)} e-posta"]
    for label, values in (
        ("Gelişten yönlendirmeye", [r.to_decision for r in rows if r.to_decision is not None]),
        ("Gelişten öneriye", [r.to_proposal for r in rows if r.to_proposal is not None]),
    ):
        if values:
            lines.append(
                f"{label}: n={len(values)}  ortanca {percentile(values, 50):.1f} sn  "
                f"p95 {percentile(values, 95):.1f} sn  en uzun {max(values):.1f} sn"
            )
        else:
            lines.append(f"{label}: veri yok")
    return "\n".join(lines)
