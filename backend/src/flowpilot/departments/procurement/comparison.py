"""Aynı talebe gelen tekliflerin karşılaştırılması ve satın alma taslağı (ADR-015).

Ürün koduna göre: birim fiyat sabit demo kuruyla TRY'ye çevrilir, en düşük seçilir; eşitlikte
kısa teslim süresi. Hatalı (error) işaretli satırlar karşılaştırmaya girmez. Seçim kullanıcınındır:
ajan yalnızca önerir ve gerekçesini yazar.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, Field

from flowpilot.departments.procurement.catalog import DEMO_FX_TRY
from flowpilot.departments.procurement.validation import QuoteData

CENT = Decimal("0.01")


def tr_number(value: Decimal) -> str:
    """1234.5 → "1.234,50" (gerekçe metni Türkçe okunur)."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Offer(BaseModel):
    supplier: str
    quote_no: str | None = None
    currency: str
    unit_price: Decimal
    unit_price_try: Decimal
    lead_time_days: int | None = None
    valid_until: date | None = None


class DraftLine(BaseModel):
    product_code: str
    description: str = ""
    quantity: Decimal
    unit: str | None = None
    chosen: Offer
    line_total_try: Decimal
    alternatives: list[Offer] = Field(default_factory=list)


class PurchaseDraftData(BaseModel):
    """`purchase_draft` önerisinin verisi."""

    request_no: str
    currency: str = "TRY"
    lines: list[DraftLine]
    total: Decimal
    reasoning: str
    fx_note: str


def _usable_offers(quote: QuoteData, today: date) -> list[tuple[str, str, Decimal, Offer]]:
    if quote.currency not in DEMO_FX_TRY or quote.flagged("currency"):
        return []
    if quote.valid_until is not None and quote.valid_until < today:
        return []
    rate = DEMO_FX_TRY[quote.currency]
    out = []
    for index, line in enumerate(quote.lines):
        prefix = f"lines[{index}]"
        if (
            line.product_code is None
            or line.unit_price is None
            or line.quantity is None
            or any(quote.flagged(f"{prefix}.{f}") for f in ("unit_price", "quantity"))
        ):
            continue
        offer = Offer(
            supplier=quote.supplier,
            quote_no=quote.quote_no,
            currency=quote.currency,
            unit_price=line.unit_price,
            unit_price_try=(line.unit_price * rate).quantize(CENT, ROUND_HALF_UP),
            lead_time_days=line.lead_time_days,
            valid_until=quote.valid_until,
        )
        out.append((line.product_code, line.description, line.quantity, offer))
    return out


def compare(
    request_no: str, quotes: list[QuoteData], *, today: date | None = None
) -> PurchaseDraftData | None:
    """En az iki farklı tedarikçinin karşılaştırılabilir satırı yoksa `None`."""
    today = today or date.today()
    by_product: dict[str, list[tuple[str, Decimal, Offer]]] = {}
    for quote in quotes:
        for code, description, quantity, offer in _usable_offers(quote, today):
            by_product.setdefault(code, []).append((description, quantity, offer))

    suppliers = {o.supplier for offers in by_product.values() for _, _, o in offers}
    if len(suppliers) < 2:
        return None

    lines: list[DraftLine] = []
    reasons: list[str] = []
    for code in sorted(by_product):
        offers = by_product[code]
        ranked = sorted(offers, key=lambda x: (x[2].unit_price_try, x[2].lead_time_days or 10**6))
        description, quantity, chosen = ranked[0]
        alternatives = [o for _, _, o in ranked[1:]]
        lines.append(
            DraftLine(
                product_code=code,
                description=description,
                quantity=quantity,
                chosen=chosen,
                line_total_try=(quantity * chosen.unit_price_try).quantize(CENT, ROUND_HALF_UP),
                alternatives=alternatives,
            )
        )
        if alternatives:
            nearest = alternatives[0]
            diff = (nearest.unit_price_try - chosen.unit_price_try).quantize(CENT, ROUND_HALF_UP)
            reason = (
                f"{code}: {chosen.supplier} en ucuz ({tr_number(chosen.unit_price_try)} TRY/birim; "
                f"{nearest.supplier} {tr_number(nearest.unit_price_try)} TRY, "
                f"fark {tr_number(diff)} TRY)"
            )
            if (
                chosen.lead_time_days is not None
                and nearest.lead_time_days is not None
                and chosen.lead_time_days > nearest.lead_time_days
            ):
                reason += (
                    f"; ama teslim süresi daha uzun ({chosen.lead_time_days} gün, "
                    f"{nearest.supplier} {nearest.lead_time_days} gün)"
                )
            reasons.append(reason + ".")
        else:
            reasons.append(f"{code}: yalnızca {chosen.supplier} teklif verdi.")

    rates = ", ".join(f"1 {c} = {tr_number(r)} TRY" for c, r in DEMO_FX_TRY.items() if c != "TRY")
    return PurchaseDraftData(
        request_no=request_no,
        lines=lines,
        total=sum((line.line_total_try for line in lines), Decimal(0)).quantize(
            CENT, ROUND_HALF_UP
        ),
        reasoning=" ".join(reasons),
        fx_note=f"Sabit demo kuru: {rates}. Gerçek kur değildir.",
    )
