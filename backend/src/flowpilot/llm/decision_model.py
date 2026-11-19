"""Karar modelleri (System One API): Cloudflare Clef, SubQ Snap.

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
SUBQ_API = "https://api.subq.ai/v1"


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
        return _post(self, self._url, body, "Clef", _cloudflare_errors)


class SubQClient:
    """SubQ Decisions API (POST /v1/systemone); SUBQ_API_KEY gerekir. Model: subq-snap-1.2."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "subq-snap-1.2",
        max_retries: int = 5,
        timeout: float = 60.0,
        client: Any = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not model.startswith("subq-snap"):
            raise LLMError(f"SubQ karar modeli değil: {model}")
        if client is None and not api_key:
            raise LLMError("SUBQ_API_KEY ayarlanmamış")
        self.model = model
        self._url = f"{SUBQ_API}/systemone"
        self._client = client or httpx2.Client(
            timeout=timeout, headers={"Authorization": f"Bearer {api_key}"}
        )
        self._max_retries = max_retries
        self._sleep = sleep

    def ask(self, *, state: str, questions: dict[str, dict[str, Any]]) -> DecisionAnswers:
        body = {"model": self.model, "state": state, "questions": questions}
        return _post(self, self._url, body, "SubQ", _subq_errors)


def _post(
    owner: Any, url: str, body: dict[str, Any], name: str, errors: Callable[[Any], str]
) -> DecisionAnswers:
    """İki istemcinin ortak isteği: geçici hatalarda (ağ, 429, 5xx) bekleyip yeniden dener."""
    for attempt in range(owner._max_retries + 1):
        try:
            response = owner._client.post(url, json=body)
        except (OSError, httpx2.TransportError) as exc:
            if attempt == owner._max_retries:
                raise LLMUnavailableError(f"{name} sunucusuna bağlanılamadı: {exc}") from exc
            owner._sleep(_backoff(attempt))
            continue
        if response.status_code in RETRYABLE:
            if attempt == owner._max_retries:
                raise LLMUnavailableError(f"{name} erişilemez: HTTP {response.status_code}")
            retry_after = response.headers.get("retry-after")
            owner._sleep(float(retry_after) if retry_after else _backoff(attempt))
            continue
        if response.status_code >= 400:
            raise LLMError(f"{name} hatası: HTTP {response.status_code} {errors(response)}")
        return _parse(response.json())
    raise LLMUnavailableError(f"{name} yanıt vermedi")  # pragma: no cover


def _backoff(attempt: int) -> float:
    return min(2.0**attempt, 30.0) + random.uniform(0, 0.5)


def _cloudflare_errors(response: Any) -> str:
    try:
        return "; ".join(e.get("message", "") for e in response.json().get("errors", []))[:300]
    except ValueError:
        return ""


def _subq_errors(response: Any) -> str:
    # SubQ hata gövdesi: {"detail": {"error_type": ..., "message": ...}}
    try:
        detail = response.json().get("detail")
    except ValueError:
        return ""
    if isinstance(detail, dict):
        return f"{detail.get('error_type', '')}: {detail.get('message', '')}"[:300]
    return str(detail or "")[:300]


def _parse(payload: dict[str, Any]) -> DecisionAnswers:
    # Workers AI REST cevabı {"success", "result": {...}} zarfındadır; SubQ cevabı zarfsızdır.
    result = payload.get("result", payload)
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
        raise LLMError("Karar modeli cevabında 'answers' yok")
    usage = result.get("usage") or {}
    tokens = usage.get("total_input_tokens", usage.get("input_tokens"))
    return DecisionAnswers(result["answers"], tokens)


class FakeDecisionModel:
    """Testler için: verilen cevap işlevini çağırır."""

    model = "fake-decision"

    def __init__(self, respond: Callable[[str, dict[str, dict[str, Any]]], dict[str, Any]]) -> None:
        self._respond = respond
        self.calls: list[tuple[str, dict[str, dict[str, Any]]]] = []

    def ask(self, *, state: str, questions: dict[str, dict[str, Any]]) -> DecisionAnswers:
        self.calls.append((state, questions))
        return DecisionAnswers(self._respond(state, questions))
