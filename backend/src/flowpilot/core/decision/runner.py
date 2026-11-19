from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot.core.decision.engine import decide
from flowpilot.core.models import Email, EmailStatus
from flowpilot.core.registry import DepartmentRegistry
from flowpilot.llm import LLMClient, LLMUnavailableError


@dataclass
class ClassifyReport:
    routed: int = 0
    needs_review: int = 0
    failed: list[str] = field(default_factory=list)


def classify_pending(
    session_scope: Callable[[], AbstractContextManager[Session]],
    *,
    llm: LLMClient,
    model_name: str,
    registry: DepartmentRegistry,
    threshold: float,
    limit: int | None = None,
) -> ClassifyReport:
    """`received` durumundaki e-postaları geliş sırasıyla sınıflandırır; her biri ayrı işlemde.

    Hata olursa o e-postanın işlemi geri alınır ve e-posta `received` kalır (sonra yeniden denenir).
    """
    with session_scope() as session:
        query = select(Email.id).where(Email.status == EmailStatus.RECEIVED)
        ids = list(session.scalars(query.order_by(Email.received_at).limit(limit)))

    report = ClassifyReport()
    for email_id in ids:
        try:
            with session_scope() as session:
                email = session.get_one(Email, email_id)
                decision = decide(
                    session,
                    email,
                    llm=llm,
                    model_name=model_name,
                    registry=registry,
                    threshold=threshold,
                )
        except LLMUnavailableError as exc:
            # Model erişilemez: kalanları denemenin anlamı yok; hepsi `received` kalır.
            report.failed.append(f"{email_id}: {exc} — kalan e-postalar sonraki çalıştırmaya kaldı")
            break
        except Exception as exc:
            report.failed.append(f"{email_id}: {exc}")
            continue
        if decision.needs_review:
            report.needs_review += 1
        else:
            report.routed += 1
    return report
