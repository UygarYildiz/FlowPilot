"""Kademeli sınıflandırma (ADR-013): ağ yok, sahte alt motorlar."""

from dataclasses import dataclass, field

import pytest

from flowpilot.core.decision.cascade import CascadeClassifier
from flowpilot.core.decision.engine import Classification
from flowpilot.core.decision.prompt import EmailForDecision
from flowpilot.core.decision.schema import ModelRoute
from flowpilot.llm import LLMUnavailableError

EMAIL = EmailForDecision(from_addr="a@b.example", subject="Konu", body_text="Metin")


def route(department: str, confidence: float) -> ModelRoute:
    return ModelRoute(
        department=department,
        intent=None if department == "unknown" else "new_quote",
        priority="normal",
        confidence=confidence,
        suggested_action="",
    )


def result(*routes: ModelRoute, review: bool, why: str = "gerekçe") -> Classification:
    return Classification(
        routes=list(routes),
        reasoning=why,
        needs_review=review,
        review_reason="güven eşiğin (0.75) altında" if review else None,
        attempts=1,
    )


@dataclass
class Stub:
    model_name: str
    answer: Classification | Exception
    prompt_version: str = "v"
    calls: list[EmailForDecision] = field(default_factory=list)

    def __call__(self, email: EmailForDecision) -> Classification:
        self.calls.append(email)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def cascade(first: Classification | Exception, second: Classification | Exception):  # noqa: ANN201
    a, b = Stub("subq:snap", first), Stub("gemini:flash", second)
    return CascadeClassifier(first=a, second=b), a, b


def test_confident_first_decides_and_second_is_not_called() -> None:
    clf, _, gemini = cascade(result(route("procurement", 0.97), review=False), RuntimeError())
    out = clf(EMAIL)
    assert out.decided_by == "subq:snap" and not out.needs_review
    assert gemini.calls == []
    assert out.raw_output is not None and len(out.raw_output["stages"]) == 1


def test_unsure_first_goes_to_second_and_confident_second_decides() -> None:
    first = result(route("sales_orders", 0.62), route("procurement", 0.54), review=True, why="S")
    second = result(route("sales_orders", 0.95), review=False, why="Müşteri talebi")
    out, _, _ = cascade(first, second)
    final = out(EMAIL)
    assert final.decided_by == "gemini:flash" and not final.needs_review
    assert [r.department for r in final.routes] == ["sales_orders"]
    assert final.reasoning == "SubQ: S\nGemini: Müşteri talebi"
    assert final.attempts == 2 and len(final.raw_output["stages"]) == 2


def test_both_unsure_goes_to_human_with_both_reasons() -> None:
    first = result(route("logistics", 0.6), review=True)
    second = result(route("sales_orders", 0.7), review=True)
    final = cascade(first, second)[0](EMAIL)
    assert final.needs_review and final.decided_by == "gemini:flash"
    assert final.review_reason is not None
    assert final.review_reason.startswith("SubQ: ") and "; Gemini: " in final.review_reason


def test_clearly_unrelated_email_skips_second() -> None:
    first = result(route("unknown", 0.99), review=True)
    clf, _, gemini = cascade(first, RuntimeError())
    final = clf(EMAIL)
    assert final.needs_review and gemini.calls == []
    # güven düşükse ikinci motor yine bakar
    clf, _, gemini = cascade(result(route("unknown", 0.6), review=True), first)
    clf(EMAIL)
    assert len(gemini.calls) == 1


def test_unavailable_engines_fall_back_to_the_other() -> None:
    gemini_ok = result(route("finance", 0.95), review=False)
    final = cascade(LLMUnavailableError("subq kapalı"), gemini_ok)[0](EMAIL)
    assert final.decided_by == "gemini:flash" and "subq kapalı" in final.errors[0]

    unsure = result(route("finance", 0.6), review=True)
    final = cascade(unsure, LLMUnavailableError("gemini kapalı"))[0](EMAIL)
    assert final.decided_by == "subq:snap" and final.needs_review
    assert [r.department for r in final.routes] == ["finance"]

    with pytest.raises(LLMUnavailableError):
        cascade(LLMUnavailableError("a"), LLMUnavailableError("b"))[0](EMAIL)


def test_second_without_routes_keeps_first_suggestion() -> None:
    broken = Classification(
        routes=[], reasoning="", needs_review=True, review_reason="geçersiz", attempts=2
    )
    final = cascade(result(route("finance", 0.6), review=True), broken)[0](EMAIL)
    assert final.needs_review and final.decided_by == "subq:snap"
    assert [r.department for r in final.routes] == ["finance"]


def test_name_and_prompt_version_describe_both_engines() -> None:
    clf = cascade(result(review=False), result(review=False))[0]
    assert clf.model_name == "cascade:subq:snap>gemini:flash"
    assert clf.prompt_version == "v>v"
