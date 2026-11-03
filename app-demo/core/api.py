"""HTTP ports of the core. The voice agent and the console only know these."""

from __future__ import annotations

from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from core import db
from datetime import datetime, timezone

from core.cases import (
    OPEN_STATUSES,
    Case,
    CaseClosed,
    CaseNotFound,
    CaseStore,
    CaseTakenByOther,
    NewCase,
    PostgresCaseStore,
)
from core.engine import Engine, InvalidTransition, Result, label_from_dtmf, load_flows
from core.masking import mask_id_number, mask_numbers_in_text, normalize_id_number
from core.sessions import PostgresSessionStore, Session, SessionStore

app = FastAPI(title="Core — field enrollment support")
engine = Engine(load_flows())  # fails at boot if a YAML is invalid: better than failing mid-call

_postgres_sessions = PostgresSessionStore()
_postgres_cases = PostgresCaseStore()


def get_session_store() -> SessionStore:
    """Persistence adapter injection; tests replace it with an in-memory one."""
    return _postgres_sessions


def get_case_store() -> CaseStore:
    return _postgres_cases


# --------------------------------------------------------------------------- health


@app.get("/health")
def health(response: Response) -> dict:
    db_ok = db.is_healthy()
    if not db_ok:
        response.status_code = 503
    return {"status": "ok" if db_ok else "degraded", "postgres": db_ok, "flows": sorted(engine.flows)}


# --------------------------------------------------------------------------- next step

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


@app.post("/next-step", response_model=NextStepResponse)
def next_step(req: NextStepRequest, store: SessionStore = Depends(get_session_store)) -> NextStepResponse:
    if req.label == "start":
        if not req.flow:
            raise HTTPException(422, "label 'start' requires 'flow'")
        if req.flow not in engine.flows:
            raise HTTPException(422, f"unknown flow '{req.flow}'")
        r = engine.start(req.flow)
        store.save(Session(req.session_id, req.phone, r.state), "start", {"flow": req.flow, "step": r.step.id})
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

    event.update(applied_label=label, next=r.step.id)
    store.save(Session(session.id, session.phone, r.state, masked_id), "turn", event)
    return _response(r)


# --------------------------------------------------------------------------- cases


class TranscriptTurn(BaseModel):
    speaker: Literal["operator", "agent"]
    text: str = Field(max_length=2000)


class CreateCaseRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    transcript: list[TranscriptTurn] = Field(default_factory=list, max_length=500)


class CreateCaseResponse(BaseModel):
    number: int
    created: bool  # False when the case already existed (agent retry)
    destination: str
    priority: str


@app.post("/cases", response_model=CreateCaseResponse)
def create_case(
    req: CreateCaseRequest,
    response: Response,
    sessions: SessionStore = Depends(get_session_store),
    cases: CaseStore = Depends(get_case_store),
) -> CreateCaseResponse:
    session = sessions.get(req.session_id)
    if session is None:
        raise HTTPException(404, "unknown session")

    current = engine.current(session.state)
    if not current.create_case:
        raise HTTPException(409, f"step '{current.step.id}' does not create a case")

    destination = current.step.destination or "help_desk"
    priority = current.step.priority or "normal"
    number, created = cases.create(
        NewCase(
            session_id=session.id,
            phone=session.phone,
            masked_id_number=session.masked_id_number,
            flow=session.state.flow_id,
            destination=destination,
            priority=priority,
            reason=current.step.id,
            steps_tried=list(session.state.history),
            transcript=[{"speaker": t.speaker, "text": mask_numbers_in_text(t.text)} for t in req.transcript],
        )
    )
    response.status_code = 201 if created else 200
    return CreateCaseResponse(number=number, created=created, destination=destination, priority=priority)


# --------------------------------------------------------------------------- console
# Exposed to the browser through Caddy under /api (GET /cases*, POST /cases/{n}/take|close only).

CaseStatus = Literal["open", "taken", "closed"]
CloseReason = Literal["resolved_by_phone", "tablet_replaced", "sent_to_census", "other"]


class StepTried(BaseModel):
    id: str
    text: str


class CaseSummary(BaseModel):
    number: int
    status: CaseStatus
    priority: str
    flow: str
    flow_description: str
    destination: str
    phone: str
    masked_id_number: str | None
    reason: str
    taken_by: str | None
    created_at: datetime
    waiting_minutes: int


class CaseDetail(CaseSummary):
    steps_tried: list[StepTried]
    transcript: list[TranscriptTurn]
    close_reason: str | None
    notes: str | None


class TakeCaseRequest(BaseModel):
    taken_by: str = Field(min_length=1, max_length=80)


class CloseCaseRequest(BaseModel):
    close_reason: CloseReason
    notes: str = Field(default="", max_length=2000)


def _summary_fields(c: Case) -> dict:
    flow = engine.flows.get(c.flow)
    created = c.created_at if c.created_at.tzinfo else c.created_at.replace(tzinfo=timezone.utc)
    return {
        "number": c.number,
        "status": c.status,
        "priority": c.priority,
        "flow": c.flow,
        "flow_description": flow.description if flow else c.flow,
        "destination": c.destination,
        "phone": c.phone,
        "masked_id_number": c.masked_id_number,
        "reason": c.reason,
        "taken_by": c.taken_by,
        "created_at": created,
        "waiting_minutes": max(0, int((datetime.now(timezone.utc) - created).total_seconds() // 60)),
    }


def _detail(c: Case) -> CaseDetail:
    flow = engine.flows.get(c.flow)
    steps = [
        StepTried(id=s, text=flow.steps[s].text if flow and s in flow.steps else s) for s in c.steps_tried
    ]
    return CaseDetail(
        **_summary_fields(c),
        steps_tried=steps,
        transcript=[TranscriptTurn(**t) for t in c.transcript],
        close_reason=c.close_reason,
        notes=c.notes,
    )


@app.get("/cases", response_model=list[CaseSummary])
def list_cases(status: CaseStatus | None = None, cases: CaseStore = Depends(get_case_store)) -> list[CaseSummary]:
    statuses = (status,) if status else OPEN_STATUSES
    return [CaseSummary(**_summary_fields(c)) for c in cases.list(statuses)]


@app.get("/cases/{number}", response_model=CaseDetail)
def get_case(number: int, cases: CaseStore = Depends(get_case_store)) -> CaseDetail:
    case = cases.get(number)
    if case is None:
        raise HTTPException(404, "case not found")
    return _detail(case)


@app.post("/cases/{number}/take", response_model=CaseDetail)
def take_case(number: int, req: TakeCaseRequest, cases: CaseStore = Depends(get_case_store)) -> CaseDetail:
    try:
        return _detail(cases.take(number, req.taken_by.strip()))
    except CaseNotFound:
        raise HTTPException(404, "case not found")
    except CaseClosed:
        raise HTTPException(409, "case is already closed")
    except CaseTakenByOther as e:
        raise HTTPException(409, f"case already taken by {e.taken_by}")


@app.post("/cases/{number}/close", response_model=CaseDetail)
def close_case(number: int, req: CloseCaseRequest, cases: CaseStore = Depends(get_case_store)) -> CaseDetail:
    try:
        return _detail(cases.close(number, req.close_reason, req.notes.strip()))
    except CaseNotFound:
        raise HTTPException(404, "case not found")
    except CaseClosed:
        raise HTTPException(409, "case is already closed")
