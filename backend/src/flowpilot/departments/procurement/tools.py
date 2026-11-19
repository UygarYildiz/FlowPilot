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


TOOLS = (
    Tool(
        "open_quotes",
        "Aynı talep numarasına kayıtlı, süresi dolmamış tedarikçi tekliflerini döndürür.",
        open_quotes,
    ),
)
