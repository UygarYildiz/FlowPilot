"""Satın Alma ajanı (v1 kapsamı 3.6; ADR-015). 1. parça: `new_quote`.

Akış: ekteki (yoksa gövdedeki) her belge için çıkar → doğrula → `record_quote` önerisi. Aynı talebe
kayıtlı ya da aynı e-postada gelen başka tedarikçi teklifleri varsa → `purchase_draft` önerisi.
Diğer intent'ler 2. parçada; şimdilik öneri üretmez.
"""

from collections.abc import Callable
from decimal import Decimal

from flowpilot.core.registry import AgentContext, ProposalDraft
from flowpilot.departments.procurement.comparison import compare
from flowpilot.departments.procurement.extraction import extract_quote
from flowpilot.departments.procurement.validation import QuoteData, validate
from flowpilot.llm import LLMClient

HANDLED_INTENTS = {"new_quote"}


def money(value: Decimal | None, currency: str | None) -> str:
    if value is None:
        return "tutar yok"
    text = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} {currency or ''}".strip()


def _quote_total(quote: QuoteData) -> Decimal | None:
    if quote.total is not None:
        return quote.total
    if quote.subtotal is not None:
        return quote.subtotal
    if quote.lines and all(
        line.line_total is not None or (line.quantity is not None and line.unit_price is not None)
        for line in quote.lines
    ):
        return sum(
            (
                line.line_total
                if line.line_total is not None
                else (line.quantity or Decimal(0)) * (line.unit_price or Decimal(0))
                for line in quote.lines
            ),
            Decimal(0),
        )
    return None


def quote_summary(quote: QuoteData) -> str:
    errors = sum(1 for i in quote.issues if i.level == "error")
    warnings = sum(1 for i in quote.issues if i.level == "warning")
    flags = []
    if errors:
        flags.append(f"{errors} şüpheli alan")
    if warnings:
        flags.append(f"{warnings} uyarı")
    tail = f" — {', '.join(flags)}" if flags else ""
    return (
        f"{quote.supplier} teklifini kaydet: {len(quote.lines)} kalem, "
        f"{money(_quote_total(quote), quote.currency)}{tail}"
    )


class ProcurementAgent:
    def __init__(self, llm_factory: Callable[[], LLMClient]) -> None:
        self._llm_factory = llm_factory
        self._llm: LLMClient | None = None

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = self._llm_factory()
        return self._llm

    def handle(self, context: AgentContext) -> list[ProposalDraft]:
        if context.intent not in HANDLED_INTENTS:
            return []
        sender_domain = context.from_addr.rsplit("@", 1)[-1]
        sources = [(a.filename, a.text) for a in context.attachments if a.text and a.text.strip()]
        if not sources and context.body_text.strip():
            sources = [("e-posta gövdesi", context.body_text)]

        drafts: list[ProposalDraft] = []
        quotes: list[QuoteData] = []
        for filename, text in sources:
            assert text is not None
            extraction = extract_quote(
                self.llm,
                sender=context.from_addr,
                subject=context.subject,
                filename=filename,
                text=text,
            )
            if not extraction.is_quote:
                continue
            quote = validate(
                extraction,
                text,
                source_filename=filename,
                fallback_supplier=f"Bilinmeyen tedarikçi ({sender_domain})",
            )
            quotes.append(quote)
            drafts.append(
                ProposalDraft("record_quote", quote.model_dump(mode="json"), quote_summary(quote))
            )

        for request_no in sorted({q.request_no for q in quotes if q.request_no}):
            current = [q for q in quotes if q.request_no == request_no]
            known = {(q.supplier, q.quote_no) for q in current}
            recorded = [
                QuoteData.model_validate(item)
                for item in context.tools.call("open_quotes", request_no=request_no)
            ]
            others = [q for q in recorded if (q.supplier, q.quote_no) not in known]
            draft = compare(request_no, current + others)
            if draft is not None:
                suppliers = sorted({line.chosen.supplier for line in draft.lines})
                drafts.append(
                    ProposalDraft(
                        "purchase_draft",
                        draft.model_dump(mode="json"),
                        f"{request_no} için satın alma taslağı: {len(draft.lines)} kalem, "
                        f"{money(draft.total, 'TRY')} ({', '.join(suppliers)})",
                    )
                )
        return drafts
