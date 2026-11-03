"""Case persistence port and its two adapters.

A case is created once per call, when the flow reaches an end step whose action
is `create_case`. Creation is idempotent: retrying returns the same case number.
The help-desk console then lists, takes and closes cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Protocol

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from core import db

OPEN_STATUSES = ("open", "taken")


@dataclass(frozen=True)
class NewCase:
    session_id: str
    phone: str
    masked_id_number: str | None
    flow: str
    destination: str
    priority: str
    reason: str  # end step that created the case
    steps_tried: list[str]
    transcript: list[dict[str, str]] = field(default_factory=list)  # already masked


@dataclass(frozen=True)
class Case:
    number: int
    session_id: str
    status: str  # open | taken | closed
    priority: str
    flow: str
    destination: str
    phone: str
    masked_id_number: str | None
    reason: str
    steps_tried: list[str]
    transcript: list[dict[str, str]]
    taken_by: str | None
    close_reason: str | None
    notes: str | None
    created_at: datetime


class CaseNotFound(LookupError):
    pass


class CaseClosed(ValueError):
    pass


class CaseTakenByOther(ValueError):
    def __init__(self, taken_by: str):
        super().__init__(f"case already taken by {taken_by}")
        self.taken_by = taken_by


class CaseStore(Protocol):
    def create(self, case: NewCase) -> tuple[int, bool]:
        """Create the case for the session, or return the existing one. Returns (number, created)."""
        ...

    def list(self, statuses: tuple[str, ...]) -> list[Case]:
        """High priority first, then oldest first."""
        ...

    def get(self, number: int) -> Case | None: ...

    def take(self, number: int, taken_by: str) -> Case:
        """Idempotent for the same person. Raises CaseNotFound, CaseClosed, CaseTakenByOther."""
        ...

    def close(self, number: int, close_reason: str, notes: str) -> Case:
        """Raises CaseNotFound, CaseClosed."""
        ...


def _queue_key(c: Case) -> tuple:
    return (c.priority != "high", c.created_at)


class InMemoryCaseStore:
    def __init__(self) -> None:
        self.cases: dict[int, Case] = {}
        self.events: list[tuple[str, str, dict[str, Any]]] = []
        self._by_session: dict[str, int] = {}

    def create(self, case: NewCase) -> tuple[int, bool]:
        if case.session_id in self._by_session:
            return self._by_session[case.session_id], False
        number = len(self.cases) + 1
        self.cases[number] = Case(
            number=number,
            session_id=case.session_id,
            status="open",
            priority=case.priority,
            flow=case.flow,
            destination=case.destination,
            phone=case.phone,
            masked_id_number=case.masked_id_number,
            reason=case.reason,
            steps_tried=list(case.steps_tried),
            transcript=list(case.transcript),
            taken_by=None,
            close_reason=None,
            notes=None,
            created_at=datetime.now(timezone.utc),
        )
        self._by_session[case.session_id] = number
        self.events.append((case.session_id, "escalation", {"case_number": number}))
        return number, True

    def list(self, statuses: tuple[str, ...]) -> list[Case]:
        return sorted((c for c in self.cases.values() if c.status in statuses), key=_queue_key)

    def get(self, number: int) -> Case | None:
        return self.cases.get(number)

    def take(self, number: int, taken_by: str) -> Case:
        case = self._existing(number)
        if case.status == "taken" and case.taken_by != taken_by:
            raise CaseTakenByOther(case.taken_by or "")
        updated = replace(case, status="taken", taken_by=taken_by)
        self.cases[number] = updated
        self.events.append((case.session_id, "case_taken", {"case_number": number, "by": taken_by}))
        return updated

    def close(self, number: int, close_reason: str, notes: str) -> Case:
        case = self._existing(number)
        updated = replace(case, status="closed", close_reason=close_reason, notes=notes)
        self.cases[number] = updated
        self.events.append((case.session_id, "case_closed", {"case_number": number, "reason": close_reason}))
        return updated

    def _existing(self, number: int) -> Case:
        case = self.cases.get(number)
        if case is None:
            raise CaseNotFound(number)
        if case.status == "closed":
            raise CaseClosed(number)
        return case


# --------------------------------------------------------------------------- Postgres

_COLUMNS = (
    "number, session_id, status, priority, flow, destination, phone, masked_id_number, "
    "reason, steps_tried, transcript, taken_by, close_reason, notes, created_at"
)

# One round trip: insert (or find) the case and log the escalation event.
_CREATE = """
with ins as (
    insert into cases (session_id, phone, masked_id_number, flow, destination,
                       priority, reason, steps_tried, transcript)
    values (%(session_id)s, %(phone)s, %(masked_id_number)s, %(flow)s, %(destination)s,
            %(priority)s, %(reason)s, %(steps_tried)s, %(transcript)s)
    on conflict (session_id) do nothing
    returning number
),
ev as (
    insert into events (session_id, type, data)
    select %(session_id)s, 'escalation', jsonb_build_object('case_number', number) from ins
)
select number, true from ins
union all
select number, false from cases where session_id = %(session_id)s and not exists (select 1 from ins)
"""

_TAKE = f"""
with upd as (
    update cases set status = 'taken', taken_by = %(by)s, updated_at = now()
    where number = %(number)s
      and (status = 'open' or (status = 'taken' and taken_by = %(by)s))
    returning {_COLUMNS}
),
ev as (
    insert into events (session_id, type, data)
    select session_id, 'case_taken', jsonb_build_object('case_number', number, 'by', taken_by) from upd
)
select {_COLUMNS} from upd
"""

_CLOSE = f"""
with upd as (
    update cases set status = 'closed', close_reason = %(reason)s, notes = %(notes)s, updated_at = now()
    where number = %(number)s and status <> 'closed'
    returning {_COLUMNS}
),
ev as (
    insert into events (session_id, type, data)
    select session_id, 'case_closed', jsonb_build_object('case_number', number, 'reason', close_reason) from upd
)
select {_COLUMNS} from upd
"""


def _row_to_case(row: dict[str, Any]) -> Case:
    return Case(**row)


class PostgresCaseStore:
    def create(self, case: NewCase) -> tuple[int, bool]:
        with db.connect() as conn:
            number, created = conn.execute(
                _CREATE,
                {
                    "session_id": case.session_id,
                    "phone": case.phone,
                    "masked_id_number": case.masked_id_number,
                    "flow": case.flow,
                    "destination": case.destination,
                    "priority": case.priority,
                    "reason": case.reason,
                    "steps_tried": Jsonb(case.steps_tried),
                    "transcript": Jsonb(case.transcript),
                },
            ).fetchone()
        return number, created

    def list(self, statuses: tuple[str, ...]) -> list[Case]:
        with db.connect() as conn:
            cur = conn.cursor(row_factory=dict_row)
            rows = cur.execute(
                f"select {_COLUMNS} from cases where status = any(%s) "
                "order by (priority = 'high') desc, created_at asc limit 200",
                (list(statuses),),
            ).fetchall()
        return [_row_to_case(r) for r in rows]

    def get(self, number: int) -> Case | None:
        with db.connect() as conn:
            cur = conn.cursor(row_factory=dict_row)
            row = cur.execute(f"select {_COLUMNS} from cases where number = %s", (number,)).fetchone()
        return _row_to_case(row) if row else None

    def take(self, number: int, taken_by: str) -> Case:
        with db.connect() as conn:
            cur = conn.cursor(row_factory=dict_row)
            row = cur.execute(_TAKE, {"number": number, "by": taken_by}).fetchone()
        if row:
            return _row_to_case(row)
        self._raise_for(number)

    def close(self, number: int, close_reason: str, notes: str) -> Case:
        with db.connect() as conn:
            cur = conn.cursor(row_factory=dict_row)
            row = cur.execute(_CLOSE, {"number": number, "reason": close_reason, "notes": notes}).fetchone()
        if row:
            return _row_to_case(row)
        self._raise_for(number)

    def _raise_for(self, number: int):
        """The conditional update matched nothing: explain why."""
        case = self.get(number)
        if case is None:
            raise CaseNotFound(number)
        if case.status == "closed":
            raise CaseClosed(number)
        raise CaseTakenByOther(case.taken_by or "")
