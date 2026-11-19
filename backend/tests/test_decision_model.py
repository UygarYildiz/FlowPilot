"""Karar modeli (Clef) istemcisi ve sınıflandırıcısı; ağ yok."""

from typing import Any

import pytest

from flowpilot.bootstrap import get_registry
from flowpilot.core.decision.prompt import EmailForDecision
from flowpilot.core.decision.typed import DecisionModelClassifier, build_questions
from flowpilot.llm import LLMError, LLMUnavailableError
from flowpilot.llm.decision_model import ClefClient, FakeDecisionModel, SubQClient

EMAIL = EmailForDecision(
    from_addr="satinalma@bilgemakina.example",
    subject="Eksik teslimat ve hatalı fatura",
    body_text="2 kaplin eksik geldi, faturada da var.",
)


# ---------- istemci ----------


class FakeResponse:
    def __init__(self, status: int, body: Any, headers: dict[str, str] | None = None) -> None:
        self.status_code = status
        self._body = body
        self.headers = headers or {}

    def json(self) -> Any:
        return self._body


class FakeHttp:
    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.posts: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, json: dict[str, Any]) -> Any:
        self.posts.append((url, json))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def clef(*responses: Any) -> tuple[ClefClient, FakeHttp, list[float]]:
    http = FakeHttp(*responses)
    sleeps: list[float] = []
    client = ClefClient(
        account_id="acc", api_token="", client=http, sleep=sleeps.append, max_retries=2
    )
    return client, http, sleeps


OK = FakeResponse(
    200,
    {
        "success": True,
        "result": {
            "answers": {
                "urgent": {"type": "noul", "noul": 0.91, "confidence": 0.91},
                "team": {
                    "type": "choice",
                    "choice": "billing",
                    "probabilities": {"billing": 0.8, "sales": 0.2},
                },
                "sev": {"type": "score", "score": 2.4, "probabilities": {"0": 0.1, "3": 0.9}},
            },
            "usage": {"total_input_tokens": 315},
        },
    },
)


def test_client_sends_state_and_questions_and_parses_envelope() -> None:
    client, http, _ = clef(OK)
    answers = client.ask(state="durum", questions={"urgent": {"type": "noul", "instructions": "?"}})
    url, body = http.posts[0]
    assert url.endswith("/accounts/acc/ai/run/@cf/cloudflare/clef-flash")
    assert body["model"] == "clef-flash" and body["state"] == "durum"
    assert answers.noul("urgent") == 0.91
    assert answers.choice("team") == ("billing", {"billing": 0.8, "sales": 0.2})
    assert answers.score("sev") == (2.4, {0: 0.1, 3: 0.9})
    assert answers.input_tokens == 315


def test_rate_limit_is_retried_with_retry_after() -> None:
    client, _, sleeps = clef(FakeResponse(429, {}, {"retry-after": "3"}), OK)
    assert client.ask(state="s", questions={}).noul("urgent") == 0.91
    assert sleeps == [3.0]


def test_unavailable_after_retries_and_errors_are_not_retried() -> None:
    client, _, _ = clef(OSError("dns"), OSError("dns"), OSError("dns"))
    with pytest.raises(LLMUnavailableError):
        client.ask(state="s", questions={})
    bad = FakeResponse(400, {"errors": [{"message": "questions geçersiz"}]})
    client, _, sleeps = clef(bad)
    with pytest.raises(LLMError, match="questions geçersiz"):
        client.ask(state="s", questions={})
    assert sleeps == []


def test_missing_answer_raises() -> None:
    client, _, _ = clef(OK)
    with pytest.raises(LLMError):
        client.ask(state="s", questions={}).noul("yok")


def test_unknown_model_or_missing_credentials_rejected() -> None:
    with pytest.raises(LLMError):
        ClefClient(account_id="a", api_token="t", model="gpt")
    with pytest.raises(LLMError):
        ClefClient(account_id="", api_token="")


def test_subq_client_posts_to_systemone_and_parses_flat_body() -> None:
    body = {
        "model": "subq-snap-1.2",
        "answers": OK.json()["result"]["answers"],
        "usage": {"input_tokens": 120, "output_tokens": 0},
    }
    http = FakeHttp(FakeResponse(200, body))
    client = SubQClient(api_key="", client=http, sleep=lambda _: None)
    answers = client.ask(state="durum", questions={"urgent": {"type": "noul", "instructions": "?"}})
    url, sent = http.posts[0]
    assert url == "https://api.subq.ai/v1/systemone"
    assert sent["model"] == "subq-snap-1.2" and sent["state"] == "durum"
    assert answers.choice("team")[0] == "billing" and answers.input_tokens == 120


def test_subq_errors_show_detail_and_bad_config_rejected() -> None:
    bad = FakeResponse(
        422, {"detail": {"error_type": "validation_error", "message": "criteria yok"}}
    )
    client = SubQClient(api_key="", client=FakeHttp(bad), sleep=lambda _: None)
    with pytest.raises(LLMError, match="validation_error: criteria yok"):
        client.ask(state="s", questions={})
    with pytest.raises(LLMError):
        SubQClient(api_key="k", model="subq-savant-1.4")
    with pytest.raises(LLMError):
        SubQClient(api_key="")


# ---------- sınıflandırıcı ----------


def respond(act: dict[str, float], priority: float = 1.0):  # noqa: ANN201
    def answer(state: str, questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {"priority": {"type": "score", "score": priority}}
        for qid, q in questions.items():
            if qid.startswith("act."):
                out[qid] = {"type": "noul", "noul": act.get(qid[4:], 0.02)}
            elif qid.startswith("intent."):
                first = next(iter(q["criteria"]))
                out[qid] = {"type": "choice", "choice": first, "probabilities": {first: 0.9}}
        return out

    return answer


def classify(act: dict[str, float], priority: float = 1.0):  # noqa: ANN201
    model = FakeDecisionModel(respond(act, priority))
    return DecisionModelClassifier(model, get_registry(), "fake")(EMAIL), model


def test_questions_cover_every_department_and_intent() -> None:
    questions = build_questions(get_registry())
    for department in get_registry():
        assert questions[f"act.{department.key}"]["type"] == "noul"
        assert set(questions[f"intent.{department.key}"]["criteria"]) == department.intent_keys()
    assert questions["priority"]["type"] == "score"
    assert len(questions) == 2 * len(get_registry()) + 2 <= 64


def test_confident_departments_become_routes() -> None:
    result, model = classify({"logistics": 0.93, "finance": 0.88}, priority=2.3)
    assert [r.department for r in result.routes] == ["logistics", "finance"]
    assert result.routes[0].intent == "shipment_request"  # sahte model ilk seçeneği seçer
    assert result.routes[0].priority == "high"
    assert not result.needs_review
    assert "Lojistik %93" in result.reasoning
    assert "Konu: Eksik teslimat ve hatalı fatura" in model.calls[0][0]


def test_no_department_is_unknown_and_reviewed() -> None:
    result, _ = classify({})
    assert [r.department for r in result.routes] == ["unknown"]
    assert result.needs_review and "eşleşmedi" in (result.review_reason or "")


def test_borderline_route_or_maybe_department_is_reviewed() -> None:
    low, _ = classify({"procurement": 0.6})
    assert low.needs_review and "eşiğin" in (low.review_reason or "")

    maybe, _ = classify({"procurement": 0.95, "logistics": 0.4})
    assert [r.department for r in maybe.routes] == ["procurement"]
    assert maybe.needs_review and "belirsiz departman: logistics" in (maybe.review_reason or "")


def v3_respond(primary: dict[str, float], also: dict[str, float]):  # noqa: ANN201
    def answer(state: str, questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        top = max(primary, key=lambda k: primary[k])
        out: dict[str, Any] = {
            "priority": {"type": "score", "score": 1.0},
            "primary": {"type": "choice", "choice": top, "probabilities": primary},
        }
        for qid, q in questions.items():
            if qid.startswith("also."):
                out[qid] = {"type": "noul", "noul": also.get(qid[5:], 0.02)}
            elif qid.startswith("intent."):
                first = next(iter(q["criteria"]))
                out[qid] = {"type": "choice", "choice": first, "probabilities": {first: 0.9}}
        return out

    return answer


def test_v3_asks_primary_then_additional_departments() -> None:
    questions = build_questions(get_registry(), "typed-v3")
    assert set(questions["primary"]["criteria"]) == {d.key for d in get_registry()} | {"none"}
    assert all(
        f"also.{d.key}" in questions and f"act.{d.key}" not in questions for d in get_registry()
    )
    with pytest.raises(ValueError):
        build_questions(get_registry(), "typed-v9")


def test_v3_combines_primary_and_additional_probabilities() -> None:
    model = FakeDecisionModel(
        v3_respond({"logistics": 0.8, "finance": 0.2}, {"finance": 0.9, "logistics": 0.05})
    )
    result = DecisionModelClassifier(model, get_registry(), "fake", prompt_version="typed-v3")(
        EMAIL
    )
    conf = {r.department: r.confidence for r in result.routes}
    # lojistik: 0,8 + 0,2·0,05 = 0,81; finans: 0,2 + 0,8·0,9 = 0,92
    assert conf == {"finance": 0.92, "logistics": 0.81}
    assert not result.needs_review

    model = FakeDecisionModel(v3_respond({"none": 0.97, "sales_orders": 0.03}, {}))
    result = DecisionModelClassifier(model, get_registry(), "fake", prompt_version="typed-v3")(
        EMAIL
    )
    assert [r.department for r in result.routes] == ["unknown"] and result.needs_review


def test_broken_answer_goes_to_review_instead_of_crashing() -> None:
    model = FakeDecisionModel(lambda state, questions: {})
    result = DecisionModelClassifier(model, get_registry(), "fake")(EMAIL)
    assert result.needs_review and result.routes == []
