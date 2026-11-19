"""Satın Alma öneri tipleri ve `apply` işlevleri (ADR-014, ADR-015).

`apply` yalnızca çekirdeğin tek yürütücüsü tarafından, onaydan sonra çağrılır. Yazdığı kayıt
yürütücünün `idempotency_key`'ini taşır: aynı öneri iki kez kayıt açamaz.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from flowpilot.core.registry import ApplyContext, ProposalType
from flowpilot.departments.procurement.comparison import PurchaseDraftData
from flowpilot.departments.procurement.internal_request import PurchaseRequestData
from flowpilot.departments.procurement.models import (
    PurchaseDraft,
    PurchaseRequest,
    Quote,
    QuoteLine,
    ReplyDraft,
    Supplier,
    SupplierPrice,
)
from flowpilot.departments.procurement.pricing import PriceUpdateData
from flowpilot.departments.procurement.replies import ReplyDraftData
from flowpilot.departments.procurement.validation import QuoteData

FIRST_REQUEST_NO = 101


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


def apply_supplier_prices(ctx: ApplyContext, data: PriceUpdateData) -> dict[str, Any]:
    if data.currency is None:
        raise ValueError("Para birimi olmadan fiyat kaydedilemez.")
    supplier = _supplier(ctx, data.supplier)
    for item in data.items:
        ctx.session.add(
            SupplierPrice(
                supplier=supplier,
                product_code=item.product_code,
                description=item.description,
                unit=item.unit,
                price=item.new_price,
                currency=data.currency,
                valid_from=data.valid_from,
                source_email_id=uuid.UUID(ctx.email_id),
                idempotency_key=ctx.idempotency_key,
            )
        )
    ctx.session.flush()
    return {"supplier": data.supplier, "prices": len(data.items)}


def apply_reply_draft(ctx: ApplyContext, data: ReplyDraftData) -> dict[str, Any]:
    """Yalnızca taslağı kaydeder; e-posta GÖNDERİLMEZ (v1, ADR-016)."""
    draft = ReplyDraft(
        kind=data.kind,
        to_addr=data.to,
        subject=data.subject,
        body=data.body,
        priority=data.priority,
        source_email_id=uuid.UUID(ctx.email_id),
        idempotency_key=ctx.idempotency_key,
    )
    ctx.session.add(draft)
    ctx.session.flush()
    return {"reply_draft_id": str(draft.id), "sent": False}


def _next_request_no(ctx: ApplyContext, year: int) -> str:
    prefix = f"SAT-{year}-"
    taken = ctx.session.scalars(
        select(PurchaseRequest.request_no).where(PurchaseRequest.request_no.like(f"{prefix}%"))
    ).all()
    numbers = [int(n.removeprefix(prefix)) for n in taken if n.removeprefix(prefix).isdigit()]
    return f"{prefix}{max([FIRST_REQUEST_NO - 1, *numbers]) + 1:03d}"


def apply_purchase_request(ctx: ApplyContext, data: PurchaseRequestData) -> dict[str, Any]:
    year = data.needed_by.year if data.needed_by else datetime.now(UTC).year
    request = PurchaseRequest(
        request_no=_next_request_no(ctx, year),
        requester=data.requester,
        department=data.department,
        cost_center=data.cost_center,
        needed_by=data.needed_by,
        reason=data.reason,
        items=[item.model_dump(mode="json") for item in data.items],
        issues=[i.model_dump() for i in data.issues],
        source_email_id=uuid.UUID(ctx.email_id),
        idempotency_key=ctx.idempotency_key,
    )
    ctx.session.add(request)
    ctx.session.flush()
    return {"request_no": request.request_no, "items": len(data.items)}


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
    ProposalType(
        "update_supplier_prices",
        "Tedarikçi fiyatlarını güncelle",
        PriceUpdateData,
        apply_supplier_prices,
        description="Fiyat listesindeki yeni fiyatları kaydeder.",
    ),
    ProposalType(
        "reply_draft",
        "Yanıt taslağı",
        ReplyDraftData,
        apply_reply_draft,
        description="Yanıt taslağını kaydeder. E-posta gönderilmez.",
    ),
    ProposalType(
        "create_purchase_request",
        "Satın alma talebi oluştur",
        PurchaseRequestData,
        apply_purchase_request,
        description="İç talebi kaydeder ve talep numarası verir.",
    ),
)
