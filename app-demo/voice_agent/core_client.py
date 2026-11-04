"""HTTP adapter to the core. The agent knows the core only through these two calls."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class Step:
    step_id: str
    text: str
    active_wait: bool
    asks_dtmf: bool
    keypad_mode: bool
    end: bool
    create_case: bool


class Core(Protocol):
    async def next_step(
        self, session_id: str, phone: str, label: str, flow: str | None = None, dtmf: str | None = None
    ) -> Step: ...

    async def create_case(self, session_id: str, transcript: list[dict]) -> int: ...


class HttpCore:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)

    async def next_step(
        self, session_id: str, phone: str, label: str, flow: str | None = None, dtmf: str | None = None
    ) -> Step:
        body: dict = {"session_id": session_id, "phone": phone, "label": label}
        if flow:
            body["flow"] = flow
        if dtmf is not None:
            body["dtmf"] = dtmf
        r = await self._client.post("/next-step", json=body)
        r.raise_for_status()
        d = r.json()
        return Step(
            step_id=d["step_id"],
            text=d["text"],
            active_wait=d["active_wait"],
            asks_dtmf=d["asks_dtmf"],
            keypad_mode=d["keypad_mode"],
            end=d["end"],
            create_case=d["create_case"],
        )

    async def create_case(self, session_id: str, transcript: list[dict]) -> int:
        # Idempotent in the core (one case per session): safe to retry.
        r = await self._client.post("/cases", json={"session_id": session_id, "transcript": transcript})
        r.raise_for_status()
        return int(r.json()["number"])

    async def aclose(self) -> None:
        await self._client.aclose()
