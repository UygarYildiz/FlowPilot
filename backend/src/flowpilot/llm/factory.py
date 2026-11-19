from flowpilot.config import Settings
from flowpilot.llm.base import LLMClient, LLMError
from flowpilot.llm.fake import FakeLLM


def build_llm(settings: Settings) -> tuple[LLMClient, str]:
    """Ayarlara göre model istemcisini ve kayıtlarda görünecek model adını döndürür."""
    if settings.llm_provider == "fake":
        return FakeLLM(), "fake"
    if settings.llm_provider == "gemini":
        from flowpilot.llm.gemini import GeminiClient

        client = GeminiClient(api_key=settings.gemini_api_key, model=settings.llm_model)
        return client, f"gemini:{settings.llm_model}"
    raise LLMError(f"Bilinmeyen LLM sağlayıcısı: {settings.llm_provider}")
