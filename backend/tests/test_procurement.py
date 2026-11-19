"""Satın Alma ajanı (ADR-015): çıkarma doğrulaması, karşılaştırma, araçlar ve uçtan uca akış.

Model çağrısı yok: `FakeLLM` kayıtlı cevap döndürür; belge metinleri gerçek seed eklerinden okunur.
"""

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowpilot.bootstrap import DEPARTMENTS
from flowpilot.core.ingestion.extract import extract_text
from flowpilot.core.ingestion.service import ingest
from flowpilot.core.ingestion.types import IncomingAttachment, IncomingEmail
from flowpilot.core.models import (
    Decision,
    EmailStatus,
    Priority,
    ProposalStatus,
    Route,
    User,
    UserRole,
)
from flowpilot.core.proposals import approve, run_agent
from flowpilot.core.registry import DepartmentRegistry
from flowpilot.core.storage import MemoryStorage
from flowpilot.departments import procurement
from flowpilot.departments.procurement.comparison import compare
from flowpilot.departments.procurement.extraction import TASK, QuoteExtraction, build_prompt
from flowpilot.departments.procurement.models import PurchaseDraft, Quote
from flowpilot.departments.procurement.validation import numbers_in, validate
from flowpilot.llm.fake import FakeLLM

ATTACHMENTS = Path(__file__).resolve().parents[1] / "seed" / "atlas" / "attachments"
TODAY = date(2026, 11, 20)
OZKAN_FILE = "teklif-ozkan-rulman-TK-2611-07.pdf"
ANADOLU_FILE = "teklif-anadolu-rulman-AR-26-1184.xlsx"


def text_of(filename: str) -> str:
    result = extract_text(filename, "", (ATTACHMENTS / filename).read_bytes())
    assert result.text
    return result.text


OZKAN: dict[str, Any] = {
    "is_quote": True,
    "supplier": "Özkan Rulman San. ve Tic. Ltd. Şti.",
    "quote_no": "TK-2611-07",
    "request_no": "SAT-2026-031",
    "currency": "TRY",
    "valid_until": "2026-12-01",
    "lines": [
        {
            "product_code": "RLM-6205-2RS",
            "description": "Sabit bilyalı rulman 6205-2RS",
            "quantity": 400,
            "unit": "adet",
            "unit_price": 68.5,
            "line_total": 27400.0,
            "lead_time_days": 10,
        },
        {
            "product_code": "RLM-6308-ZZ",
            "description": "Sabit bilyalı rulman 6308-ZZ",
            "quantity": 150,
            "unit": "adet",
            "unit_price": 214.0,
            "line_total": 32100.0,
            "lead_time_days": 10,
        },
        {
            "product_code": "RLM-32210",
            "description": "Konik makaralı rulman 32210",
            "quantity": 60,
            "unit": "adet",
            "unit_price": 489.9,
            "line_total": 29394.0,
            "lead_time_days": 10,
        },
    ],
    "subtotal": 88894.0,
    "vat": 17778.8,
    "total": 106672.8,
}

ANADOLU: dict[str, Any] = {
    "is_quote": True,
    "supplier": "Anadolu Rulman A.Ş.",
    "quote_no": "AR-26-1184",
    "request_no": "SAT-2026-031",
    "currency": "EUR",
    "valid_until": "2026-11-28",
    "lines": [
        {
            "product_code": "RLM-6205-2RS",
            "description": "Sabit bilyalı rulman 6205-2RS",
            "quantity": 400,
            "unit": "adet",
            "unit_price": 1.62,
            "lead_time_days": 5,
        },
        {
            "product_code": "RLM-6308-ZZ",
            "description": "Sabit bilyalı rulman 6308-ZZ",
            "quantity": 150,
            "unit": "adet",
            "unit_price": 5.35,
            "lead_time_days": 5,
        },
        {
            "product_code": "RLM-32210",
            "description": "Konik makaralı rulman 32210",
            "quantity": 60,
            "unit": "adet",
            "unit_price": 11.8,
            "lead_time_days": 21,
        },
    ],
}


def checked(data: dict[str, Any], filename: str):  # noqa: ANN201
    return validate(
        QuoteExtraction.model_validate(data),
        text_of(filename),
        source_filename=filename,
        fallback_supplier="?",
        today=TODAY,
    )


# ---------- Kaynak ve aritmetik kontrolü ----------


def test_numbers_in_reads_turkish_and_english_formats() -> None:
    found = numbers_in("Toplam 27.400,00 TL · birim 1.62 EUR · 1,234.50 USD · 10 gün")
    assert {Decimal("27400"), Decimal("1.62"), Decimal("1234.5"), Decimal("10")} <= found


def test_correct_extraction_passes_without_errors() -> None:
    quote = checked(OZKAN, OZKAN_FILE)
    assert not quote.has_errors(), quote.issues
    assert quote.total == Decimal("106672.8") and quote.lines[0].unit_price == Decimal("68.5")
    assert not checked(ANADOLU, ANADOLU_FILE).has_errors()


def test_number_missing_from_the_document_is_flagged_not_trusted() -> None:
    data = {**OZKAN, "lines": [{**OZKAN["lines"][0], "unit_price": 66.0}, *OZKAN["lines"][1:]]}
    quote = checked(data, OZKAN_FILE)
    assert quote.flagged("lines[0].unit_price")
    messages = {i.message for i in quote.issues if i.field == "lines[0].unit_price"}
    assert "Bu sayı belgede geçmiyor." in messages


def test_number_taken_from_the_wrong_place_fails_arithmetic() -> None:
    # 214,00 belgede geçiyor ama ilk satırın fiyatı değil: aritmetik yakalar.
    data = {**OZKAN, "lines": [{**OZKAN["lines"][0], "unit_price": 214.0}, *OZKAN["lines"][1:]]}
    quote = checked(data, OZKAN_FILE)
    assert not any("geçmiyor" in i.message for i in quote.issues)
    assert quote.flagged("lines[0].unit_price") and quote.flagged("lines[0].line_total")


def test_missing_currency_and_bad_totals_are_flagged() -> None:
    quote = checked({**OZKAN, "currency": None, "total": 88894.0}, OZKAN_FILE)
    assert quote.flagged("currency") and quote.flagged("total")


def test_unknown_product_and_expired_quote_are_warnings() -> None:
    lines = [{**OZKAN["lines"][0], "product_code": "RLM-9999"}]
    quote = validate(
        QuoteExtraction.model_validate({**OZKAN, "lines": lines, "subtotal": None}),
        text_of(OZKAN_FILE) + " RLM-9999",
        source_filename=OZKAN_FILE,
        fallback_supplier="?",
        today=date(2026, 12, 5),
    )
    levels = {(i.field, i.level) for i in quote.issues}
    assert ("lines[0].product_code", "warning") in levels
    assert ("valid_until", "warning") in levels
    assert not quote.has_errors()


# ---------- Karşılaştırma ----------


def test_comparison_converts_currency_and_picks_cheapest_with_reasoning() -> None:
    draft = compare(
        "SAT-2026-031", [checked(OZKAN, OZKAN_FILE), checked(ANADOLU, ANADOLU_FILE)], today=TODAY
    )
    assert draft is not None
    chosen = {line.product_code: line.chosen for line in draft.lines}
    # 1,62 EUR × 37,50 = 60,75 TRY < 68,50 TRY
    assert chosen["RLM-6205-2RS"].supplier == "Anadolu Rulman A.Ş."
    assert chosen["RLM-6205-2RS"].unit_price_try == Decimal("60.75")
    # 11,80 EUR × 37,50 = 442,50 TRY < 489,90 TRY ama teslim 21 gün: gerekçede yazar.
    assert chosen["RLM-32210"].supplier == "Anadolu Rulman A.Ş."
    assert "teslim süresi daha uzun (21 gün" in draft.reasoning
    assert draft.total == Decimal("400") * Decimal("60.75") + Decimal("150") * Decimal(
        "200.63"
    ) + Decimal("60") * Decimal("442.50")
    assert "Gerçek kur değildir" in draft.fx_note


def test_single_supplier_or_flagged_lines_give_no_draft() -> None:
    assert compare("SAT-2026-031", [checked(OZKAN, OZKAN_FILE)], today=TODAY) is None
    no_currency = checked({**ANADOLU, "currency": None}, ANADOLU_FILE)
    assert compare("SAT-2026-031", [checked(OZKAN, OZKAN_FILE), no_currency], today=TODAY) is None


# ---------- Uçtan uca: ajan → öneri → onay → kayıt; ikinci e-postada araçla karşılaştırma ---


def _email(session: Session, filename: str, sender: str) -> Route:
    incoming = IncomingEmail(
        message_id=f"<{uuid.uuid4()}@x.example>",
        from_addr=sender,
        subject="SAT-2026-031 fiyat teklifimiz",
        body_text="Teklifimiz ektedir.",
        attachments=[
            IncomingAttachment(
                filename, "application/octet-stream", (ATTACHMENTS / filename).read_bytes()
            )
        ],
    )
    email = ingest(session, MemoryStorage(), incoming, source="test").email
    decision = Decision(email=email, model="m", prompt_version="v", needs_review=False, attempts=1)
    route = Route(
        position=0,
        department="procurement",
        intent="new_quote",
        priority=Priority.NORMAL,
        confidence=0.95,
    )
    decision.routes.append(route)
    session.add(decision)
    email.current_decision = decision
    email.status = EmailStatus.ROUTED
    session.flush()
    return route


@pytest.fixture
def llm() -> FakeLLM:
    fake = FakeLLM()
    for filename, sender, answer in [
        (OZKAN_FILE, "satis@ozkanrulman.example", OZKAN),
        (ANADOLU_FILE, "teklif@anadolurulman.example", ANADOLU),
    ]:
        prompt = build_prompt(
            sender=sender,
            subject="SAT-2026-031 fiyat teklifimiz",
            filename=filename,
            text=text_of(filename),
        )
        fake.add(TASK, prompt, answer)
    return fake


def test_agent_proposes_quotes_and_draft_after_first_quote_is_recorded(
    session: Session, llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> None:
    from flowpilot.departments.procurement import comparison, validation

    real_validate, real_compare = validation.validate, comparison.compare
    monkeypatch.setattr(
        "flowpilot.departments.procurement.agent.validate",
        lambda *a, **k: real_validate(*a, **{**k, "today": TODAY}),
    )
    monkeypatch.setattr(
        "flowpilot.departments.procurement.agent.compare",
        lambda *a, **k: real_compare(*a, **{**k, "today": TODAY}),
    )
    monkeypatch.setattr(
        "flowpilot.departments.procurement.tools.date",
        type("D", (), {"today": staticmethod(lambda: TODAY)}),
    )
    registry = DepartmentRegistry(
        procurement.with_agent(lambda: llm) if d.key == "procurement" else d for d in DEPARTMENTS
    )
    admin = User(
        email="y@atlas.example", name="Y", role=UserRole.ADMIN, departments=[], password_hash="-"
    )
    session.add(admin)

    # 1. e-posta: Özkan teklifi. Henüz başka teklif yok → yalnızca kaydet önerisi.
    run = run_agent(
        session, _email(session, OZKAN_FILE, "satis@ozkanrulman.example"), registry=registry
    )
    assert run is not None and run.status.value == "succeeded", run and run.error
    assert [p.type for p in run.proposals] == ["record_quote"]
    first = run.proposals[0]
    assert (
        first.summary
        == "Özkan Rulman San. ve Tic. Ltd. Şti. teklifini kaydet: 3 kalem, 106.672,80 TRY"
    )
    assert approve(session, first, user=admin, registry=registry).status is ProposalStatus.EXECUTED
    quote = session.scalars(select(Quote)).one()
    assert quote.total == Decimal("106672.8") and len(quote.lines) == 3

    # 2. e-posta: Anadolu teklifi. Araç kayıtlı Özkan teklifini bulur → taslak önerisi de gelir.
    run = run_agent(
        session, _email(session, ANADOLU_FILE, "teklif@anadolurulman.example"), registry=registry
    )
    assert run is not None and [p.type for p in run.proposals] == ["record_quote", "purchase_draft"]
    draft = run.proposals[1]
    assert draft.summary.startswith("SAT-2026-031 için satın alma taslağı: 3 kalem")
    assert approve(session, draft, user=admin, registry=registry).status is ProposalStatus.EXECUTED
    stored = session.scalars(select(PurchaseDraft)).one()
    assert stored.request_no == "SAT-2026-031" and stored.lines[0]["chosen"]["supplier"]
    # Araçlar hiçbir şey yazmadı: hâlâ tek teklif kayıtlı (Anadolu'nun kaydı onay bekliyor).
    assert session.scalar(select(func.count()).select_from(Quote)) == 1


def test_other_intents_produce_no_proposals_yet(session: Session, llm: FakeLLM) -> None:
    registry = DepartmentRegistry(
        procurement.with_agent(lambda: llm) if d.key == "procurement" else d for d in DEPARTMENTS
    )
    route = _email(session, OZKAN_FILE, "satis@ozkanrulman.example")
    route.intent = "supplier_complaint"
    run = run_agent(session, route, registry=registry)
    assert run is not None and run.status.value == "succeeded" and run.proposals == []
    assert llm.calls == []
