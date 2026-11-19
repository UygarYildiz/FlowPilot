from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot.api.deps import get_db, get_storage
from flowpilot.core.ingestion.service import ingest
from flowpilot.core.ingestion.types import IncomingAttachment, IncomingEmail
from flowpilot.core.models import (
    Correction,
    Decision,
    Email,
    EmailStatus,
    Priority,
    Route,
)
from flowpilot.core.storage import MemoryStorage
from flowpilot.core.users import DEMO_DOMAIN, ensure_demo_users
from flowpilot.main import create_app

PASSWORD = "test-sifresi"
ADMIN = f"yonetici@{DEMO_DOMAIN}"
PROCUREMENT = f"satinalma@{DEMO_DOMAIN}"


def _email(
    session: Session,
    storage: MemoryStorage,
    key: str,
    routes: list[tuple[str, str | None, float]],
    *,
    needs_review: bool = False,
    attachment: bytes | None = None,
) -> Email:
    incoming = IncomingEmail(
        message_id=f"<{key}@x.example>",
        from_addr=f"{key}@tedarikci.example",
        subject=f"Konu {key}",
        body_text=f"Gövde {key}",
        attachments=[IncomingAttachment("liste.csv", "text/csv", attachment)] if attachment else [],
    )
    email = ingest(session, storage, incoming, source="test").email
    decision = Decision(
        email=email,
        model="test",
        prompt_version="t",
        reasoning="gerekçe",
        needs_review=needs_review,
        review_reason="düşük güven" if needs_review else None,
        attempts=1,
    )
    for position, (department, intent, confidence) in enumerate(routes):
        decision.routes.append(
            Route(
                position=position,
                department=department,
                intent=intent,
                priority=Priority.NORMAL,
                confidence=confidence,
            )
        )
    session.add(decision)
    email.current_decision = decision
    email.status = EmailStatus.NEEDS_REVIEW if needs_review else EmailStatus.ROUTED
    session.flush()
    return email


@pytest.fixture
def data(session: Session) -> dict[str, Email]:
    storage = MemoryStorage()
    ensure_demo_users(session, PASSWORD)
    return {
        "quote": _email(
            session,
            storage,
            "quote",
            [("procurement", "new_quote", 0.95)],
            attachment=b"Kod;Fiyat\n",
        ),
        "invoice": _email(session, storage, "invoice", [("finance", "invoice_received", 0.9)]),
        "multi": _email(
            session,
            storage,
            "multi",
            [("logistics", "delivery_issue", 0.9), ("procurement", "supplier_complaint", 0.8)],
        ),
        "unclear": _email(
            session, storage, "unclear", [("procurement", "new_quote", 0.4)], needs_review=True
        ),
        "_storage": storage,  # type: ignore[dict-item]
    }


@pytest.fixture
def client(session: Session, data: dict[str, Email]) -> Iterator[TestClient]:
    app = create_app()

    def db() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_db] = db
    app.dependency_overrides[get_storage] = lambda: data["_storage"]
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text


def test_login_flow(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401
    bad = client.post("/api/auth/login", json={"email": ADMIN, "password": "yanlis"})
    assert bad.status_code == 401
    login(client, ADMIN.upper())
    assert client.get("/api/auth/me").json()["role"] == "admin"
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_admin_sees_everything_and_counts(client: TestClient) -> None:
    login(client, ADMIN)
    assert client.get("/api/emails").json()["total"] == 4
    review = client.get("/api/emails", params={"view": "review"}).json()
    assert [e["subject"] for e in review["items"]] == ["Konu unclear"]
    counts = client.get("/api/counts").json()
    assert counts["all"] == 4 and counts["needs_review"] == 1
    open_counts = {d["key"]: d["open_count"] for d in counts["departments"]}
    assert open_counts == {"procurement": 2, "finance": 1, "sales_orders": 0, "logistics": 1}


def test_department_user_sees_only_own_routed_emails(
    client: TestClient, data: dict[str, Email]
) -> None:
    login(client, PROCUREMENT)
    subjects = {e["subject"] for e in client.get("/api/emails").json()["items"]}
    assert subjects == {"Konu quote", "Konu multi"}
    assert client.get("/api/emails", params={"view": "review"}).status_code == 403
    assert client.get(f"/api/emails/{data['invoice'].id}").status_code == 404
    assert client.get(f"/api/emails/{data['unclear'].id}").status_code == 404
    assert (
        client.get(
            "/api/emails", params={"view": "department", "department": "finance"}
        ).status_code
        == 404
    )
    assert [d["key"] for d in client.get("/api/counts").json()["departments"]] == ["procurement"]


def test_department_inbox_and_search(client: TestClient) -> None:
    login(client, ADMIN)
    inbox = client.get("/api/emails", params={"view": "department", "department": "logistics"})
    assert [e["subject"] for e in inbox.json()["items"]] == ["Konu multi"]
    found = client.get("/api/emails", params={"q": "invoice"}).json()
    assert [e["subject"] for e in found["items"]] == ["Konu invoice"]


def test_correction_creates_manual_decision(
    client: TestClient, data: dict[str, Email], session: Session
) -> None:
    login(client, ADMIN)
    email_id = data["unclear"].id
    response = client.post(
        f"/api/emails/{email_id}/correction",
        json={
            "routes": [{"department": "finance", "intent": "invoice_received", "priority": "high"}],
            "reason": "Aslında fatura",
        },
    )
    assert response.status_code == 200, response.text
    detail = response.json()
    assert detail["status"] == "routed"
    assert detail["current_decision"]["model"] == "manual"
    assert detail["current_decision"]["routes"][0]["origin"] == "manual"
    assert detail["previous_decisions"][0]["routes"][0]["intent"] == "new_quote"
    assert [e["action"] for e in detail["events"]][-1] == "email.rerouted"
    correction = session.scalars(select(Correction)).one()
    assert correction.user_email == ADMIN and correction.reason == "Aslında fatura"


def test_correction_validation(client: TestClient, data: dict[str, Email]) -> None:
    login(client, ADMIN)
    url = f"/api/emails/{data['unclear'].id}/correction"
    wrong_intent = client.post(
        url,
        json={"routes": [{"department": "finance", "intent": "new_quote"}], "reason": "x"},
    )
    assert wrong_intent.status_code == 422
    assert "geçersiz" in wrong_intent.json()["detail"]
    no_reason = client.post(
        url,
        json={"routes": [{"department": "finance", "intent": "invoice_received"}], "reason": " "},
    )
    assert no_reason.status_code == 422


def test_route_done_closes_email_when_all_routes_done(
    client: TestClient, data: dict[str, Email]
) -> None:
    login(client, PROCUREMENT)
    multi = client.get(f"/api/emails/{data['multi'].id}").json()
    routes = {r["department"]: r["id"] for r in multi["current_decision"]["routes"]}

    assert client.post(f"/api/routes/{routes['logistics']}/done", json={}).status_code == 404
    after = client.post(f"/api/routes/{routes['procurement']}/done", json={}).json()
    statuses = {r["department"]: r["status"] for r in after["current_decision"]["routes"]}
    assert statuses == {"logistics": "open", "procurement": "done"}
    assert after["status"] == "routed"

    quote = client.get(f"/api/emails/{data['quote'].id}").json()
    route_id = quote["current_decision"]["routes"][0]["id"]
    closed = client.post(f"/api/routes/{route_id}/done", json={"reason": "teklif sisteme girildi"})
    assert closed.json()["status"] == "done"
    assert closed.json()["current_decision"]["routes"][0]["done_by"] == PROCUREMENT


def test_dismiss_is_admin_only(client: TestClient, data: dict[str, Email]) -> None:
    login(client, PROCUREMENT)
    assert (
        client.post(f"/api/emails/{data['quote'].id}/dismiss", json={"reason": "x"}).status_code
        == 403
    )
    login(client, ADMIN)
    dismissed = client.post(f"/api/emails/{data['unclear'].id}/dismiss", json={"reason": "reklam"})
    assert dismissed.json()["status"] == "done"


def test_attachment_download(client: TestClient, data: dict[str, Email]) -> None:
    login(client, PROCUREMENT)
    detail = client.get(f"/api/emails/{data['quote'].id}").json()
    attachment = detail["attachments"][0]
    assert attachment["parse_status"] == "ok" and attachment["text_preview"] == "Kod\tFiyat"
    response = client.get(f"/api/emails/{data['quote'].id}/attachments/{attachment['id']}")
    assert response.status_code == 200
    assert response.content == b"Kod;Fiyat\n"
    assert "liste.csv" in response.headers["content-disposition"]
