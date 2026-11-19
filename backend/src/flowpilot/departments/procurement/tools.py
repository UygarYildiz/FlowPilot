"""Satın Alma ajanının salt-okunur araçları (ADR-015). Düz veri döndürür, yazmaz."""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from flowpilot.core.registry import Tool
from flowpilot.departments.procurement.models import Quote


def open_quotes(
    session: Session, request_no: str, today: date | None = None
) -> list[dict[str, Any]]:
    """Talep numarasına kayıtlı, süresi dolmamış teklifler (`QuoteData` biçiminde)."""
    today = today or date.today()
    quotes = session.scalars(
        select(Quote)
        .where(Quote.request_no == request_no)
        .options(selectinload(Quote.lines), selectinload(Quote.supplier))
        .order_by(Quote.created_at)
    ).all()
    out = []
    for q in quotes:
        if q.valid_until is not None and q.valid_until < today:
            continue
        out.append(
            {
                "source_filename": q.source_filename or "",
                "supplier": q.supplier.name,
                "quote_no": q.quote_no,
                "request_no": q.request_no,
                "currency": q.currency,
                "valid_until": q.valid_until.isoformat() if q.valid_until else None,
                "subtotal": str(q.subtotal) if q.subtotal is not None else None,
                "vat": str(q.vat) if q.vat is not None else None,
                "total": str(q.total) if q.total is not None else None,
                "issues": q.issues,
                "lines": [
                    {
                        "product_code": line.product_code,
                        "description": line.description,
                        "quantity": str(line.quantity) if line.quantity is not None else None,
                        "unit": line.unit,
                        "unit_price": str(line.unit_price) if line.unit_price is not None else None,
                        "line_total": str(line.line_total) if line.line_total is not None else None,
                        "lead_time_days": line.lead_time_days,
                    }
                    for line in q.lines
                ],
            }
        )
    return out


def known_prices(
    session: Session, supplier: str, codes: list[str], currency: str | None
) -> dict[str, dict[str, Any]]:
    """Tedarikçinin ürün başına son kayıtlı fiyatı: önce fiyat listesi, yoksa son teklif satırı."""
    from flowpilot.departments.procurement.models import QuoteLine, Supplier, SupplierPrice

    found: dict[str, dict[str, Any]] = {}
    supplier_row = session.scalars(select(Supplier).where(Supplier.name == supplier)).first()
    if supplier_row is None:
        return found
    prices = session.scalars(
        select(SupplierPrice)
        .where(
            SupplierPrice.supplier_id == supplier_row.id,
            SupplierPrice.product_code.in_(codes),
        )
        .order_by(SupplierPrice.created_at.desc())
    ).all()
    for p in prices:
        if p.product_code not in found and (currency is None or p.currency == currency):
            when = f" ({p.valid_from:%d.%m.%Y})" if p.valid_from else ""
            found[p.product_code] = {
                "price": str(p.price),
                "currency": p.currency,
                "source": f"kayıtlı fiyat listesi{when}",
            }
    lines = session.execute(
        select(QuoteLine, Quote)
        .join(Quote, Quote.id == QuoteLine.quote_id)
        .where(Quote.supplier_id == supplier_row.id, QuoteLine.product_code.in_(codes))
        .order_by(Quote.created_at.desc())
    ).all()
    for line, quote in lines:
        code = line.product_code
        if (
            code
            and code not in found
            and line.unit_price is not None
            and (currency is None or quote.currency == currency)
        ):
            found[code] = {
                "price": str(line.unit_price),
                "currency": quote.currency,
                "source": f"teklif {quote.quote_no or ''}".strip(),
            }
    return found


def find_records(session: Session, references: list[str]) -> list[dict[str, Any]]:
    """E-postadaki referansları (talep no, teklif no) Satın Alma kayıtlarında arar."""
    from flowpilot.departments.procurement.models import PurchaseDraft, PurchaseRequest

    if not references:
        return []
    records: list[dict[str, Any]] = []
    for q in session.scalars(
        select(Quote)
        .where((Quote.request_no.in_(references)) | (Quote.quote_no.in_(references)))
        .options(selectinload(Quote.supplier))
    ):
        records.append(
            {
                "kayıt": "teklif",
                "tedarikçi": q.supplier.name,
                "teklif_no": q.quote_no,
                "talep_no": q.request_no,
                "geçerlilik": q.valid_until.isoformat() if q.valid_until else None,
                "kayıt_tarihi": q.created_at.date().isoformat(),
            }
        )
    for d in session.scalars(select(PurchaseDraft).where(PurchaseDraft.request_no.in_(references))):
        records.append(
            {
                "kayıt": "satın alma taslağı (onaylı, tedarikçiye gönderilmedi)",
                "talep_no": d.request_no,
                "kayıt_tarihi": d.created_at.date().isoformat(),
            }
        )
    for r in session.scalars(
        select(PurchaseRequest).where(PurchaseRequest.request_no.in_(references))
    ):
        records.append(
            {
                "kayıt": "iç satın alma talebi",
                "talep_no": r.request_no,
                "birim": r.department,
                "en_geç": r.needed_by.isoformat() if r.needed_by else None,
            }
        )
    return records


TOOLS = (
    Tool(
        "open_quotes",
        "Aynı talep numarasına kayıtlı, süresi dolmamış tedarikçi tekliflerini döndürür.",
        open_quotes,
    ),
    Tool(
        "known_prices",
        "Tedarikçinin ürün kodlarına göre son kayıtlı fiyatlarını döndürür.",
        known_prices,
    ),
    Tool(
        "find_records",
        "Talep/teklif numaralarını Satın Alma kayıtlarında arar.",
        find_records,
    ),
)
