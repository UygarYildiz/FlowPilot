from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Model çağrısı başarısız oldu ya da çıktı şemaya uymadı."""


class LLMUnavailableError(Exception):
    """Model geçici olarak erişilemez (ağ, kota, sunucu hatası); yeniden denemeler tükendi.

    `LLMError`'dan türemez: geçersiz çıktı manuel incelemeye gider, erişilemeyen model ise
    işi bekletir (e-posta `received` kalır ve sonra yeniden denenir).
    """


class LLMClient(Protocol):
    """Yapılandırılmış çıktı üreten model istemcisi.

    `schema` bir Pydantic modelidir; dönüş değeri o şemaya göre doğrulanmış nesnedir.
    Doğrulanamazsa `LLMError`, model erişilemezse `LLMUnavailableError` fırlatılır; tahmin edilmez.
    """

    def generate(self, *, task: str, system: str, prompt: str, schema: type[T]) -> T: ...
