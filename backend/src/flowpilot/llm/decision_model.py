"""Karar modelleri (System One API): Cloudflare Clef, TypeSafe Jev.

Generatif LLM'den farkı: metin üretmez. Bir durum (state) ve tipli sorular alır, her izinli
cevap için olasılık döndürür. Soru türleri:
    noul   — evet/hayır; cevap: {"noul": p(evet)}
    choice — seçeneklerden biri; cevap: {"choice": anahtar, "probabilities": {anahtar: p}}
    score  — sıralı seviyeler; cevap: {"score": beklenen seviye, "probabilities": {"0": p, ...}}
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx2

from flowpilot.llm.base import LLMError, LLMUnavailableError

RETRYABLE = {429, 500, 502, 503, 504}
CLOUDFLARE_API = "https://api.cloudflare.com/client/v4"
CLEF_MODELS = {"clef", "clef-flash"}


@dataclass(frozen=True)
class DecisionAnswers:
    answers: dict[str, dict[str, Any]]
    input_tokens: int | None = None

    def noul(self, question_id: str) -> float:
        return float(self._get(question_id, "noul")["noul"])

    def choice(self, question_id: str) -> tuple[str, dict[str, float]]:
        answer = self._get(question_id, "choice")
        probabilities = {k: float(v) for k, v in answer.get("probabilities", {}).items()}
        return str(answer["choice"]), probabilities

    def score(self, question_id: str) -> tuple[float, dict[int, float]]:
        answer = self._get(question_id, "score")
        probabilities = {int(k): float(v) for k, v in answer.get("probabilities", {}).items()}
        return float(answer["score"]), probabilities

    def _get(self, question_id: str, field: str) -> dict[str, Any]:
        answer = self.answers.get(question_id)
        if not isinstance(answer, dict) or field not in answer:
            raise LLMError(f"Karar modeli cevabında '{question_id}' ({field}) yok")
        return answer


class DecisionModelClient(Protocol):
    model: str

    def ask(self, *, state: str, questions: dict[str, dict[str, Any]]) -> DecisionAnswers: ...


class ClefClient:
    """Workers AI REST API'si üzerinden Clef; hesap kimliği ve Workers AI izinli anahtar gerekir."""

    def __init__(
        self,
        *,
        account_id: str,
        api_token: str,
        model: str = "clef-flash",
        max_retries: int = 5,
        timeout: float = 60.0,
        client: Any = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if model not in CLEF_MODELS:
            raise LLMError(f"Bilinmeyen Clef modeli: {model}")
        if client is None and not (account_id and api_token):
            raise LLMError("CLOUDFLARE_ACCOUNT_ID ve CLOUDFLARE_API_TOKEN ayarlanmamış")
        self.model = model
        self._url = f"{CLOUDFLARE_API}/accounts/{account_id}/ai/run/@cf/cloudflare/{model}"
        self._client = client or httpx2.Client(
            timeout=timeout, headers={"Authorization": f"Bearer {api_token}"}
        )
        self._max_retries = max_retries
        self._sleep = sleep

    def ask(self, *, state: str, questions: dict[str, dict[str, Any]]) -> DecisionAnswers:
        body = {"model": self.model, "state": state, "questions": questions}
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.post(self._url, json=body)
            except (OSError, httpx2.TransportError) as exc:
                if attempt == self._max_retries:
                    raise LLMUnavailableError(f"Cloudflare'e bağlanılamadı: {exc}") from exc
                self._sleep(_backoff(attempt))
                continue
            if response.status_code in RETRYABLE:
                if attempt == self._max_retries:
                    raise LLMUnavailableError(f"Clef erişilemez: HTTP {response.status_code}")
                retry_after = response.headers.get("retry-after")
                self._sleep(float(retry_after) if retry_after else _backoff(attempt))
                continue
            if response.status_code >= 400:
                raise LLMError(f"Clef hatası: HTTP {response.status_code} {_errors(response)}")
            return _parse(response.json())
        raise LLMUnavailableError("Clef yanıt vermedi")  # pragma: no cover


def _backoff(attempt: int) -> float:
    return min(2.0**attempt, 30.0) + random.uniform(0, 0.5)


def _errors(response: Any) -> str:
    try:
        return "; ".join(e.get("message", "") for e in response.json().get("errors", []))[:300]
    except ValueError:
        return ""


def _parse(payload: dict[str, Any]) -> DecisionAnswers:
    # Workers AI REST cevabı {"success", "result": {...}} zarfındadır.
    result = payload.get("result", payload)
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
        raise LLMError("Karar modeli cevabında 'answers' yok")
    usage = result.get("usage") or {}
    return DecisionAnswers(result["answers"], usage.get("total_input_tokens"))


class FakeDecisionModel:
    """Testler için: verilen cevap işlevini çağırır."""

    model = "fake-decision"

    def __init__(self, respond: Callable[[str, dict[str, dict[str, Any]]], dict[str, Any]]) -> None:
        self._respond = respond
        self.calls: list[tuple[str, dict[str, dict[str, Any]]]] = []

    def ask(self, *, state: str, questions: dict[str, dict[str, Any]]) -> DecisionAnswers:
        self.calls.append((state, questions))
        return DecisionAnswers(self._respond(state, questions))
