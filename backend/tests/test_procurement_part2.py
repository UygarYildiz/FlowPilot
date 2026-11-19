"""Satın Alma ajanı 2. parça (ADR-016): fiyat güncellemesi, yanıt taslakları, iç talep.

Model çağrısı yok (`FakeLLM`); e-postalar ve ekler kurgusal şirketin seed verisinden.
"""

import json
import uuid
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
    AgentRun,
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
from flowpilot.departments.procurement import internal_request, pricing, replies
from flowpilot.departments.procurement.models import (
    PurchaseRequest,
    ReplyDraft,
    SupplierPrice,
)
from flowpilot.llm.fake import FakeLLM

SEED = Path(__file__).resolve().parents[1] / "seed" / "atlas"
EMAILS = {e["id"]: e for e in json.loads((SEED / "emails.json").read_text("utf-8"))["emails"]}
PRICE_FILE = "fiyat-listesi-kaya-hidrolik-2026-12.csv"


def make_email(session: Session, seed_id: str, intent: str, *, body: str | None = None) -> Route:
    seed = EMAILS[seed_id]
    attachments = [
        IncomingAttachment(name, "text/csv", (SEED / "attachments" / name).read_bytes())
        for name in seed.get("attachments") or []
    ]
    incoming = IncomingEmail(
        message_id=f"<{uuid.uuid4()}@x.example>",
        from_addr=seed["from"],
        to_addrs=seed.get("to") or [],
        subject=seed["subject"],
        body_text=body if body is not None else seed["body"],
        attachments=attachments,
    )
    email = ingest(session, MemoryStorage(), incoming, source="test").email
    decision = Decision(email=email, model="m", prompt_version="v", needs_review=False, attempts=1)
    route = Route(
        position=0,
        department="procurement",
        intent=intent,
        priority=Priority.NORMAL,
        confidence=0.9,
    )
    decision.routes.append(route)
    session.add(decision)
    email.current_decision = decision
    email.status = EmailStatus.ROUTED
    session.flush()
    return route


def registry_with(llm: FakeLLM) -> DepartmentRegistry:
    return DepartmentRegistry(
        procurement.with_agent(lambda: llm) if d.key == "procurement" else d for d in DEPARTMENTS
    )


def admin(session: Session) -> User:
    user = User(
        email=f"{uuid.uuid4().hex[:6]}@atlas.example",
        name="Y",
        role=UserRole.ADMIN,
        departments=[],
        password_hash="-",
    )
    session.add(user)
    session.flush()
    return user


def ran(session: Session, route: Route, registry: DepartmentRegistry) -> AgentRun:
    run = run_agent(session, route, registry=registry)
    assert run is not None and run.status.value == "succeeded", run and run.error
    return run


# ---------- Fiyat güncellemesi ----------

KAYA: dict[str, Any] = {
    "is_price_list": True,
    "supplier": "Kaya Hidrolik",
    "currency": "TRY",
    "valid_from": "2026-12-01",
    "items": [
        {
            "product_code": "HYD-PMP-045",
            "description": "Dişli pompa 45 cc",
            "old_price": 7850.0,
            "new_price": 8420.0,
        },
        {
            "product_code": "HYD-VLF-12",
            "description": 'Yön kontrol valfi 1/2"',
            "old_price": 2310.0,
            "new_price": 2310.0,
        },
        {
            "product_code": "HYD-HRT-08",
            "description": "Hidrolik hortum 8 mm",
            "unit": "m",
            "old_price": 96.0,
            "new_price": 104.5,
        },
        {
            "product_code": "HYD-FLT-10",
            "description": "Dönüş filtresi 10 mikron",
            "old_price": 640.0,
            "new_price": 702.0,
        },
    ],
}


def add_price_answer(llm: FakeLLM, answer: dict[str, Any]) -> None:
    seed = EMAILS["seed-003"]
    text = extract_text(PRICE_FILE, "", (SEED / "attachments" / PRICE_FILE).read_bytes()).text
    prompt = pricing.build_prompt(
        sender=seed["from"],
        subject=seed["subject"],
        body=seed["body"],
        filename=PRICE_FILE,
        text=text or "",
    )
    llm.add(pricing.TASK, prompt, answer)


def test_price_update_uses_document_old_price_then_recorded_prices(session: Session) -> None:
    llm = FakeLLM()
    add_price_answer(llm, KAYA)
    registry = registry_with(llm)

    run = ran(session, make_email(session, "seed-003", "price_update"), registry)
    proposal = run.proposals[0]
    assert proposal.type == "update_supplier_prices"
    assert proposal.summary == (
        "Kaya Hidrolik fiyatlarını güncelle — 4 ürün: 3 zam (ort. %8,6), 1 değişmedi, "
        "01.12.2026 itibarıyla"
    )
    items = {i["product_code"]: i for i in proposal.payload["items"]}
    assert items["HYD-PMP-045"]["previous_source"] == "belgedeki eski fiyat"
    assert Decimal(items["HYD-PMP-045"]["change_pct"]) == Decimal("7.3")
    assert not [i for i in proposal.payload["issues"] if i["level"] == "error"]

    assert approve(session, proposal, user=admin(session), registry=registry).status is (
        ProposalStatus.EXECUTED
    )
    assert session.scalar(select(func.count()).select_from(SupplierPrice)) == 4

    # Aynı tedarikçiden ikinci liste: önceki fiyat artık kayıtlardan gelir.
    run = ran(session, make_email(session, "seed-003", "price_update"), registry)
    items = {i["product_code"]: i for i in run.proposals[0].payload["items"]}
    assert items["HYD-PMP-045"]["previous_source"] == "kayıtlı fiyat listesi (01.12.2026)"
    assert Decimal(items["HYD-PMP-045"]["previous_price"]) == Decimal("8420")


def test_price_not_in_document_is_flagged(session: Session) -> None:
    llm = FakeLLM()
    wrong = json.loads(json.dumps(KAYA))
    wrong["items"][0]["new_price"] = 8240.0  # belgede 8.420,00
    add_price_answer(llm, wrong)
    run = ran(session, make_email(session, "seed-003", "price_update"), registry_with(llm))
    errors = [i for i in run.proposals[0].payload["issues"] if i["level"] == "error"]
    assert errors == [
        {"field": "items[0].new_price", "level": "error", "message": "Bu sayı belgede geçmiyor."}
    ]


# ---------- Yanıt taslakları ----------


def reply_answer(body: str, priority: str = "normal") -> dict[str, Any]:
    return {
        "summary": "Tedarikçi PO-2026-0902 siparişinin imzalı formunu bekliyor.",
        "priority": priority,
        "priority_reason": "Tedarikçinin üretim planı buna bağlı.",
        "reply_subject": "RE: PO-2026-0902 sipariş onayınız hk.",
        "reply_body": body,
    }


def add_reply_answer(
    llm: FakeLLM, seed_id: str, kind: str, records: list[dict[str, Any]], answer: dict[str, Any]
) -> None:
    seed = EMAILS[seed_id]
    prompt = replies.build_prompt(
        kind=kind, sender=seed["from"], subject=seed["subject"], body=seed["body"], records=records
    )
    llm.add(replies.TASK, prompt, answer)


def test_order_status_reply_without_record_and_invented_number_warning(session: Session) -> None:
    llm = FakeLLM()
    body = (
        "Merhaba Burak Bey,\nPO-2026-0902 siparişinin kaydını kontrol edip size dönüş yapacağız. "
        "İmzalı formu 3 iş günü içinde iletmeyi hedefliyoruz.\nAtlas Endüstri Satın Alma"
    )
    add_reply_answer(llm, "seed-004", "order_status_inquiry", [], reply_answer(body))
    registry = registry_with(llm)

    run = ran(session, make_email(session, "seed-004", "order_status_inquiry"), registry)
    proposal = run.proposals[0]
    assert proposal.summary == ("Yanıt taslağı (sipariş durumu, öncelik: normal; kayıt bulunamadı)")
    payload = proposal.payload
    assert payload["references"] == ["PO-2026-0902"] and payload["records"] == []
    assert payload["to"] == "siparis@demirtascelik.example"
    # "3 iş günü" e-postada da kayıtlarda da yok: uyarı.
    assert [i["message"] for i in payload["issues"]] == [
        "Taslaktaki 3 sayısı e-postada ve kayıtlarda geçmiyor; kontrol et."
    ]
    done = approve(session, proposal, user=admin(session), registry=registry)
    assert done.status is ProposalStatus.EXECUTED and done.result is not None
    assert done.result["sent"] is False
    assert session.scalars(select(ReplyDraft)).one().body == body


def test_complaint_reply_finds_recorded_quote_by_reference(session: Session) -> None:
    from flowpilot.departments.procurement.models import Quote, Supplier

    supplier = Supplier(name="Özkan Rulman")
    session.add(supplier)
    session.add(
        Quote(
            supplier=supplier,
            quote_no="TK-2611-07",
            request_no="SAT-2026-031",
            currency="TRY",
            issues=[],
            idempotency_key=uuid.uuid4().hex,
        )
    )
    session.flush()
    body = EMAILS["seed-005"]["body"] + "\nİlgili talep: SAT-2026-031"
    route = make_email(session, "seed-005", "supplier_complaint", body=body)
    records = replies.references_in(EMAILS["seed-005"]["subject"], body)
    assert records == ["PO-2026-0877", "SAT-2026-031"]

    llm = FakeLLM()
    seed = EMAILS["seed-005"]
    found = [
        {
            "kayıt": "teklif",
            "tedarikçi": "Özkan Rulman",
            "teklif_no": "TK-2611-07",
            "talep_no": "SAT-2026-031",
            "geçerlilik": None,
            "kayıt_tarihi": session.scalars(select(Quote)).one().created_at.date().isoformat(),
        }
    ]
    prompt = replies.build_prompt(
        kind="supplier_complaint",
        sender=seed["from"],
        subject=seed["subject"],
        body=body,
        records=found,
    )
    llm.add(
        replies.TASK,
        prompt,
        reply_answer("Konuyu ciddiye alıyoruz; uygun toplantı zamanlarını ileteceğiz.", "high"),
    )
    run = ran(session, route, registry_with(llm))
    proposal = run.proposals[0]
    assert proposal.summary == "Yanıt taslağı (tedarikçi şikâyeti, öncelik: yüksek; kayıt bulundu)"
    assert proposal.payload["records"] == found and proposal.payload["issues"] == []


# ---------- İç satın alma talebi ----------

HAT3: dict[str, Any] = {
    "requester": "Ece Yılmaz",
    "department": "Üretim Planlama",
    "cost_center": "ÜRT-03",
    "needed_by": "2026-11-24",
    "reason": "Hat 3'ün 25 Kasım'daki bakım duruşu",
    "items": [
        {
            "product_code": "HYD-PMP-045",
            "description": "dişli pompa 45 cc",
            "quantity": 2,
            "unit": "adet",
        },
        {
            "product_code": "HYD-FLT-10",
            "description": "dönüş filtresi",
            "quantity": 12,
            "unit": "adet",
        },
        {"product_code": "RLM-6205-2RS", "description": "rulman", "quantity": 40, "unit": "adet"},
    ],
}


def add_request_answer(llm: FakeLLM, route: Route, answer: dict[str, Any]) -> None:
    email = route.decision.email
    prompt = internal_request.build_prompt(
        sender=email.from_addr,
        subject=email.subject,
        body=email.body_text,
        received=email.received_at.isoformat()[:10],
    )
    llm.add(internal_request.TASK, prompt, answer)


def test_purchase_request_gets_numbered_on_approval(session: Session) -> None:
    llm = FakeLLM()
    registry = registry_with(llm)
    user = admin(session)
    numbers = []
    for _ in range(2):
        route = make_email(session, "seed-006", "purchase_request")
        add_request_answer(llm, route, HAT3)
        proposal = ran(session, route, registry).proposals[0]
        assert proposal.summary == (
            "Satın alma talebi oluştur: 3 kalem (Üretim Planlama, en geç 24.11.2026)"
        )
        assert [i["level"] for i in proposal.payload["issues"]] in ([], ["warning"])
        done = approve(session, proposal, user=user, registry=registry)
        assert done.result is not None
        numbers.append(done.result["request_no"])
    assert numbers == ["SAT-2026-101", "SAT-2026-102"]
    stored = session.scalars(select(PurchaseRequest).order_by(PurchaseRequest.request_no)).first()
    assert stored is not None and stored.cost_center == "ÜRT-03" and len(stored.items) == 3


def test_request_quantity_not_in_email_is_flagged(session: Session) -> None:
    llm = FakeLLM()
    route = make_email(session, "seed-006", "purchase_request")
    wrong = json.loads(json.dumps(HAT3))
    wrong["items"][1]["quantity"] = 15
    add_request_answer(llm, route, wrong)
    payload = ran(session, route, registry_with(llm)).proposals[0].payload
    assert {
        "field": "items[1].quantity",
        "level": "error",
        "message": "Bu sayı e-postada geçmiyor.",
    } in (payload["issues"])


@pytest.mark.parametrize("intent", [None, "unknown"])
def test_unhandled_intent_makes_no_model_call(session: Session, intent: str | None) -> None:
    llm = FakeLLM()
    route = make_email(session, "seed-004", "order_status_inquiry")
    route.intent = intent
    run = ran(session, route, registry_with(llm))
    assert run.proposals == [] and llm.calls == []
