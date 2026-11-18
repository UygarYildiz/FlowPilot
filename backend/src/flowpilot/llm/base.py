from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Model çağrısı başarısız oldu ya da çıktı şemaya uymadı."""


class LLMClient(Protocol):
    """Yapılandırılmış çıktı üreten model istemcisi.

    `schema` bir Pydantic modelidir; dönüş değeri o şemaya göre doğrulanmış nesnedir.
    Doğrulanamazsa `LLMError` fırlatılır; tahmin edilmez.
    """

    def generate(self, *, task: str, system: str, prompt: str, schema: type[T]) -> T: ...
