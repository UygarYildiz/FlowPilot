"""Çıkarılan teklifin deterministik doğrulaması (ADR-015, kriter 5).

Hiçbir değer düzeltilmez ya da tahmin edilmez. Tutmayan alan `Issue` ile işaretlenir:
- `error`: kaynakta yok, aritmetik tutmuyor, zorunlu alan eksik → bu sayıya güvenilmez.
- `warning`: katalogda yok, süresi geçmiş, tedarikçi adı yok → bilgi.
"""

import re
from contextlib import suppress
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, Field

from flowpilot.departments.procurement.catalog import DEMO_FX_TRY, PRODUCTS
from flowpilot.departments.procurement.extraction import QuoteExtraction

TOLERANCE = Decimal("0.01")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


class Issue(BaseModel):
    field: str
    level: Literal["error", "warning"]
    message: str


class QuoteLineData(BaseModel):
    product_code: str | None = None
    description: str = ""
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    line_total: Decimal | None = None
    lead_time_days: int | None = None


class QuoteData(BaseModel):
    """`record_quote` önerisinin verisi: çıkarılan + doğrulanan teklif."""

    source_filename: str
    supplier: str
    quote_no: str | None = None
    request_no: str | None = None
    currency: str | None = None
    valid_until: date | None = None
    lines: list[QuoteLineData] = Field(default_factory=list)
    subtotal: Decimal | None = None
    vat: Decimal | None = None
    total: Decimal | None = None
    issues: list[Issue] = Field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    def flagged(self, field: str) -> bool:
        return any(i.field == field and i.level == "error" for i in self.issues)


def _variants(token: str) -> set[Decimal]:
    """Bir sayı yazımının TR (1.234,56) ve EN (1,234.56) okumalarının hepsi."""
    t = token.strip(".,")
    found: set[Decimal] = set()

    def add(s: str) -> None:
        with suppress(InvalidOperation):
            found.add(Decimal(s))

    if not t:
        return found
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            add(t.replace(".", "").replace(",", "."))
        else:
            add(t.replace(",", ""))
    elif "," in t:
        if t.count(",") == 1:
            add(t.replace(",", "."))
        add(t.replace(",", ""))
    elif "." in t:
        if t.count(".") == 1:
            add(t)
        add(t.replace(".", ""))
    else:
        add(t)
    return found


def numbers_in(text: str) -> set[Decimal]:
    numbers: set[Decimal] = set()
    for token in _NUMBER.findall(text):
        numbers |= _variants(token)
    return numbers


def to_decimal(value: float | int | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(repr(value)) if isinstance(value, float) else Decimal(value)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def validate(
    extraction: QuoteExtraction,
    source_text: str,
    *,
    source_filename: str,
    fallback_supplier: str,
    today: date | None = None,
) -> QuoteData:
    today = today or date.today()
    issues: list[Issue] = []
    seen = numbers_in(source_text)

    def grounded(field: str, value: Decimal | int | None) -> None:
        if value is not None and Decimal(value) not in seen:
            issues.append(Issue(field=field, level="error", message="Bu sayı belgede geçmiyor."))

    supplier = (extraction.supplier or "").strip()
    if not supplier:
        supplier = fallback_supplier
        issues.append(
            Issue(field="supplier", level="warning", message="Tedarikçi adı belgede bulunamadı.")
        )

    currency = (extraction.currency or "").strip().upper() or None
    if currency is None:
        issues.append(Issue(field="currency", level="error", message="Para birimi belgede yok."))
    elif currency not in DEMO_FX_TRY:
        issues.append(
            Issue(field="currency", level="warning", message=f"Bilinmeyen para birimi: {currency}")
        )

    valid_until = parse_date(extraction.valid_until)
    if extraction.valid_until and valid_until is None:
        issues.append(
            Issue(field="valid_until", level="warning", message="Geçerlilik tarihi okunamadı.")
        )
    elif valid_until is not None and valid_until < today:
        issues.append(
            Issue(
                field="valid_until", level="warning", message="Teklifin geçerlilik süresi dolmuş."
            )
        )

    lines: list[QuoteLineData] = []
    computed_sum = Decimal(0)
    sum_known = True
    for index, raw in enumerate(extraction.lines):
        prefix = f"lines[{index}]"
        line = QuoteLineData(
            product_code=(raw.product_code or "").strip() or None,
            description=(raw.description or "").strip(),
            quantity=to_decimal(raw.quantity),
            unit=raw.unit,
            unit_price=to_decimal(raw.unit_price),
            line_total=to_decimal(raw.line_total),
            lead_time_days=raw.lead_time_days,
        )
        lines.append(line)
        grounded(f"{prefix}.quantity", line.quantity)
        grounded(f"{prefix}.unit_price", line.unit_price)
        grounded(f"{prefix}.line_total", line.line_total)
        grounded(f"{prefix}.lead_time_days", line.lead_time_days)

        if line.quantity is None:
            issues.append(Issue(field=f"{prefix}.quantity", level="error", message="Miktar yok."))
        elif line.quantity <= 0:
            issues.append(
                Issue(
                    field=f"{prefix}.quantity",
                    level="error",
                    message="Miktar sıfırdan büyük değil.",
                )
            )
        if line.unit_price is None:
            issues.append(
                Issue(field=f"{prefix}.unit_price", level="error", message="Birim fiyat yok.")
            )
        if line.product_code is None:
            issues.append(
                Issue(field=f"{prefix}.product_code", level="warning", message="Ürün kodu yok.")
            )
        elif line.product_code not in PRODUCTS:
            issues.append(
                Issue(
                    field=f"{prefix}.product_code",
                    level="warning",
                    message="Ürün kodu katalogda yok.",
                )
            )

        if line.quantity is not None and line.unit_price is not None:
            product = line.quantity * line.unit_price
            if line.line_total is not None and abs(product - line.line_total) > TOLERANCE:
                for field in ("quantity", "unit_price", "line_total"):
                    issues.append(
                        Issue(
                            field=f"{prefix}.{field}",
                            level="error",
                            message=f"Miktar × birim fiyat ({product:.2f}) satır tutarını"
                            " tutmuyor.",
                        )
                    )
            computed_sum += line.line_total if line.line_total is not None else product
        elif line.line_total is not None:
            computed_sum += line.line_total
        else:
            sum_known = False

    subtotal, vat, total = (
        to_decimal(extraction.subtotal),
        to_decimal(extraction.vat),
        to_decimal(extraction.total),
    )
    grounded("subtotal", subtotal)
    grounded("vat", vat)
    grounded("total", total)
    tolerance = TOLERANCE * (len(lines) + 1)
    if subtotal is not None and sum_known and lines and abs(computed_sum - subtotal) > tolerance:
        issues.append(
            Issue(
                field="subtotal",
                level="error",
                message=f"Satırların toplamı ({computed_sum:.2f}) ara toplamı tutmuyor.",
            )
        )
    if subtotal is not None and vat is not None and total is not None:
        if abs(subtotal + vat - total) > TOLERANCE:
            issues.append(
                Issue(
                    field="total", level="error", message="Ara toplam + KDV genel toplamı tutmuyor."
                )
            )
    elif total is not None and vat is None and sum_known and lines:
        base = subtotal if subtotal is not None else computed_sum
        if abs(base - total) > tolerance:
            issues.append(
                Issue(
                    field="total",
                    level="warning",
                    message="Genel toplam satırlarla tutmuyor (KDV ayrı yazılmamış olabilir).",
                )
            )

    if not lines:
        issues.append(Issue(field="lines", level="error", message="Teklifte satır bulunamadı."))

    return QuoteData(
        source_filename=source_filename,
        supplier=supplier,
        quote_no=(extraction.quote_no or "").strip() or None,
        request_no=(extraction.request_no or "").strip() or None,
        currency=currency,
        valid_until=valid_until,
        lines=lines,
        subtotal=subtotal,
        vat=vat,
        total=total,
        issues=issues,
    )
