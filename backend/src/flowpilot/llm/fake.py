import hashlib
import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from flowpilot.llm.base import LLMError

T = TypeVar("T", bound=BaseModel)


def prompt_key(task: str, prompt: str) -> str:
    """Bir isteğin kayıtlı cevabını bulmak için kararlı anahtar."""
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    return f"{task}:{digest}"


class FakeLLM:
    """Testler ve CI için deterministik model: kayıtlı cevapları döndürür (ADR-008).

    Cevaplar `task` + prompt özetiyle eşleştirilir. Kayıt yoksa `LLMError` fırlatır;
    böylece testte beklenmeyen bir istek sessizce geçmez.
    """

    def __init__(self, responses: dict[str, dict[str, Any]] | None = None) -> None:
        self._responses: dict[str, dict[str, Any]] = dict(responses or {})
        self.calls: list[str] = []

    def add(self, task: str, prompt: str, response: dict[str, Any]) -> None:
        self._responses[prompt_key(task, prompt)] = response

    def generate(self, *, task: str, system: str, prompt: str, schema: type[T]) -> T:
        key = prompt_key(task, prompt)
        self.calls.append(key)
        if key not in self._responses:
            raise LLMError(f"Sahte modelde kayıtlı cevap yok: {key}")
        try:
            return schema.model_validate_json(json.dumps(self._responses[key]))
        except ValidationError as exc:
            raise LLMError(f"Kayıtlı cevap şemaya uymuyor: {key}") from exc
