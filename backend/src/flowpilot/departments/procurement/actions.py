"""Satın Alma öneri tipleri ve `apply` işlevleri (ADR-014, ADR-015).

`apply` yalnızca çekirdeğin tek yürütücüsü tarafından, onaydan sonra çağrılır. Yazdığı kayıt
yürütücünün `idempotency_key`'ini taşır: aynı öneri iki kez kayıt açamaz.
"""

import uuid
from typing import Any

from sqlalchemy import select

from flowpilot.core.registry import ApplyContext, ProposalType
from flowpilot.departments.procurement.comparison import PurchaseDraftData
from flowpilot.departments.procurement.models import PurchaseDraft, Quote, QuoteLine, Supplier
from flowpilot.departments.procurement.validation import QuoteData


def _supplier(ctx: ApplyContext, name: str) -> Supplier:
    supplier = ctx.session.scalars(select(Supplier).where(Supplier.name == name)).first()
    if supplier is None:
        supplier = Supplier(name=name)
        ctx.session.add(supplier)
        ctx.session.flush()
    return supplier


def apply_record_quote(ctx: ApplyContext, data: QuoteData) -> dict[str, Any]:
    quote = Quote(
        supplier=_supplier(ctx, data.supplier),
        quote_no=data.quote_no,
        request_no=data.request_no,
        currency=data.currency,
        valid_until=data.valid_until,
        subtotal=data.subtotal,
        vat=data.vat,
        total=data.total,
        issues=[i.model_dump() for i in data.issues],
        source_email_id=uuid.UUID(ctx.email_id),
        source_filename=data.source_filename,
        idempotency_key=ctx.idempotency_key,
    )
    for position, line in enumerate(data.lines):
        quote.lines.append(
            QuoteLine(
                position=position,
                product_code=line.product_code,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                line_total=line.line_total,
                lead_time_days=line.lead_time_days,
            )
        )
    ctx.session.add(quote)
    ctx.session.flush()
    return {"quote_id": str(quote.id), "supplier": data.supplier, "lines": len(data.lines)}


def apply_purchase_draft(ctx: ApplyContext, data: PurchaseDraftData) -> dict[str, Any]:
    draft = PurchaseDraft(
        request_no=data.request_no,
        currency=data.currency,
        total=data.total,
        lines=[line.model_dump(mode="json") for line in data.lines],
        reasoning=data.reasoning,
        source_email_id=uuid.UUID(ctx.email_id),
        idempotency_key=ctx.idempotency_key,
    )
    ctx.session.add(draft)
    ctx.session.flush()
    return {"purchase_draft_id": str(draft.id), "total_try": str(data.total)}


PROPOSAL_TYPES = (
    ProposalType(
        "record_quote",
        "Teklifi kaydet",
        QuoteData,
        apply_record_quote,
        description="Tedarikçi teklifini satırlarıyla kaydeder; işaretli alanlar da kaydedilir.",
    ),
    ProposalType(
        "purchase_draft",
        "Satın alma taslağı",
        PurchaseDraftData,
        apply_purchase_draft,
        description="Ürün başına seçilen tedarikçiyle taslak oluşturur. Dış sisteme gönderilmez.",
    ),
)
