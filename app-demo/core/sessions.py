"""Session persistence port and its two adapters.

- `PostgresSessionStore`: the real one (demo, pilot and on-premise).
- `InMemorySessionStore`: for tests; needs no database.
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

    def save(self, session: Session) -> None: ...

    def log_event(self, session_id: str, type_: str, data: dict[str, Any]) -> None: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    def get(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def save(self, session: Session) -> None:
        self.sessions[session.id] = session

    def log_event(self, session_id: str, type_: str, data: dict[str, Any]) -> None:
        self.events.append((session_id, type_, data))


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

    def save(self, session: Session) -> None:
        with db.connect() as conn:
            conn.execute(
                """
                insert into sessions (id, phone, state, masked_id_number)
                values (%s, %s, %s, %s)
                on conflict (id) do update set
                    phone = excluded.phone,
                    state = excluded.state,
                    masked_id_number = excluded.masked_id_number,
                    updated_at = now()
                """,
                (session.id, session.phone, Jsonb(session.state.to_dict()), session.masked_id_number),
            )

    def log_event(self, session_id: str, type_: str, data: dict[str, Any]) -> None:
        with db.connect() as conn:
            conn.execute(
                "insert into events (session_id, type, data) values (%s, %s, %s)",
                (session_id, type_, Jsonb(data)),
            )
