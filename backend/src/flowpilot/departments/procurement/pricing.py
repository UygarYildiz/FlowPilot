"""Fiyat güncellemesi (`price_update` → `update_supplier_prices`; ADR-016).

Model fiyat listesini çıkarır; önceki fiyat önce kayıtlardan (`known_prices` aracı), yoksa
belgedeki "eski fiyat" sütunundan alınır ve kaynağı yazılır. Sayılar kaynak kontrolünden geçer.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from pydantic import BaseModel, Field

from flowpilot.departments.procurement.catalog import DEMO_FX_TRY, PRODUCTS
from flowpilot.departments.procurement.validation import Issue, numbers_in, parse_date, to_decimal
from flowpilot.llm import LLMClient

TASK = "procurement.extract_price_list"
SYSTEM = """Sen Atlas Endüstri A.Ş.'nin satın alma biriminde çalışan dikkatli bir asistansın.
Sana bir tedarikçinin fiyat güncellemesi e-postası ve eki verilecek. Görevin belgede YAZAN fiyatları
şemaya aktarmak.

Kurallar:
- Yalnızca belgede yazan değerleri yaz; olmayan alanı null bırak. Hesap yapma, yuvarlama.
- Sayıları belgedeki değerle aynı yaz (ör. "8.420,00" → 8420).
- old_price: belgede "eski fiyat" olarak yazıyorsa; new_price: yeni/güncel fiyat.
- Para birimini ISO kodu olarak yaz (TL/TRY → TRY). Belgede yoksa null.
- valid_from: yeni fiyatların geçerli olacağı ilk tarih (YYYY-AA-GG).
- Belge bir fiyat listesi değilse is_price_list=false yap ve kalem yazma.
"""


class ExtractedPrice(BaseModel):
    product_code: str | None = None
    description: str | None = None
    unit: str | None = None
    old_price: float | None = None
    new_price: float | None = None


class PriceListExtraction(BaseModel):
    is_price_list: bool
    supplier: str | None = None
    currency: str | None = None
    valid_from: str | None = None
    items: list[ExtractedPrice] = Field(default_factory=list)


class PriceItem(BaseModel):
    product_code: str
    description: str = ""
    unit: str | None = None
    new_price: Decimal
    previous_price: Decimal | None = None
    previous_source: str | None = None
    change_pct: Decimal | None = None


class PriceUpdateData(BaseModel):
    """`update_supplier_prices` önerisinin verisi."""

    source_filename: str
    supplier: str
    currency: str | None = None
    valid_from: date | None = None
    items: list[PriceItem] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)


def build_prompt(*, sender: str, subject: str, body: str, filename: str, text: str) -> str:
    return (
        f"Gönderen: {sender}\nKonu: {subject}\n\n--- E-POSTA ---\n{body[:4000]}\n"
        f"--- EK: {filename} ---\n{text[:16000]}\n--- SON ---"
    )


def extract_price_list(llm: LLMClient, **kwargs: str) -> PriceListExtraction:
    return llm.generate(
        task=TASK, system=SYSTEM, prompt=build_prompt(**kwargs), schema=PriceListExtraction
    )


def build_update(
    extraction: PriceListExtraction,
    source_text: str,
    *,
    source_filename: str,
    fallback_supplier: str,
    known: dict[str, dict[str, Any]],
) -> PriceUpdateData:
    """`known`: ürün koduna göre kayıtlı önceki fiyat (`price`, `currency`, `source`)."""
    issues: list[Issue] = []
    seen = numbers_in(source_text)
    supplier = (extraction.supplier or "").strip() or fallback_supplier
    if not (extraction.supplier or "").strip():
        issues.append(Issue(field="supplier", level="warning", message="Tedarikçi adı yok."))
    currency = (extraction.currency or "").strip().upper() or None
    if currency is None:
        issues.append(Issue(field="currency", level="error", message="Para birimi belgede yok."))
    elif currency not in DEMO_FX_TRY:
        issues.append(Issue(field="currency", level="warning", message="Bilinmeyen para birimi."))
    valid_from = parse_date(extraction.valid_from)

    items: list[PriceItem] = []
    for index, raw in enumerate(extraction.items):
        prefix = f"items[{len(items)}]"
        code = (raw.product_code or "").strip()
        new = to_decimal(raw.new_price)
        if not code or new is None:
            issues.append(
                Issue(
                    field=f"items[{index}]",
                    level="error",
                    message="Kod ya da yeni fiyat yok; kalem atlandı.",
                )
            )
            continue
        old_doc = to_decimal(raw.old_price)
        for field, value in (("new_price", new), ("previous_price", old_doc)):
            if value is not None and value not in seen:
                issues.append(
                    Issue(
                        field=f"{prefix}.{field}",
                        level="error",
                        message="Bu sayı belgede geçmiyor.",
                    )
                )
        if new <= 0:
            issues.append(
                Issue(
                    field=f"{prefix}.new_price",
                    level="error",
                    message="Fiyat sıfırdan büyük değil.",
                )
            )
        if code not in PRODUCTS:
            issues.append(
                Issue(field=f"{prefix}.product_code", level="warning", message="Kod katalogda yok.")
            )

        previous, source = None, None
        record = known.get(code)
        if record and record.get("currency") == currency and record.get("price") is not None:
            previous, source = Decimal(str(record["price"])), str(record["source"])
            if old_doc is not None and old_doc != previous:
                issues.append(
                    Issue(
                        field=f"{prefix}.previous_price",
                        level="warning",
                        message=f"Belgedeki eski fiyat ({old_doc}) kayıtlı fiyatla ({previous}) "
                        "aynı değil.",
                    )
                )
        elif old_doc is not None:
            previous, source = old_doc, "belgedeki eski fiyat"
        change = (
            ((new - previous) / previous * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)
            if previous
            else None
        )
        items.append(
            PriceItem(
                product_code=code,
                description=(raw.description or "").strip(),
                unit=raw.unit,
                new_price=new,
                previous_price=previous,
                previous_source=source,
                change_pct=change,
            )
        )
    if not items:
        issues.append(Issue(field="items", level="error", message="Fiyat kalemi bulunamadı."))
    return PriceUpdateData(
        source_filename=source_filename,
        supplier=supplier,
        currency=currency,
        valid_from=valid_from,
        items=items,
        issues=issues,
    )


def summary(data: PriceUpdateData) -> str:
    ups = [i for i in data.items if i.change_pct is not None and i.change_pct > 0]
    downs = [i for i in data.items if i.change_pct is not None and i.change_pct < 0]
    same = [i for i in data.items if i.change_pct == 0]
    parts = []
    if ups:
        avg = sum((i.change_pct or Decimal(0) for i in ups), Decimal(0)) / len(ups)
        parts.append(
            f"{len(ups)} zam (ort. %{str(avg.quantize(Decimal('0.1'))).replace('.', ',')})"
        )
    if downs:
        parts.append(f"{len(downs)} indirim")
    if same:
        parts.append(f"{len(same)} değişmedi")
    when = f", {data.valid_from:%d.%m.%Y} itibarıyla" if data.valid_from else ""
    detail = f": {', '.join(parts)}" if parts else ""
    return f"{data.supplier} fiyatlarını güncelle — {len(data.items)} ürün{detail}{when}"
