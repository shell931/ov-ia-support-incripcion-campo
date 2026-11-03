"""Case persistence port and its two adapters.

A case is created once per call, when the flow reaches an end step whose action
is `create_case`. Creation is idempotent: retrying returns the same case number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from psycopg.types.json import Jsonb

from core import db


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


class CaseStore(Protocol):
    def create(self, case: NewCase) -> tuple[int, bool]:
        """Create the case for the session, or return the existing one. Returns (number, created)."""
        ...


class InMemoryCaseStore:
    def __init__(self) -> None:
        self.cases: dict[int, NewCase] = {}
        self.events: list[tuple[str, str, dict[str, Any]]] = []
        self._by_session: dict[str, int] = {}

    def create(self, case: NewCase) -> tuple[int, bool]:
        if case.session_id in self._by_session:
            return self._by_session[case.session_id], False
        number = len(self.cases) + 1
        self.cases[number] = case
        self._by_session[case.session_id] = number
        self.events.append((case.session_id, "escalation", {"case_number": number}))
        return number, True


# One round trip: insert (or find) the case and log the escalation event.
_CREATE_CASE = """
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


class PostgresCaseStore:
    def create(self, case: NewCase) -> tuple[int, bool]:
        with db.connect() as conn:
            row = conn.execute(
                _CREATE_CASE,
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
        number, created = row
        return number, created
