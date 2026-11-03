"""HTTP ports of the core. The voice agent and the console only know these."""

from __future__ import annotations

from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from core import db
from core.engine import Engine, InvalidTransition, Result, label_from_dtmf, load_flows
from core.masking import mask_id_number, normalize_id_number
from core.sessions import PostgresSessionStore, Session, SessionStore

app = FastAPI(title="Core — field enrollment support")
engine = Engine(load_flows())  # fails at boot if a YAML is invalid: better than failing mid-call

_postgres_store = PostgresSessionStore()


def get_session_store() -> SessionStore:
    """Persistence adapter injection; tests replace it with an in-memory one."""
    return _postgres_store


Label = Literal["start", "yes", "no", "unclear", "human", "wait"]


class NextStepRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    phone: str = Field(min_length=1, max_length=32)
    label: Label
    flow: str | None = None  # required with label "start"
    dtmf: str | None = Field(default=None, max_length=32)  # keys pressed; takes precedence over the label


class NextStepResponse(BaseModel):
    step_id: str
    text: str
    active_wait: bool
    asks_dtmf: bool
    keypad_mode: bool
    end: bool
    create_case: bool
    destination: str | None
    priority: str | None
    steps_tried: list[str]


def _response(r: Result) -> NextStepResponse:
    return NextStepResponse(
        step_id=r.step.id,
        text=r.step.text,
        active_wait=r.step.active_wait,
        asks_dtmf=r.step.asks_dtmf,
        keypad_mode=r.keypad_mode,
        end=r.end,
        create_case=r.create_case,
        destination=r.step.destination,
        priority=r.step.priority,
        steps_tried=list(r.state.history),
    )


@app.get("/health")
def health(response: Response) -> dict:
    db_ok = db.is_healthy()
    if not db_ok:
        response.status_code = 503
    return {"status": "ok" if db_ok else "degraded", "postgres": db_ok, "flows": sorted(engine.flows)}


@app.post("/next-step", response_model=NextStepResponse)
def next_step(req: NextStepRequest, store: SessionStore = Depends(get_session_store)) -> NextStepResponse:
    if req.label == "start":
        if not req.flow:
            raise HTTPException(422, "label 'start' requires 'flow'")
        if req.flow not in engine.flows:
            raise HTTPException(422, f"unknown flow '{req.flow}'")
        r = engine.start(req.flow)
        store.save(Session(req.session_id, req.phone, r.state))
        store.log_event(req.session_id, "start", {"flow": req.flow, "step": r.step.id})
        return _response(r)

    session = store.get(req.session_id)
    if session is None:
        raise HTTPException(404, "unknown session; begin with label 'start'")

    current = engine.current(session.state)
    label: str = req.label
    masked_id = session.masked_id_number
    event: dict = {"step": current.step.id, "label": req.label}

    if req.dtmf is not None:
        if current.step.asks_dtmf:
            # ID-number step: if valid, store it MASKED and move on.
            digits = normalize_id_number(req.dtmf)
            label = "yes" if digits else "unclear"
            if digits:
                masked_id = mask_id_number(digits)
            event["dtmf"] = "valid_id_number" if digits else "invalid_id_number"  # never the number itself
        else:
            label = label_from_dtmf(req.dtmf)
            event["dtmf"] = req.dtmf[:1]
    elif current.step.asks_dtmf and label == "yes":
        # The ID number only comes in through the keypad: a spoken "yes" doesn't replace it.
        label = "unclear"

    try:
        r = engine.advance(session.state, label)
    except InvalidTransition as e:
        raise HTTPException(409, str(e)) from e

    store.save(Session(session.id, session.phone, r.state, masked_id))
    event.update(applied_label=label, next=r.step.id)
    store.log_event(session.id, "turn", event)
    return _response(r)
