"""Gemini istemcisi, ağ olmadan sahte bir SDK istemcisiyle test edilir."""

from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import errors
from pydantic import BaseModel

from flowpilot.llm import LLMError, LLMUnavailableError
from flowpilot.llm.gemini import GeminiClient, retry_delay


class Answer(BaseModel):
    department: str


def rate_limited(delay: str | None = "7s") -> errors.APIError:
    details = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}]
    body = {
        "error": {
            "code": 429,
            "status": "RESOURCE_EXHAUSTED",
            "message": "kota",
            "details": details,
        }
    }
    return errors.APIError(429, body)


class FakeModels:
    def __init__(self, *results: Any) -> None:
        self.results = list(results)
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return SimpleNamespace(text=result)


def client(*results: Any) -> tuple[GeminiClient, FakeModels, list[float]]:
    models = FakeModels(*results)
    sleeps: list[float] = []
    gemini = GeminiClient(
        api_key="",
        model="gemini-test",
        client=SimpleNamespace(models=models),
        sleep=sleeps.append,
        max_retries=2,
    )
    return gemini, models, sleeps


def test_returns_validated_object_and_sends_schema() -> None:
    gemini, models, _ = client('{"department": "finance"}')
    answer = gemini.generate(task="t", system="sistem", prompt="p", schema=Answer)
    assert answer == Answer(department="finance")
    config = models.calls[0]["config"]
    assert models.calls[0]["model"] == "gemini-test"
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema["properties"]["department"]["type"] == "string"
    assert config.system_instruction == "sistem"


def test_rate_limit_waits_server_delay_then_succeeds() -> None:
    gemini, _, sleeps = client(rate_limited("7s"), '{"department": "finance"}')
    assert gemini.generate(task="t", system="", prompt="p", schema=Answer).department == "finance"
    assert sleeps == [8.0]


def test_gives_up_after_max_retries() -> None:
    gemini, _, sleeps = client(rate_limited(), rate_limited(), rate_limited())
    with pytest.raises(LLMUnavailableError, match="429"):
        gemini.generate(task="t", system="", prompt="p", schema=Answer)
    assert len(sleeps) == 2


def test_network_errors_are_retried_then_unavailable() -> None:
    gemini, _, sleeps = client(OSError("dns"), '{"department": "finance"}')
    assert gemini.generate(task="t", system="", prompt="p", schema=Answer).department == "finance"
    assert sleeps == [1.0]

    gemini, _, _ = client(OSError("dns"), OSError("dns"), OSError("dns"))
    with pytest.raises(LLMUnavailableError, match="bağlanılamadı"):
        gemini.generate(task="t", system="", prompt="p", schema=Answer)


def test_client_error_is_not_retried() -> None:
    gemini, _, sleeps = client(errors.APIError(400, {"error": {"code": 400, "message": "kötü"}}))
    with pytest.raises(LLMError, match="400"):
        gemini.generate(task="t", system="", prompt="p", schema=Answer)
    assert sleeps == []


def test_invalid_or_empty_output_raises() -> None:
    gemini, _, _ = client('{"dept": 1}', "")
    with pytest.raises(LLMError, match="şemaya uymuyor"):
        gemini.generate(task="t", system="", prompt="p", schema=Answer)
    with pytest.raises(LLMError, match="boş"):
        gemini.generate(task="t", system="", prompt="p", schema=Answer)


def test_retry_delay_falls_back_to_exponential() -> None:
    error = errors.APIError(503, {"error": {"code": 503, "message": "meşgul"}})
    assert retry_delay(error, 0) == 1.0
    assert retry_delay(error, 3) == 8.0
    assert retry_delay(rate_limited("12.5s"), 0) == 13.5
