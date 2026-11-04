"""Dialog logic of the voice agent, with fakes: the real core engine in memory, a scripted classifier."""
from __future__ import annotations

import asyncio

import pytest

from core.engine import Engine, label_from_dtmf, load_flows
from core.masking import normalize_id_number
from voice_agent import dialog as d
from voice_agent.classifier import ANSWER_LABELS, PROBLEM_LABELS, parse_label
from voice_agent.core_client import Step


class FakeCore:
    """Same semantics as core /next-step and /cases, on the real YAML engine, without HTTP or DB."""

    def __init__(self) -> None:
        self.engine = Engine(load_flows())
        self.states: dict = {}
        self.cases: list[dict] = []

    async def next_step(self, session_id, phone, label, flow=None, dtmf=None) -> Step:
        if label == "start":
            r = self.engine.start(flow)
        else:
            state = self.states[session_id]
            current = self.engine.current(state).step
            if dtmf is not None:
                label = ("yes" if normalize_id_number(dtmf) else "unclear") if current.asks_dtmf else label_from_dtmf(dtmf)
            elif current.asks_dtmf and label == "yes":
                label = "unclear"
            r = self.engine.advance(state, label)
        self.states[session_id] = r.state
        return Step(r.step.id, r.step.text, r.step.active_wait, r.step.asks_dtmf, r.keypad_mode, r.end, r.create_case)

    async def create_case(self, session_id, transcript) -> int:
        self.cases.append({"session_id": session_id, "transcript": transcript})
        return 41 + len(self.cases)


class ScriptedClassifier:
    def __init__(self, problem: str = "no_internet", answers: list[str] | None = None) -> None:
        self.problem = problem
        self.answers = list(answers or [])
        self.seen: list[str] = []

    async def classify_problem(self, said: str) -> str:
        self.seen.append(said)
        return self.problem

    async def classify_answer(self, question: str, said: str) -> str:
        self.seen.append(said)
        return self.answers.pop(0)


def make(problem="no_internet", answers=None):
    core = FakeCore()
    clf = ScriptedClassifier(problem, answers)
    return d.Dialog("s-1", "+573000000000", clf, core), core, clf


def run(coro):
    return asyncio.run(coro)


def texts(replies):
    return [r.text for r in replies]


# --------------------------------------------------------------------------- happy paths


def test_greets_first():
    dialog, _, _ = make()
    assert texts(dialog.greet()) == [d.GREETING]


def test_no_internet_resolved_by_voice():
    dialog, core, _ = make("no_internet", ["yes", "yes"])
    first = run(dialog.on_speech("no tengo internet"))
    assert "datos móviles" in first[0].text
    run(dialog.on_speech("sí, están activos"))
    last = run(dialog.on_speech("ya tengo internet"))
    assert last[-1].hang_up and "resuelto" in last[-1].text
    assert dialog.finished and core.cases == []


def test_escalation_creates_case_and_says_its_number():
    dialog, core, _ = make("no_internet", ["no", "no"])
    run(dialog.on_speech("no tengo internet"))
    run(dialog.on_speech("no están activos"))
    replies = run(dialog.on_speech("no pude"))
    assert replies[-1].text == d.CASE_NUMBER.format(number=42)
    assert replies[-1].hang_up and not replies[-1].cacheable  # the number changes every call
    assert len(core.cases) == 1
    speakers = {t["speaker"] for t in core.cases[0]["transcript"]}
    assert speakers == {"operator", "agent"}


# --------------------------------------------------------------------------- in-between moments


def test_wait_keeps_the_step_and_acknowledges():
    dialog, _, _ = make("no_internet", ["no", "wait"])
    run(dialog.on_speech("sin internet"))
    run(dialog.on_speech("no están activos"))  # -> enable_data (active wait)
    replies = run(dialog.on_speech("espéreme un momento"))
    assert texts(replies) == [d.WAIT_ACK]


def test_unclear_repeats_then_offers_keypad():
    dialog, _, _ = make("no_internet", ["unclear", "unclear"])
    run(dialog.on_speech("sin internet"))
    once = run(dialog.on_speech("eh"))
    assert texts(once)[0] == d.NOT_UNDERSTOOD and d.KEYPAD_HINT not in texts(once)
    twice = run(dialog.on_speech("mmm"))
    assert texts(twice)[-1] == d.KEYPAD_HINT


def test_keypad_answers_a_question():
    dialog, _, _ = make("no_internet")
    run(dialog.on_speech("sin internet"))
    replies = run(dialog.on_dtmf("1"))  # 1 = yes -> airplane_mode
    assert "modo avión" in replies[0].text


def test_human_mid_flow_escalates():
    dialog, core, _ = make("tablet_wont_power_on", ["human"])
    run(dialog.on_speech("no prende"))
    replies = run(dialog.on_speech("quiero hablar con una persona"))
    assert replies[-1].hang_up and len(core.cases) == 1


# --------------------------------------------------------------------------- choosing the problem


def test_problem_by_keypad():
    dialog, _, _ = make()
    replies = run(dialog.on_dtmf("2"))  # 2 = tablet won't power on
    assert texts(replies) == ["¿Tiene la tableta con usted en el puesto?"]


def test_asking_for_a_person_first_opens_a_generic_case():
    dialog, core, _ = make("human")
    replies = run(dialog.on_speech("páseme con alguien"))
    assert replies[-1].hang_up and len(core.cases) == 1


def test_never_understood_problem_ends_in_a_case():
    dialog, core, _ = make("unclear")
    assert d.PROBLEM_QUESTION in run(dialog.on_speech("eh"))[0].text
    assert d.PROBLEM_KEYPAD in run(dialog.on_speech("eh"))[0].text
    last = run(dialog.on_speech("eh"))
    assert last[-1].hang_up and len(core.cases) == 1


# --------------------------------------------------------------------------- ID number


def test_id_number_only_by_keypad_and_masked():
    dialog, core, clf = make("first_login", [])
    run(dialog.on_speech("es mi primer ingreso"))
    assert dialog.wants_id_number
    clf.answers = ["yes"]
    spoken = run(dialog.on_speech("mi cédula es 1098765432"))
    assert texts(spoken) == [d.ID_BY_KEYPAD]  # a spoken ID does not count
    assert "1098765432" not in " ".join(clf.seen) and "*******432" in " ".join(clf.seen)
    typed = run(dialog.on_dtmf("1098765432"))
    assert not dialog.wants_id_number and typed[0].text != d.NOT_UNDERSTOOD


def test_invalid_id_by_keypad_repeats():
    dialog, _, _ = make("first_login")
    run(dialog.on_speech("primer ingreso"))
    replies = run(dialog.on_dtmf("12"))
    assert texts(replies)[0] == d.NOT_UNDERSTOOD and dialog.wants_id_number


def test_mask_digits():
    assert d.mask_digits("cédula 1.098.765.432 ok") == "cédula *******432 ok"
    assert d.mask_digits("marque 1 o 2") == "marque 1 o 2"


# --------------------------------------------------------------------------- failures


class BrokenCore(FakeCore):
    async def next_step(self, *a, **k):
        raise ConnectionError("core down")


def test_core_down_apologizes_and_hangs_up():
    dialog = d.Dialog("s", "p", ScriptedClassifier(), BrokenCore())
    replies = run(dialog.on_speech("no tengo internet"))
    assert texts(replies) == [d.TECH_ERROR] and replies[0].hang_up


def test_after_the_end_ignores_input():
    dialog, _, _ = make("human")
    run(dialog.on_speech("una persona"))
    assert run(dialog.on_speech("hola?")) == [] and run(dialog.on_dtmf("1")) == []


# --------------------------------------------------------------------------- classifier output parsing


@pytest.mark.parametrize(
    "raw, expected",
    [("yes", "yes"), (" No.", "no"), ("wait\n", "wait"), ("HUMAN", "human"), ("sí", "unclear"), ("", "unclear"), ("maybe", "unclear")],
)
def test_parse_answer_label(raw, expected):
    assert parse_label(raw, ANSWER_LABELS) == expected


def test_parse_problem_label():
    assert parse_label("first_login", PROBLEM_LABELS) == "first_login"
    assert parse_label("tablet_wont_power_on.", PROBLEM_LABELS) == "tablet_wont_power_on"
