"""Guided-flow engine.

Loads the YAML decision trees and picks the next step from a label
(yes / no / unclear / human / wait). It is deterministic: whatever the
operator hears comes from the YAML, never from an LLM.

Architecture rule: this module imports nothing from LiveKit or any vendor SDK.
It is the heart of the hexagonal core.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

LABELS = frozenset({"start", "yes", "no", "unclear", "human", "wait"})

# Keypad fallback when speech recognition fails.
DTMF_TO_LABEL = {"1": "yes", "2": "no", "0": "human"}

FLOWS_DIR = Path(__file__).parent / "flows"


class InvalidFlow(ValueError):
    """A flow YAML does not satisfy the contract."""


class InvalidTransition(ValueError):
    """Tried to advance with a label that does not apply to the current state."""


@dataclass(frozen=True)
class Step:
    id: str
    text: str
    on_yes: str | None = None
    on_no: str | None = None
    active_wait: bool = False  # silence does not end the turn; agent checks back every 20–30 s
    asks_dtmf: bool = False  # input comes from the keypad (e.g. ID number)
    end: bool = False
    action: str | None = None  # "create_case"
    destination: str | None = None  # "help_desk" | "census_office" | "logistics"
    priority: str | None = None  # "normal" | "high"


@dataclass(frozen=True)
class Flow:
    id: str
    description: str
    start: str
    escalate: str
    max_unclear_attempts: int
    steps: dict[str, Step]


@dataclass(frozen=True)
class State:
    """Session state inside a flow. Immutable: every advance returns a new one."""

    flow_id: str
    step_id: str
    unclear_attempts: int = 0
    history: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "unclear_attempts": self.unclear_attempts,
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "State":
        return cls(
            flow_id=d["flow_id"],
            step_id=d["step_id"],
            unclear_attempts=d.get("unclear_attempts", 0),
            history=tuple(d.get("history", ())),
        )


@dataclass(frozen=True)
class Result:
    state: State
    step: Step
    keypad_mode: bool  # agent must offer "1 yes, 2 no, 0 human"
    create_case: bool  # agent must call create_case()

    @property
    def end(self) -> bool:
        return self.step.end


# --------------------------------------------------------------------------- loading


def _step_from_dict(d: dict[str, Any], flow_id: str) -> Step:
    try:
        return Step(
            id=d["id"],
            text=str(d["text"]).strip(),
            on_yes=d.get("on_yes"),
            on_no=d.get("on_no"),
            active_wait=bool(d.get("active_wait", False)),
            asks_dtmf=bool(d.get("asks_dtmf", False)),
            end=bool(d.get("end", False)),
            action=d.get("action"),
            destination=d.get("destination"),
            priority=d.get("priority"),
        )
    except KeyError as e:
        raise InvalidFlow(f"{flow_id}: step missing required field {e}") from e


def _validate(flow: Flow) -> None:
    steps = flow.steps
    if flow.start not in steps:
        raise InvalidFlow(f"{flow.id}: start step '{flow.start}' does not exist")
    if flow.escalate not in steps:
        raise InvalidFlow(f"{flow.id}: escalate step '{flow.escalate}' does not exist")
    if flow.max_unclear_attempts < 1:
        raise InvalidFlow(f"{flow.id}: max_unclear_attempts must be >= 1")
    for step in steps.values():
        if not step.text:
            raise InvalidFlow(f"{flow.id}/{step.id}: empty text")
        if step.end:
            if step.on_yes or step.on_no:
                raise InvalidFlow(f"{flow.id}/{step.id}: an end step has no transitions")
            continue
        if not step.on_yes or not step.on_no:
            raise InvalidFlow(f"{flow.id}/{step.id}: a non-end step needs 'on_yes' and 'on_no'")
        for target in (step.on_yes, step.on_no):
            if target not in steps:
                raise InvalidFlow(f"{flow.id}/{step.id}: points to '{target}', which does not exist")
        if step.action is not None:
            raise InvalidFlow(f"{flow.id}/{step.id}: only end steps carry an action")
    if not steps[flow.escalate].end or steps[flow.escalate].action != "create_case":
        raise InvalidFlow(f"{flow.id}: the escalate step must be an end step that creates a case")


def flow_from_dict(d: dict[str, Any]) -> Flow:
    flow_id = d.get("id") or "<no id>"
    raw_steps = d.get("steps") or []
    if not raw_steps:
        raise InvalidFlow(f"{flow_id}: has no steps")
    steps: dict[str, Step] = {}
    for raw in raw_steps:
        step = _step_from_dict(raw, flow_id)
        if step.id in steps:
            raise InvalidFlow(f"{flow_id}: duplicate step id '{step.id}'")
        steps[step.id] = step
    flow = Flow(
        id=flow_id,
        description=str(d.get("description", "")).strip(),
        start=d.get("start") or raw_steps[0]["id"],
        escalate=d.get("escalate", "escalate"),
        max_unclear_attempts=int(d.get("max_unclear_attempts", 2)),
        steps=steps,
    )
    _validate(flow)
    return flow


def load_flows(directory: Path = FLOWS_DIR) -> dict[str, Flow]:
    flows: dict[str, Flow] = {}
    for path in sorted(directory.glob("*.yaml")):
        flow = flow_from_dict(yaml.safe_load(path.read_text(encoding="utf-8")))
        if flow.id in flows:
            raise InvalidFlow(f"duplicate flow '{flow.id}' in {path.name}")
        flows[flow.id] = flow
    if not flows:
        raise InvalidFlow(f"no flows in {directory}")
    return flows


# --------------------------------------------------------------------------- engine


def label_from_dtmf(key: str) -> str:
    """Map a keypad fallback key to a label. Any other key means unclear."""
    return DTMF_TO_LABEL.get(key.strip(), "unclear")


class Engine:
    def __init__(self, flows: dict[str, Flow]):
        self._flows = flows

    @property
    def flows(self) -> dict[str, Flow]:
        return self._flows

    def _flow(self, flow_id: str) -> Flow:
        try:
            return self._flows[flow_id]
        except KeyError as e:
            raise InvalidTransition(f"unknown flow '{flow_id}'") from e

    def _result(self, flow: Flow, state: State, keypad_mode: bool = False) -> Result:
        step = flow.steps[state.step_id]
        return Result(state=state, step=step, keypad_mode=keypad_mode, create_case=step.action == "create_case")

    def start(self, flow_id: str) -> Result:
        flow = self._flow(flow_id)
        state = State(flow_id=flow.id, step_id=flow.start, history=(flow.start,))
        return self._result(flow, state)

    def current(self, state: State) -> Result:
        return self._result(self._flow(state.flow_id), state)

    def advance(self, state: State, label: str) -> Result:
        if label not in LABELS or label == "start":
            raise InvalidTransition(f"invalid label '{label}'")
        flow = self._flow(state.flow_id)
        step = flow.steps[state.step_id]
        if step.end:
            raise InvalidTransition(f"flow already ended at '{step.id}'")

        if label == "wait":
            # Active wait: the operator is doing something; not a failure.
            return self._result(flow, state)

        if label == "unclear":
            attempts = state.unclear_attempts + 1
            new_state = replace(state, unclear_attempts=attempts)
            return self._result(flow, new_state, keypad_mode=attempts >= flow.max_unclear_attempts)

        if label == "human":
            target = flow.escalate
        else:
            target = step.on_yes if label == "yes" else step.on_no
        new_state = State(flow_id=flow.id, step_id=target, unclear_attempts=0, history=state.history + (target,))
        return self._result(flow, new_state)
