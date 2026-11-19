"""Decision Engine.

`classify` saf işlevdir (veritabanı yok): değerlendirme aracı da onu kullanır.
`decide` sonucu `Decision` + `Route` olarak kaydeder; e-postanın durumunu ve
denetim kaydını günceller.
"""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from flowpilot.core import audit
from flowpilot.core.decision.prompt import (
    PROMPT_VERSION,
    AttachmentForDecision,
    EmailForDecision,
    build_system_prompt,
    build_user_prompt,
)
from flowpilot.core.decision.schema import ModelDecision, ModelRoute
from flowpilot.core.models import Decision, Email, EmailStatus, Priority, Route
from flowpilot.core.registry import UNKNOWN, DepartmentRegistry
from flowpilot.llm import LLMClient, LLMError

DEFAULT_THRESHOLD = 0.75
MAX_ATTEMPTS = 2  # ilk deneme + bir yeniden deneme
TASK = "decision"


@dataclass(frozen=True)
class Classification:
    routes: list[ModelRoute]
    reasoning: str
    needs_review: bool
    review_reason: str | None
    attempts: int
    raw_output: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)

    def departments(self) -> set[str]:
        return {route.department for route in self.routes}


def validate(decision: ModelDecision, registry: DepartmentRegistry) -> list[str]:
    """Şemanın ötesindeki kurallar: departman ve intent kayıt defterinde var mı?"""
    problems = []
    for route in decision.routes:
        if route.department == UNKNOWN:
            continue
        department = registry.get(route.department)
        if department is None:
            problems.append(f"bilinmeyen departman: {route.department}")
        elif route.intent not in department.intent_keys():
            problems.append(f"{route.department} için geçersiz intent: {route.intent}")
    return problems


def _merge(routes: list[ModelRoute]) -> list[ModelRoute]:
    """Aynı departman iki kez gelirse güveni yüksek olanı tutar; 'unknown' başka rotayla kalmaz."""
    best: dict[str, ModelRoute] = {}
    for route in routes:
        current = best.get(route.department)
        if current is None or route.confidence > current.confidence:
            best[route.department] = route
    if len(best) > 1:
        best.pop(UNKNOWN, None)
    return sorted(best.values(), key=lambda r: r.confidence, reverse=True)


def classify(
    email: EmailForDecision,
    *,
    llm: LLMClient,
    registry: DepartmentRegistry,
    threshold: float = DEFAULT_THRESHOLD,
) -> Classification:
    system = build_system_prompt(registry)
    prompt = build_user_prompt(email)
    errors: list[str] = []

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            output = llm.generate(task=TASK, system=system, prompt=prompt, schema=ModelDecision)
        except LLMError as exc:
            errors.append(str(exc))
            continue
        if problems := validate(output, registry):
            errors.append("; ".join(problems))
            continue

        routes = _merge(output.routes)
        review_reasons = []
        if any(route.department == UNKNOWN for route in routes):
            review_reasons.append("hiçbir departmanla eşleşmedi")
        if low := [r.department for r in routes if r.confidence < threshold]:
            review_reasons.append(f"güven eşiğin ({threshold}) altında: {', '.join(low)}")
        return Classification(
            routes=routes,
            reasoning=output.reasoning,
            needs_review=bool(review_reasons),
            review_reason="; ".join(review_reasons) or None,
            attempts=attempt,
            raw_output=output.model_dump(mode="json"),
            errors=errors,
        )

    return Classification(
        routes=[],
        reasoning="",
        needs_review=True,
        review_reason=f"model geçerli bir karar üretemedi ({MAX_ATTEMPTS} deneme)",
        attempts=MAX_ATTEMPTS,
        errors=errors,
    )


def email_for_decision(email: Email) -> EmailForDecision:
    return EmailForDecision(
        from_addr=email.from_addr,
        subject=email.subject,
        body_text=email.body_text,
        to_addrs=list(email.to_addrs),
        cc_addrs=list(email.cc_addrs),
        attachments=[
            AttachmentForDecision(a.filename, a.extracted_text, a.parse_status.value)
            for a in email.attachments
        ],
    )


def decide(
    session: Session,
    email: Email,
    *,
    llm: LLMClient,
    model_name: str,
    registry: DepartmentRegistry,
    threshold: float = DEFAULT_THRESHOLD,
) -> Decision:
    email.status = EmailStatus.CLASSIFYING
    result = classify(email_for_decision(email), llm=llm, registry=registry, threshold=threshold)

    decision = Decision(
        email=email,
        model=model_name,
        prompt_version=PROMPT_VERSION,
        reasoning=result.reasoning,
        needs_review=result.needs_review,
        review_reason=result.review_reason,
        attempts=result.attempts,
        raw_output=result.raw_output,
    )
    for position, route in enumerate(result.routes):
        decision.routes.append(
            Route(
                position=position,
                department=route.department,
                intent=route.intent,
                priority=Priority(route.priority),
                confidence=route.confidence,
                suggested_action=route.suggested_action,
            )
        )
    session.add(decision)
    email.status = EmailStatus.NEEDS_REVIEW if result.needs_review else EmailStatus.ROUTED
    session.flush()

    audit.record(
        session,
        actor=f"decision_engine:{model_name}",
        action="email.classified",
        entity_type="email",
        entity_id=email.id,
        data={
            "decision_id": str(decision.id),
            "routes": [
                {"department": r.department, "intent": r.intent, "confidence": r.confidence}
                for r in result.routes
            ],
            "needs_review": result.needs_review,
            "review_reason": result.review_reason,
            "attempts": result.attempts,
            "errors": result.errors,
        },
    )
    return decision
