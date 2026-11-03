"""Console endpoints: list, detail, take, close (in-memory persistence)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from core.api import app, get_case_store, get_session_store
from core.cases import InMemoryCaseStore
from core.sessions import InMemorySessionStore


@pytest.fixture
def cases() -> InMemoryCaseStore:
    return InMemoryCaseStore()


@pytest.fixture
def client(cases: InMemoryCaseStore):
    sessions = InMemorySessionStore()
    app.dependency_overrides[get_session_store] = lambda: sessions
    app.dependency_overrides[get_case_store] = lambda: cases
    yield TestClient(app)
    app.dependency_overrides.clear()


def escalate(client, sid: str, flow: str, labels: list[str]) -> int:
    def turn(label, **kw):
        return client.post("/next-step", json={"session_id": sid, "phone": "+573001112233", "label": label, **kw})

    turn("start", flow=flow)
    for label in labels:
        turn(label)
    r = client.post("/cases", json={"session_id": sid, "transcript": [{"speaker": "operator", "text": "no carga"}]})
    return r.json()["number"]


@pytest.fixture
def two_cases(client):
    normal = escalate(client, "a", "no_internet", ["yes", "no", "no"])  # help_desk, normal
    high = escalate(client, "b", "tablet_wont_power_on", ["no"])  # logistics, high
    return normal, high


def test_queue_lists_high_priority_first(client, two_cases):
    normal, high = two_cases
    body = client.get("/cases").json()
    assert [c["number"] for c in body] == [high, normal]
    assert body[0]["flow_description"] == "Tableta no enciende, dañada o no disponible"
    assert body[0]["waiting_minutes"] == 0


def test_queue_orders_oldest_first_within_priority(client, cases):
    a = escalate(client, "a", "no_internet", ["yes", "no", "no"])
    b = escalate(client, "b", "no_internet", ["yes", "no", "no"])
    cases.cases[b] = cases.cases[b].__class__(**{**cases.cases[b].__dict__, "created_at": datetime.now(timezone.utc) - timedelta(minutes=30)})
    body = client.get("/cases").json()
    assert [c["number"] for c in body] == [b, a]
    assert body[0]["waiting_minutes"] == 30


def test_detail_shows_step_texts_and_transcript(client, two_cases):
    normal, _ = two_cases
    body = client.get(f"/cases/{normal}").json()
    assert [s["id"] for s in body["steps_tried"]] == ["mobile_data", "airplane_mode", "restart", "escalate"]
    assert "datos móviles" in body["steps_tried"][0]["text"]
    assert body["transcript"] == [{"speaker": "operator", "text": "no carga"}]


def test_detail_unknown_is_404(client):
    assert client.get("/cases/999").status_code == 404


def test_take_then_same_person_again_is_ok(client, two_cases):
    normal, _ = two_cases
    r = client.post(f"/cases/{normal}/take", json={"taken_by": "Ana"})
    assert r.status_code == 200 and r.json()["status"] == "taken" and r.json()["taken_by"] == "Ana"
    assert client.post(f"/cases/{normal}/take", json={"taken_by": "Ana"}).status_code == 200


def test_take_by_another_person_is_409(client, two_cases):
    normal, _ = two_cases
    client.post(f"/cases/{normal}/take", json={"taken_by": "Ana"})
    r = client.post(f"/cases/{normal}/take", json={"taken_by": "Luis"})
    assert r.status_code == 409 and "Ana" in r.json()["detail"]


def test_take_requires_a_name(client, two_cases):
    normal, _ = two_cases
    assert client.post(f"/cases/{normal}/take", json={"taken_by": ""}).status_code == 422


def test_close_moves_case_out_of_the_open_queue(client, two_cases):
    normal, high = two_cases
    r = client.post(f"/cases/{normal}/close", json={"close_reason": "resolved_by_phone", "notes": "reinició"})
    assert r.status_code == 200 and r.json()["status"] == "closed" and r.json()["close_reason"] == "resolved_by_phone"
    assert [c["number"] for c in client.get("/cases").json()] == [high]
    assert [c["number"] for c in client.get("/cases?status=closed").json()] == [normal]


def test_close_twice_is_409(client, two_cases):
    normal, _ = two_cases
    client.post(f"/cases/{normal}/close", json={"close_reason": "other"})
    assert client.post(f"/cases/{normal}/close", json={"close_reason": "other"}).status_code == 409


def test_take_closed_case_is_409(client, two_cases):
    normal, _ = two_cases
    client.post(f"/cases/{normal}/close", json={"close_reason": "other"})
    assert client.post(f"/cases/{normal}/take", json={"taken_by": "Ana"}).status_code == 409


def test_close_reason_is_validated(client, two_cases):
    normal, _ = two_cases
    assert client.post(f"/cases/{normal}/close", json={"close_reason": "because"}).status_code == 422


def test_invalid_status_filter_is_422(client):
    assert client.get("/cases?status=lost").status_code == 422
