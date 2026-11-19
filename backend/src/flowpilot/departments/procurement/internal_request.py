"""Şirket içi satın alma talebi (`purchase_request` → `create_purchase_request`; ADR-016)."""

from datetime import date

from pydantic import BaseModel, Field

from flowpilot.departments.procurement.catalog import PRODUCTS
from flowpilot.departments.procurement.validation import Issue, numbers_in, parse_date, to_decimal
from flowpilot.llm import LLMClient

TASK = "procurement.extract_purchase_request"
SYSTEM = """Sen Atlas Endüstri A.Ş.'nin satın alma biriminde çalışan dikkatli bir asistansın. Şirket
içinden gelen bir malzeme/hizmet talebi e-postasını okuyup talebi şemaya aktaracaksın.

Kurallar:
- Yalnızca e-postada yazanı yaz; olmayan alanı null bırak. Miktar ya da kod uydurma.
- Her kalem için ürün kodu (yazıyorsa), açıklama, miktar ve birim.
- needed_by: malzemenin en geç ne zaman gerektiği (YYYY-AA-GG). Yıl yazmıyorsa e-postanın
  tarihine göre en yakın gelecekteki yılı kullan.
- requester: talep eden kişi; department: birimi; cost_center: masraf merkezi kodu.
"""


class ExtractedItem(BaseModel):
    product_code: str | None = None
    description: str | None = None
    quantity: float | None = None
    unit: str | None = None


class RequestExtraction(BaseModel):
    requester: str | None = None
    department: str | None = None
    cost_center: str | None = None
    needed_by: str | None = None
    reason: str | None = None
    items: list[ExtractedItem] = Field(default_factory=list)


class RequestItem(BaseModel):
    product_code: str | None = None
    description: str = ""
    quantity: float | None = None
    unit: str | None = None


class PurchaseRequestData(BaseModel):
    """`create_purchase_request` önerisinin verisi. Talep numarası onaydan sonra verilir."""

    requester: str | None = None
    department: str | None = None
    cost_center: str | None = None
    needed_by: date | None = None
    reason: str = ""
    items: list[RequestItem] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)


def build_prompt(*, sender: str, subject: str, body: str, received: str) -> str:
    return (
        f"Gönderen: {sender}\nKonu: {subject}\nE-posta tarihi: {received}\n\n"
        f"--- E-POSTA ---\n{body[:8000]}\n--- SON ---"
    )


def extract_request(llm: LLMClient, **kwargs: str) -> RequestExtraction:
    return llm.generate(
        task=TASK, system=SYSTEM, prompt=build_prompt(**kwargs), schema=RequestExtraction
    )


def build_request(
    extraction: RequestExtraction, source_text: str, *, today: date | None = None
) -> PurchaseRequestData:
    today = today or date.today()
    issues: list[Issue] = []
    seen = numbers_in(source_text)
    items: list[RequestItem] = []
    for index, raw in enumerate(extraction.items):
        prefix = f"items[{index}]"
        qty = to_decimal(raw.quantity)
        code = (raw.product_code or "").strip() or None
        if qty is None:
            issues.append(Issue(field=f"{prefix}.quantity", level="error", message="Miktar yok."))
        elif qty not in seen:
            issues.append(
                Issue(
                    field=f"{prefix}.quantity", level="error", message="Bu sayı e-postada geçmiyor."
                )
            )
        elif qty <= 0:
            issues.append(
                Issue(
                    field=f"{prefix}.quantity",
                    level="error",
                    message="Miktar sıfırdan büyük değil.",
                )
            )
        if code is None:
            issues.append(
                Issue(field=f"{prefix}.product_code", level="warning", message="Ürün kodu yok.")
            )
        elif code not in PRODUCTS:
            issues.append(
                Issue(field=f"{prefix}.product_code", level="warning", message="Kod katalogda yok.")
            )
        items.append(
            RequestItem(
                product_code=code,
                description=(raw.description or "").strip() or PRODUCTS.get(code or "", ""),
                quantity=raw.quantity,
                unit=raw.unit,
            )
        )
    needed_by = parse_date(extraction.needed_by)
    if extraction.needed_by and needed_by is None:
        issues.append(Issue(field="needed_by", level="warning", message="Tarih okunamadı."))
    elif needed_by is not None and needed_by < today:
        issues.append(Issue(field="needed_by", level="warning", message="İstenen tarih geçmiş."))
    if not items:
        issues.append(Issue(field="items", level="error", message="Talep kalemi bulunamadı."))
    return PurchaseRequestData(
        requester=extraction.requester,
        department=extraction.department,
        cost_center=extraction.cost_center,
        needed_by=needed_by,
        reason=(extraction.reason or "").strip(),
        items=items,
        issues=issues,
    )


def summary(data: PurchaseRequestData) -> str:
    who = data.department or data.requester or "iç birim"
    when = f", en geç {data.needed_by:%d.%m.%Y}" if data.needed_by else ""
    return f"Satın alma talebi oluştur: {len(data.items)} kalem ({who}{when})"
