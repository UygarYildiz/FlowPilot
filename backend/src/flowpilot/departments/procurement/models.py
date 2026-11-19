"""Satın Alma departmanının kendi tabloları (ADR-015). Çekirdek bunları bilmez.

Bu tablolara yalnızca öneri tiplerinin `apply` işlevleri yazar (onaydan sonra, tek yürütücü
üzerinden); ajanın araçları yalnızca okur.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flowpilot.core.db import Base

AMOUNT = Numeric(18, 4)


def _now() -> datetime:
    return datetime.now(UTC)


class Supplier(Base):
    __tablename__ = "procurement_supplier"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    email_domain: Mapped[str | None] = mapped_column(String(253))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Quote(Base):
    """Onaylanmış `record_quote` önerisiyle kaydedilen tedarikçi teklifi."""

    __tablename__ = "procurement_quote"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_supplier.id"))
    quote_no: Mapped[str | None] = mapped_column(String(64))
    request_no: Mapped[str | None] = mapped_column(String(64), index=True)
    currency: Mapped[str | None] = mapped_column(String(3))
    valid_until: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal | None] = mapped_column(AMOUNT)
    vat: Mapped[Decimal | None] = mapped_column(AMOUNT)
    total: Mapped[Decimal | None] = mapped_column(AMOUNT)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    source_email_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("email.id", ondelete="SET NULL")
    )
    source_filename: Mapped[str | None] = mapped_column(String(255))
    # Öneriyi uygulayan yürütücünün anahtarı: aynı öneri iki kez kayıt açamaz.
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    supplier: Mapped[Supplier] = relationship()
    lines: Mapped[list["QuoteLine"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan", order_by="QuoteLine.position"
    )


class QuoteLine(Base):
    __tablename__ = "procurement_quote_line"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("procurement_quote.id", ondelete="CASCADE")
    )
    position: Mapped[int]
    product_code: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
    quantity: Mapped[Decimal | None] = mapped_column(AMOUNT)
    unit: Mapped[str | None] = mapped_column(String(32))
    unit_price: Mapped[Decimal | None] = mapped_column(AMOUNT)
    line_total: Mapped[Decimal | None] = mapped_column(AMOUNT)
    lead_time_days: Mapped[int | None]
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    quote: Mapped[Quote] = relationship(back_populates="lines")

    __table_args__ = (Index("ix_procurement_quote_line_quote_id", "quote_id"),)


class PurchaseDraft(Base):
    """Onaylanmış `purchase_draft` önerisi: ürün başına seçilen tedarikçi. Dış sisteme gitmez."""

    __tablename__ = "procurement_purchase_draft"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_no: Mapped[str] = mapped_column(String(64), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    total: Mapped[Decimal] = mapped_column(AMOUNT)
    lines: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    source_email_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("email.id", ondelete="SET NULL")
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SupplierPrice(Base):
    """Onaylanmış `update_supplier_prices` önerisiyle kaydedilen tedarikçi fiyatı (ADR-016)."""

    __tablename__ = "procurement_supplier_price"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_supplier.id"))
    product_code: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str | None] = mapped_column(String(32))
    price: Mapped[Decimal] = mapped_column(AMOUNT)
    currency: Mapped[str] = mapped_column(String(3))
    valid_from: Mapped[date | None] = mapped_column(Date)
    source_email_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("email.id", ondelete="SET NULL")
    )
    idempotency_key: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    supplier: Mapped[Supplier] = relationship()

    __table_args__ = (
        Index("ix_procurement_supplier_price_lookup", "supplier_id", "product_code"),
        Index(
            "uq_procurement_supplier_price_key_code", "idempotency_key", "product_code", unique=True
        ),
    )


class ReplyDraft(Base):
    """Onaylanmış yanıt taslağı. Gönderilmez (v1); yalnızca kayıt ve panelde gösterim (ADR-016)."""

    __tablename__ = "procurement_reply_draft"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(32))
    to_addr: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16))
    source_email_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("email.id", ondelete="SET NULL")
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PurchaseRequest(Base):
    """Şirket içi satın alma talebi (ADR-016). Talep numarası `apply` sırasında verilir."""

    __tablename__ = "procurement_purchase_request"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_no: Mapped[str] = mapped_column(String(64), unique=True)
    requester: Mapped[str | None] = mapped_column(String(200))
    department: Mapped[str | None] = mapped_column(String(200))
    cost_center: Mapped[str | None] = mapped_column(String(64))
    needed_by: Mapped[date | None] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(Text, default="")
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    source_email_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("email.id", ondelete="SET NULL")
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
