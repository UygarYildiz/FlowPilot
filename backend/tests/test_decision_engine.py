from typing import Any, TypeVar

import pytest
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot.bootstrap import get_registry
from flowpilot.core.decision.engine import MAX_ATTEMPTS, LLMClassifier, classify, decide
from flowpilot.core.decision.prompt import (
    ATTACHMENT_EXCERPT_CHARS,
    AttachmentForDecision,
    EmailForDecision,
    build_system_prompt,
    build_user_prompt,
)
from flowpilot.core.ingestion.service import ingest
from flowpilot.core.ingestion.types import IncomingEmail
from flowpilot.core.models import AuditEvent, EmailStatus, Priority
from flowpilot.core.storage import MemoryStorage
from flowpilot.llm import LLMError, LLMUnavailableError

T = TypeVar("T", bound=BaseModel)

EMAIL = EmailForDecision(
    from_addr="satis@ozkanrulman.example",
    subject="Fiyat teklifimiz",
    body_text="SAT-2026-031 için teklifimiz ektedir.",
    to_addrs=["satinalma@atlas-endustri.example"],
)


def route(department: str, intent: str | None, confidence: float = 0.9) -> dict[str, Any]:
    return {
        "department": department,
        "intent": intent,
        "priority": "normal",
        "confidence": confidence,
        "suggested_action": "incele",
    }


class ScriptedLLM:
    """Sırayla verilen cevapları döndürür; bir istisna nesnesi verilirse onu fırlatır."""

    def __init__(self, *outputs: dict[str, Any] | Exception) -> None:
        self.outputs = list(outputs)
        self.calls = 0

    def generate(self, *, task: str, system: str, prompt: str, schema: type[T]) -> T:
        self.calls += 1
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return schema.model_validate(output)


def _decision(*routes: dict[str, Any]) -> dict[str, Any]:
    return {"routes": list(routes), "reasoning": "gerekçe"}


def test_confident_single_route_is_routed() -> None:
    llm = ScriptedLLM(_decision(route("procurement", "new_quote", 0.95)))
    result = classify(EMAIL, llm=llm, registry=get_registry())
    assert not result.needs_review
    assert result.departments() == {"procurement"}
    assert result.attempts == 1


def test_low_confidence_goes_to_review() -> None:
    llm = ScriptedLLM(_decision(route("procurement", "new_quote", 0.6)))
    result = classify(EMAIL, llm=llm, registry=get_registry())
    assert result.needs_review
    assert result.review_reason is not None and "eşiğin" in result.review_reason


def test_unknown_goes_to_review_and_is_dropped_next_to_real_route() -> None:
    alone = classify(
        EMAIL, llm=ScriptedLLM(_decision(route("unknown", None, 0.9))), registry=get_registry()
    )
    assert alone.needs_review and alone.departments() == {"unknown"}

    mixed = classify(
        EMAIL,
        llm=ScriptedLLM(
            _decision(route("unknown", None, 0.5), route("finance", "invoice_received"))
        ),
        registry=get_registry(),
    )
    assert mixed.departments() == {"finance"} and not mixed.needs_review


def test_invalid_output_is_retried_once() -> None:
    llm = ScriptedLLM(
        _decision(route("hr", "hire")),
        _decision(route("procurement", "new_quote")),
    )
    result = classify(EMAIL, llm=llm, registry=get_registry())
    assert result.attempts == 2 and not result.needs_review
    assert result.errors == ["bilinmeyen departman: hr"]


def test_two_failures_send_to_review_without_guessing() -> None:
    llm = ScriptedLLM(LLMError("zaman aşımı"), _decision(route("finance", "new_quote")))
    result = classify(EMAIL, llm=llm, registry=get_registry())
    assert llm.calls == MAX_ATTEMPTS
    assert result.needs_review and result.routes == []
    assert result.errors == ["zaman aşımı", "finance için geçersiz intent: new_quote"]


def test_multi_department_and_duplicate_routes_are_merged() -> None:
    llm = ScriptedLLM(
        _decision(
            route("logistics", "delivery_issue", 0.8),
            route("finance", "invoice_dispute", 0.9),
            route("logistics", "delivery_delay", 0.85),
        )
    )
    result = classify(EMAIL, llm=llm, registry=get_registry())
    assert [(r.department, r.intent) for r in result.routes] == [
        ("finance", "invoice_dispute"),
        ("logistics", "delivery_delay"),
    ]


def test_system_prompt_lists_every_department_and_intent() -> None:
    system = build_system_prompt(get_registry())
    for department in get_registry():
        assert f"## {department.key}" in system
        for intent in department.intents:
            assert f"- {intent.key}:" in system


def test_user_prompt_shortens_long_attachment_text() -> None:
    long_text = "x" * (ATTACHMENT_EXCERPT_CHARS + 100)
    email = EmailForDecision(
        "a@b.example",
        "Konu",
        "Gövde",
        attachments=[AttachmentForDecision("teklif.pdf", long_text, "ok")],
    )
    prompt = build_user_prompt(email)
    assert "Ek: teklif.pdf (ok)" in prompt
    assert "x" * ATTACHMENT_EXCERPT_CHARS + " …(kısaltıldı)" in prompt
    assert "x" * (ATTACHMENT_EXCERPT_CHARS + 1) not in prompt


def test_decide_persists_routes_status_and_audit(session: Session) -> None:
    incoming = IncomingEmail(
        message_id="<d1@x.example>",
        from_addr="satinalma@bilgemakina.example",
        subject="Eksik teslimat ve hatalı fatura",
        body_text="2 kaplin eksik geldi, faturada da var.",
    )
    email = ingest(session, MemoryStorage(), incoming, source="test").email
    llm = ScriptedLLM(
        _decision(route("logistics", "delivery_issue", 0.9), route("finance", "invoice_dispute"))
    )

    decision = decide(session, email, classifier=LLMClassifier(llm, get_registry(), "test-model"))

    assert email.status is EmailStatus.ROUTED
    assert decision.model == "test-model" and decision.prompt_version == "decision-v1"
    assert [r.department for r in decision.routes] == ["logistics", "finance"]
    assert decision.routes[0].priority is Priority.NORMAL
    event = session.scalars(select(AuditEvent).where(AuditEvent.action == "email.classified")).one()
    assert event.actor == "decision_engine:test-model"
    assert event.data["needs_review"] is False


def test_decide_with_cascade_records_deciding_engine_and_both_views(session: Session) -> None:
    from flowpilot.core.decision.cascade import CascadeClassifier

    incoming = IncomingEmail(
        message_id="<d3@x.example>", from_addr="a@b.example", subject="Fiyat", body_text="?"
    )
    email = ingest(session, MemoryStorage(), incoming, source="test").email
    unsure = ScriptedLLM(_decision(route("procurement", "new_quote", 0.6)))
    sure = ScriptedLLM(_decision(route("sales_orders", "customer_request", 0.95)))
    cascade = CascadeClassifier(
        first=LLMClassifier(unsure, get_registry(), "subq:snap"),
        second=LLMClassifier(sure, get_registry(), "gemini:flash"),
    )

    decision = decide(session, email, classifier=cascade)

    assert email.status is EmailStatus.ROUTED
    assert decision.model == "gemini:flash"
    assert decision.prompt_version == "decision-v1>decision-v1"
    assert [r.department for r in decision.routes] == ["sales_orders"]
    assert decision.reasoning == "SubQ: gerekçe\nGemini: gerekçe"
    assert decision.raw_output is not None
    assert [s["model"] for s in decision.raw_output["stages"]] == ["subq:snap", "gemini:flash"]
    event = session.scalars(select(AuditEvent).where(AuditEvent.action == "email.classified")).one()
    assert event.actor == "decision_engine:gemini:flash"


def test_decide_marks_needs_review(session: Session) -> None:
    incoming = IncomingEmail(
        message_id="<d2@x.example>", from_addr="a@b.example", subject="?", body_text="?"
    )
    email = ingest(session, MemoryStorage(), incoming, source="test").email
    llm = ScriptedLLM(LLMError("hata"), LLMError("hata"))
    decision = decide(session, email, classifier=LLMClassifier(llm, get_registry(), "m"))
    assert email.status is EmailStatus.NEEDS_REVIEW
    assert decision.needs_review and decision.routes == []


def test_unavailable_model_propagates_instead_of_review() -> None:
    """Kesinti e-postaları manuel incelemeye boğmamalı: hata yukarı çıkar, iş bekler."""
    llm = ScriptedLLM(LLMUnavailableError("kota"))
    with pytest.raises(LLMUnavailableError):
        classify(EMAIL, llm=llm, registry=get_registry())


def test_classify_pending_stops_when_model_unavailable(session: Session) -> None:
    from collections.abc import Iterator
    from contextlib import contextmanager

    from flowpilot.core.decision.runner import classify_pending
    from flowpilot.core.models import Email

    storage = MemoryStorage()
    for n in range(3):
        incoming = IncomingEmail(
            message_id=f"<p{n}@x.example>", from_addr="a@b.example", subject=f"s{n}", body_text="b"
        )
        ingest(session, storage, incoming, source="test")

    @contextmanager
    def scope() -> Iterator[Session]:
        with session.begin_nested():
            yield session

    llm = ScriptedLLM(
        _decision(route("finance", "invoice_received")), LLMUnavailableError("kota bitti")
    )
    report = classify_pending(scope, classifier=LLMClassifier(llm, get_registry(), "m"))

    assert report.routed == 1 and len(report.failed) == 1 and llm.calls == 2
    statuses = sorted(s.value for s in session.scalars(select(Email.status)))
    assert statuses == ["received", "received", "routed"]
