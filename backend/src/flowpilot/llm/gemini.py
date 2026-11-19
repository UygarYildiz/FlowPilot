"""Gemini uygulaması (ADR-009): `google-genai` ile şemalı JSON çıktı.

Ücretsiz katmanda dakika başına istek sınırı vardır: 429, geçici sunucu ve ağ hatalarında
sunucunun önerdiği süre kadar (yoksa üstel) bekleyip yeniden dener. Denemeler tükenirse
`LLMUnavailableError` fırlatır; diğer 4xx ve geçersiz çıktı `LLMError`'dır.
"""

import json
import re
import time
from collections.abc import Callable
from typing import Any, TypeVar

import httpx2
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from flowpilot.llm.base import LLMError, LLMUnavailableError

T = TypeVar("T", bound=BaseModel)

RETRYABLE = {429, 500, 502, 503, 504}


def retry_delay(error: errors.APIError, attempt: int) -> float:
    """Sunucu `retryDelay` verdiyse onu, yoksa üstel bekleme süresini döndürür."""
    match = re.search(
        r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", json.dumps(error.details)
    )
    if match:
        return float(match.group(1)) + 1.0
    return min(2.0**attempt, 60.0)


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_retries: int = 6,
        client: Any = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key and client is None:
            raise LLMError("GEMINI_API_KEY ayarlanmamış")
        if not model:
            raise LLMError("FLOWPILOT_LLM_MODEL ayarlanmamış")
        self.model = model
        self._client = client or genai.Client(api_key=api_key)
        self._max_retries = max_retries
        self._sleep = sleep

    def generate(self, *, task: str, system: str, prompt: str, schema: type[T]) -> T:
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
        )
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model, contents=prompt, config=config
                )
                break
            except errors.APIError as exc:
                if exc.code not in RETRYABLE:
                    raise LLMError(f"Gemini hatası ({task}): {exc.code} {exc.status}") from exc
                if attempt == self._max_retries:
                    raise LLMUnavailableError(
                        f"Gemini erişilemez ({task}): {exc.code} {exc.status}"
                    ) from exc
                self._sleep(retry_delay(exc, attempt))
            except (OSError, httpx2.TransportError) as exc:
                if attempt == self._max_retries:
                    raise LLMUnavailableError(f"Gemini'ye bağlanılamadı ({task}): {exc}") from exc
                self._sleep(min(2.0**attempt, 60.0))
        else:  # pragma: no cover - döngü her zaman break ya da raise ile biter
            raise LLMUnavailableError(f"Gemini yanıt vermedi ({task})")

        text = getattr(response, "text", None)
        if not text:
            raise LLMError(f"Gemini boş yanıt döndü ({task})")
        try:
            return schema.model_validate_json(text)
        except ValidationError as exc:
            raise LLMError(
                f"Gemini çıktısı şemaya uymuyor ({task}): {exc.error_count()} hata"
            ) from exc
