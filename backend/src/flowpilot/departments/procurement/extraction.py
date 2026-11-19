"""Teklif belgesinden alan çıkarma (ADR-015).

Model yalnızca belgede yazanı şemaya döker; hesap yapmaz ve boşlukları doldurmaz. Sayıların
doğruluğu modele değil `validation.py`'deki kaynak ve aritmetik kontrollere dayanır.
"""

from pydantic import BaseModel, Field

from flowpilot.llm import LLMClient

PROMPT_VERSION = "quote-extract-v1"
TASK = "procurement.extract_quote"
MAX_DOCUMENT_CHARS = 20_000

SYSTEM = """Sen Atlas Endüstri A.Ş.'nin satın alma biriminde çalışan dikkatli bir asistansın.
Sana bir tedarikçinin gönderdiği belge metni verilecek. Görevin, belgede YAZAN bilgileri şemaya
aktarmak.

Kurallar:
- Yalnızca belgede açıkça yazan değerleri yaz. Belgede olmayan alanı null bırak.
- Hesap yapma: satır tutarı, ara toplam, KDV veya genel toplam belgede yazmıyorsa null bırak.
  Miktar × birim fiyatı kendin çarpma.
- Sayıları belgedeki değerle aynı yaz (ör. "1.234,50" → 1234.5). Yuvarlama ya da kur çevirme yapma.
- Para birimini ISO kodu olarak yaz (TL/TRY → TRY, € / Euro → EUR, $ / USD → USD).
  Belgede para birimi hiç geçmiyorsa null bırak.
- Tarihleri YYYY-AA-GG biçiminde yaz.
- Teslim süresi gün olarak yazıyorsa lead_time_days'e yaz; hafta ya da tarih olarak
  yazıyorsa null bırak.
- Belge bir fiyat teklifi değilse (fatura, irsaliye, duyuru vb.) is_quote=false yap ve satır yazma.
- "supplier" teklifi veren firmanın adıdır; Atlas Endüstri değildir.
"""


class ExtractedLine(BaseModel):
    product_code: str | None = Field(default=None, description="Ürün/stok kodu")
    description: str | None = Field(default=None, description="Ürün açıklaması")
    quantity: float | None = None
    unit: str | None = Field(default=None, description="adet, m, kg, takım …")
    unit_price: float | None = Field(default=None, description="KDV hariç birim fiyat")
    line_total: float | None = Field(default=None, description="Belgede yazıyorsa satır tutarı")
    lead_time_days: int | None = Field(default=None, description="Teslim süresi (gün)")


class QuoteExtraction(BaseModel):
    is_quote: bool
    supplier: str | None = None
    quote_no: str | None = None
    request_no: str | None = Field(default=None, description="Atlas'ın talep numarası (SAT-...)")
    currency: str | None = Field(default=None, description="ISO 4217: TRY, EUR, USD")
    valid_until: str | None = Field(default=None, description="Teklifin son geçerlilik tarihi")
    lines: list[ExtractedLine] = Field(default_factory=list)
    subtotal: float | None = Field(default=None, description="KDV hariç ara toplam")
    vat: float | None = Field(default=None, description="KDV tutarı")
    total: float | None = Field(default=None, description="Genel toplam")


def build_prompt(*, sender: str, subject: str, filename: str, text: str) -> str:
    clipped = text[:MAX_DOCUMENT_CHARS]
    return (
        f"Gönderen: {sender}\nKonu: {subject}\nBelge: {filename}\n\n"
        f"--- BELGE METNİ ---\n{clipped}\n--- BELGE SONU ---"
    )


def extract_quote(
    llm: LLMClient, *, sender: str, subject: str, filename: str, text: str
) -> QuoteExtraction:
    prompt = build_prompt(sender=sender, subject=subject, filename=filename, text=text)
    return llm.generate(task=TASK, system=SYSTEM, prompt=prompt, schema=QuoteExtraction)
