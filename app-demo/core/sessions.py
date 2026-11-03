"""Session persistence port and its two adapters.

- `PostgresSessionStore`: the real one (Supabase in the demo, self-hosted on-premise).
- `InMemorySessionStore`: for tests; needs no database.

Latency budget: a voice turn is one `get` plus one `save`, each a single round
trip to the database (the save also writes the event, atomically, in one statement).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from psycopg.types.json import Jsonb

from core import db
from core.engine import State


@dataclass(frozen=True)
class Session:
    id: str
    phone: str
    state: State
    masked_id_number: str | None = None


class SessionStore(Protocol):
    def get(self, session_id: str) -> Session | None: ...

    def save(self, session: Session, event_type: str, event_data: dict[str, Any]) -> None:
        """Persist the session and its event atomically."""
        ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    def get(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def save(self, session: Session, event_type: str, event_data: dict[str, Any]) -> None:
        self.sessions[session.id] = session
        self.events.append((session.id, event_type, event_data))


_UPSERT_WITH_EVENT = """
with upsert as (
    insert into sessions (id, phone, state, masked_id_number)
    values (%(id)s, %(phone)s, %(state)s, %(masked_id_number)s)
    on conflict (id) do update set
        phone = excluded.phone,
        state = excluded.state,
        masked_id_number = excluded.masked_id_number,
        updated_at = now()
    returning id
)
insert into events (session_id, type, data)
select id, %(event_type)s, %(event_data)s from upsert
"""


class PostgresSessionStore:
    def get(self, session_id: str) -> Session | None:
        with db.connect() as conn:
            row = conn.execute(
                "select phone, state, masked_id_number from sessions where id = %s",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        phone, state, masked_id_number = row
        return Session(session_id, phone, State.from_dict(state), masked_id_number)

    def save(self, session: Session, event_type: str, event_data: dict[str, Any]) -> None:
        with db.connect() as conn:
            conn.execute(
                _UPSERT_WITH_EVENT,
                {
                    "id": session.id,
                    "phone": session.phone,
                    "state": Jsonb(session.state.to_dict()),
                    "masked_id_number": session.masked_id_number,
                    "event_type": event_type,
                    "event_data": Jsonb(event_data),
                },
            )
