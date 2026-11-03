"""POST /next-step port, with in-memory persistence (no Postgres)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.api import app, get_session_store
from core.masking import mask_id_number, normalize_id_number
from core.sessions import InMemorySessionStore


@pytest.fixture
def store() -> InMemorySessionStore:
    return InMemorySessionStore()


@pytest.fixture
def client(store: InMemorySessionStore):
    app.dependency_overrides[get_session_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def turn(client, label, sid="s1", **extra):
    return client.post("/next-step", json={"session_id": sid, "phone": "+573001112233", "label": label, **extra})


def test_start_returns_first_step(client):
    r = turn(client, "start", flow="no_internet")
    assert r.status_code == 200
    body = r.json()
    assert body["step_id"] == "mobile_data"
    assert "datos móviles" in body["text"]
    assert body["steps_tried"] == ["mobile_data"]


def test_full_walk_over_http_until_escalation(client):
    turn(client, "start", flow="no_internet")
    for label in ["yes", "no"]:
        assert turn(client, label).status_code == 200
    body = turn(client, "no").json()
    assert body["step_id"] == "escalate"
    assert body["end"] and body["create_case"]
    assert body["destination"] == "help_desk"
    assert body["steps_tried"] == ["mobile_data", "airplane_mode", "restart", "escalate"]


def test_start_without_flow_is_422(client):
    assert turn(client, "start").status_code == 422


def test_unknown_flow_is_422(client):
    assert turn(client, "start", flow="does_not_exist").status_code == 422


def test_label_outside_contract_is_422(client):
    turn(client, "start", flow="no_internet")
    assert turn(client, "maybe").status_code == 422


def test_unknown_session_is_404(client):
    assert turn(client, "yes", sid="nobody").status_code == 404


def test_advancing_ended_flow_is_409(client):
    turn(client, "start", flow="no_internet")
    turn(client, "yes")
    turn(client, "yes")  # resolved
    assert turn(client, "yes").status_code == 409


def test_two_unclear_turn_on_keypad_mode(client):
    turn(client, "start", flow="no_internet")
    assert turn(client, "unclear").json()["keypad_mode"] is False
    assert turn(client, "unclear").json()["keypad_mode"] is True


def test_keypad_fallback(client):
    turn(client, "start", flow="no_internet")
    assert turn(client, "unclear", dtmf="1").json()["step_id"] == "airplane_mode"  # 1 = yes


def test_valid_id_number_advances_and_is_stored_masked(client, store):
    turn(client, "start", flow="first_login")
    body = turn(client, "unclear", dtmf="1012345678#").json()
    assert body["step_id"] == "credentials_received"
    assert store.sessions["s1"].masked_id_number == "*******678"


def test_id_number_never_appears_in_full_in_events(client, store):
    turn(client, "start", flow="first_login")
    turn(client, "unclear", dtmf="1012345678#")
    assert "1012345678" not in repr(store.events)


def test_invalid_id_number_counts_as_unclear(client):
    turn(client, "start", flow="first_login")
    assert turn(client, "unclear", dtmf="12#").json()["step_id"] == "ask_id_number"


def test_spoken_yes_does_not_replace_id_number(client):
    turn(client, "start", flow="first_login")
    assert turn(client, "yes").json()["step_id"] == "ask_id_number"


def test_human_escalates_from_anywhere(client):
    turn(client, "start", flow="tablet_wont_power_on")
    body = turn(client, "human").json()
    assert body["create_case"] and body["destination"] == "logistics"


def test_sessions_are_independent(client):
    turn(client, "start", sid="a", flow="no_internet")
    turn(client, "start", sid="b", flow="first_login")
    assert turn(client, "yes", sid="a").json()["step_id"] == "airplane_mode"


def test_every_turn_is_logged(client, store):
    turn(client, "start", flow="no_internet")
    turn(client, "yes")
    assert [t for _, t, _ in store.events] == ["start", "turn"]


# --------------------------------------------------------------------------- masking


@pytest.mark.parametrize(
    "raw, expected",
    [("1012345678#", "1012345678"), ("123456", "123456"), ("12#", None), ("", None), ("12345678901", None)],
)
def test_normalize_id_number(raw, expected):
    assert normalize_id_number(raw) == expected


@pytest.mark.parametrize("raw, expected", [("1012345678", "*******678"), ("123", "***"), ("", "")])
def test_mask_id_number(raw, expected):
    assert mask_id_number(raw) == expected
