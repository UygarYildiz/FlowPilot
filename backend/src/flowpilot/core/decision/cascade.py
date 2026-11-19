"""Kademeli sınıflandırma (ADR-013): önce karar modeli, emin değilse generatif model, sonra insan.

    1. `first` (SubQ) eminse karar onundur.
    2. Değilse `second` (Gemini) bakar; eminse karar onundur.
    3. İkisi de emin değilse insana gider; panelde iki görüş de görünür.
`first` "hiçbir departman değil" diyor ve güveni ≥ `skip_unknown_at` ise `second` çağrılmaz:
ilgisiz e-posta iki motorda da incelemeye gider, ikinci çağrı sonucu değiştirmez.
Erişilemezlik: `first` yanıt vermezse `second` karar verir; `first` tereddüt edip `second`
yanıt vermezse `first`'ün önerisiyle insana gider; ikisi de yanıt vermezse hata yukarı çıkar
(e-posta `received` kalır, sonra yeniden denenir).
"""

from dataclasses import dataclass, replace

from flowpilot.core.decision.engine import Classification, Classifier
from flowpilot.core.decision.prompt import EmailForDecision
from flowpilot.core.registry import UNKNOWN
from flowpilot.llm import LLMUnavailableError

SKIP_UNKNOWN_AT = 0.95


@dataclass
class CascadeClassifier:
    first: Classifier
    second: Classifier
    skip_unknown_at: float = SKIP_UNKNOWN_AT

    @property
    def model_name(self) -> str:
        return f"cascade:{self.first.model_name}>{self.second.model_name}"

    @property
    def prompt_version(self) -> str:
        return f"{self.first.prompt_version}>{self.second.prompt_version}"

    def __call__(self, email: EmailForDecision) -> Classification:
        try:
            first = self.first(email)
        except LLMUnavailableError as exc:
            second = self.second(email)  # ikisi de erişilemezse hata yukarı çıkar
            return _tag(second, self.second.model_name, errors=[f"{self.first.model_name}: {exc}"])

        if not first.needs_review or self._clearly_unrelated(first):
            return _tag(first, self.first.model_name)

        try:
            second = self.second(email)
        except LLMUnavailableError as exc:
            return _tag(first, self.first.model_name, errors=[f"{self.second.model_name}: {exc}"])

        # İkinci emin olduysa karar onundur. İkisi de emin değilse insan karar verir; ikinci
        # rota üretemediyse (geçersiz çıktı) panelde birincinin önerisi görünür.
        use_second = not second.needs_review or bool(second.routes)
        return _combine(first, second, self.first.model_name, self.second.model_name, use_second)

    def _clearly_unrelated(self, result: Classification) -> bool:
        return (
            len(result.routes) == 1
            and result.routes[0].department == UNKNOWN
            and result.routes[0].confidence >= self.skip_unknown_at
        )


def _tag(result: Classification, model: str, errors: list[str] | None = None) -> Classification:
    raw = {"stages": [_stage(model, result)]}
    return replace(
        result, decided_by=model, raw_output=raw, errors=[*(errors or []), *result.errors]
    )


def _stage(model: str, result: Classification) -> dict:
    return {
        "model": model,
        "routes": [r.model_dump(mode="json") for r in result.routes],
        "needs_review": result.needs_review,
        "review_reason": result.review_reason,
        "reasoning": result.reasoning,
        "raw_output": result.raw_output,
    }


def _combine(
    first: Classification,
    second: Classification,
    first_model: str,
    second_model: str,
    use_second: bool,
) -> Classification:
    """İki görüşü tek karara birleştirir; gerekçe ve `raw_output` ikisini de taşır."""
    chosen, model = (second, second_model) if use_second else (first, first_model)
    reasoning = (
        f"{_short(first_model)}: {first.reasoning}\n{_short(second_model)}: {second.reasoning}"
    )
    review_reason = None
    if second.needs_review:
        review_reason = (
            f"{_short(first_model)}: {first.review_reason}; "
            f"{_short(second_model)}: {second.review_reason}"
        )
    return Classification(
        routes=chosen.routes,
        reasoning=reasoning,
        needs_review=second.needs_review,
        review_reason=review_reason,
        attempts=first.attempts + second.attempts,
        raw_output={"stages": [_stage(first_model, first), _stage(second_model, second)]},
        errors=[*first.errors, *second.errors],
        decided_by=model,
    )


PROVIDER_NAMES = {"subq": "SubQ", "gemini": "Gemini", "cloudflare": "Clef", "fake": "Sahte"}


def _short(model: str) -> str:
    provider = model.split(":", 1)[0]
    return PROVIDER_NAMES.get(provider, provider)
