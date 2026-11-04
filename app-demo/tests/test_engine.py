"""Walks the three trees without voice: if the engine is right, voice is just an adapter."""

from __future__ import annotations

import pytest

from core.engine import Engine, InvalidFlow, InvalidTransition, State, flow_from_dict, label_from_dtmf, load_flows

FLOW_IDS = ["no_internet", "first_login", "tablet_wont_power_on", "other"]


@pytest.fixture(scope="module")
def engine() -> Engine:
    return Engine(load_flows())


def walk(engine: Engine, flow_id: str, labels: list[str]):
    r = engine.start(flow_id)
    for label in labels:
        r = engine.advance(r.state, label)
    return r


# --------------------------------------------------------------------------- loading


def test_loads_all_flows(engine: Engine):
    assert set(engine.flows) == set(FLOW_IDS)


@pytest.mark.parametrize("flow_id", FLOW_IDS)
def test_every_step_is_reachable(engine: Engine, flow_id: str):
    flow = engine.flows[flow_id]
    seen, pending = set(), [flow.start]
    while pending:
        sid = pending.pop()
        if sid in seen:
            continue
        seen.add(sid)
        step = flow.steps[sid]
        pending += [t for t in (step.on_yes, step.on_no) if t]
    seen.add(flow.escalate)  # always reachable through "human"
    assert seen == set(flow.steps), f"orphan steps: {set(flow.steps) - seen}"


# --------------------------------------------------------------------------- no internet


@pytest.mark.parametrize(
    "labels, final",
    [
        (["yes", "yes"], "resolved"),  # data on, airplane mode off
        (["yes", "no", "yes"], "resolved"),  # restart fixes it
        (["yes", "no", "no"], "escalate"),  # restart does not fix it
        (["no", "yes", "yes"], "resolved"),  # turns data on
        (["no", "no"], "escalate"),  # cannot turn data on
        (["no", "yes", "no", "yes"], "resolved"),
        (["no", "yes", "no", "no"], "escalate"),
    ],
)
def test_no_internet_every_branch(engine: Engine, labels, final):
    r = walk(engine, "no_internet", labels)
    assert r.step.id == final
    assert r.end
    assert r.create_case == (final == "escalate")


def test_history_records_steps_tried(engine: Engine):
    r = walk(engine, "no_internet", ["yes", "no", "no"])
    assert r.state.history == ("mobile_data", "airplane_mode", "restart", "escalate")


# --------------------------------------------------------------------------- tablet


def test_missing_tablet_goes_to_logistics(engine: Engine):
    r = walk(engine, "tablet_wont_power_on", ["no"])
    assert r.step.id == "tablet_missing"
    assert r.create_case and r.step.destination == "logistics" and r.step.priority == "high"


def test_tablet_exhausts_four_checks_then_escalates(engine: Engine):
    r = walk(engine, "tablet_wont_power_on", ["yes", "no", "no", "no", "no"])
    assert r.step.id == "escalate"
    assert r.state.history[1:5] == ("wiggle_cable", "usb_c_cable", "other_outlet", "other_adapter")


@pytest.mark.parametrize("n_no", [0, 1, 2, 3])
def test_tablet_can_resolve_at_any_check(engine: Engine, n_no: int):
    r = walk(engine, "tablet_wont_power_on", ["yes"] + ["no"] * n_no + ["yes"])
    assert r.step.id == "resolved"


# --------------------------------------------------------------------------- first login


def test_login_starts_asking_id_number_on_keypad(engine: Engine):
    assert engine.start("first_login").step.asks_dtmf


def test_login_without_credentials_email_goes_to_census(engine: Engine):
    r = walk(engine, "first_login", ["yes", "no"])
    assert r.step.id == "missing_credentials" and r.step.destination == "census_office"


def test_login_two_credential_failures_escalate(engine: Engine):
    assert walk(engine, "first_login", ["yes", "yes", "no", "no"]).step.id == "escalate"


def test_login_rejected_fingerprint_is_high_priority(engine: Engine):
    r = walk(engine, "first_login", ["yes", "yes", "yes", "no", "no"])
    assert r.step.id == "fingerprint_rejected"
    assert r.step.destination == "census_office" and r.step.priority == "high"


def test_login_happy_path(engine: Engine):
    assert walk(engine, "first_login", ["yes", "yes", "yes", "yes"]).step.id == "resolved"


# --------------------------------------------------------------------------- cross-cutting rules


def test_human_escalates_from_any_step(engine: Engine):
    r = walk(engine, "no_internet", ["yes", "human"])
    assert r.step.id == "escalate" and r.create_case


def test_wait_neither_advances_nor_counts_as_failure(engine: Engine):
    r = walk(engine, "no_internet", ["yes", "no"])  # at "restart"
    r2 = engine.advance(r.state, "wait")
    assert r2.step.id == "restart"
    assert r2.state.unclear_attempts == 0


def test_unclear_repeats_then_switches_to_keypad(engine: Engine):
    r = engine.start("no_internet")
    r = engine.advance(r.state, "unclear")
    assert r.step.id == "mobile_data" and not r.keypad_mode
    r = engine.advance(r.state, "unclear")
    assert r.step.id == "mobile_data" and r.keypad_mode


def test_valid_answer_resets_unclear_counter(engine: Engine):
    r = engine.start("no_internet")
    r = engine.advance(r.state, "unclear")
    r = engine.advance(r.state, "yes")
    assert r.state.unclear_attempts == 0


def test_cannot_advance_an_ended_flow(engine: Engine):
    r = walk(engine, "no_internet", ["yes", "yes"])
    with pytest.raises(InvalidTransition):
        engine.advance(r.state, "yes")


@pytest.mark.parametrize("label", ["start", "maybe", ""])
def test_invalid_label(engine: Engine, label: str):
    with pytest.raises(InvalidTransition):
        engine.advance(engine.start("no_internet").state, label)


def test_unknown_flow(engine: Engine):
    with pytest.raises(InvalidTransition):
        engine.start("does_not_exist")


def test_state_round_trips(engine: Engine):
    r = walk(engine, "no_internet", ["no", "unclear"])
    assert State.from_dict(r.state.to_dict()) == r.state


@pytest.mark.parametrize("key, label", [("1", "yes"), ("2", "no"), ("0", "human"), ("9", "unclear")])
def test_dtmf(key: str, label: str):
    assert label_from_dtmf(key) == label


# --------------------------------------------------------------------------- YAML validation


def _base(**extra):
    d = {
        "id": "x",
        "steps": [
            {"id": "a", "text": "¿Sí?", "on_yes": "done", "on_no": "escalate"},
            {"id": "done", "text": "Listo.", "end": True},
            {"id": "escalate", "text": "Caso.", "end": True, "action": "create_case"},
        ],
    }
    d.update(extra)
    return d


def test_minimal_valid_flow():
    assert flow_from_dict(_base()).start == "a"


def test_rejects_transition_to_missing_step():
    d = _base()
    d["steps"][0]["on_yes"] = "ghost"
    with pytest.raises(InvalidFlow):
        flow_from_dict(d)


def test_rejects_non_end_step_without_on_no():
    d = _base()
    del d["steps"][0]["on_no"]
    with pytest.raises(InvalidFlow):
        flow_from_dict(d)


def test_rejects_escalate_that_does_not_create_case():
    d = _base()
    del d["steps"][2]["action"]
    with pytest.raises(InvalidFlow):
        flow_from_dict(d)


def test_rejects_duplicate_ids():
    d = _base()
    d["steps"].append({"id": "a", "text": "dup", "end": True})
    with pytest.raises(InvalidFlow):
        flow_from_dict(d)


# --------------------------------------------------------------------------- other (fallback)


def test_other_flow_opens_a_case_right_away(engine: Engine):
    r = engine.start("other")
    assert r.end and r.create_case
    assert r.step.destination == "help_desk"
