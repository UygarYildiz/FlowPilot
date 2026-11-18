import pytest
from pydantic import BaseModel

from flowpilot.llm import FakeLLM, LLMError


class Route(BaseModel):
    department: str
    confidence: float


def test_returns_recorded_response() -> None:
    llm = FakeLLM()
    llm.add("classify", "teklif ekte", {"department": "procurement", "confidence": 0.9})
    result = llm.generate(task="classify", system="", prompt="teklif ekte", schema=Route)
    assert result == Route(department="procurement", confidence=0.9)


def test_unknown_prompt_raises() -> None:
    with pytest.raises(LLMError):
        FakeLLM().generate(task="classify", system="", prompt="?", schema=Route)


def test_invalid_recorded_response_raises() -> None:
    llm = FakeLLM()
    llm.add("classify", "x", {"department": "procurement"})
    with pytest.raises(LLMError):
        llm.generate(task="classify", system="", prompt="x", schema=Route)
