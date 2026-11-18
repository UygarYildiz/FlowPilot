"""Model arayüzü (ADR-008). Uygulamanın geri kalanı modele yalnızca `LLMClient` üzerinden ulaşır."""

from flowpilot.llm.base import LLMClient, LLMError
from flowpilot.llm.fake import FakeLLM

__all__ = ["FakeLLM", "LLMClient", "LLMError"]
