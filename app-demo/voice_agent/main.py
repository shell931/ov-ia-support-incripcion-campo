"""LiveKit entrypoint of the voice agent.

Run (from app-demo/, with .env filled in and the core running):
  python -m voice_agent.main console   # talk with your laptop's microphone, no phone line
  python -m voice_agent.main dev       # connect to LiveKit Cloud; join from the Agents Playground
  python -m voice_agent.main start     # production (docker compose)

LiveKit does NOT use an LLM to reply here: the YAML engine in the core decides every step.
on_user_turn_completed() intercepts each finished user turn and stops LiveKit's own reply.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from pathlib import Path

from livekit import rtc
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, JobProcess, StopResponse, cli
from livekit.plugins import deepgram, silero

from voice_agent import classifier as classifier_mod
from voice_agent.core_client import HttpCore
from voice_agent.dialog import Dialog, Reply
from voice_agent.speech import AudioCache, Speaker

log = logging.getLogger("voice_agent")

ID_NUMBER_KEY_TIMEOUT = 5.0  # seconds without a key press closes the ID number


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# --------------------------------------------------------------------------- providers (switch by .env)


def build_stt():
    kind = env("STT", "deepgram")
    if kind == "deepgram":
        return deepgram.STT(
            model=env("STT_MODEL", "nova-3"),
            language=env("STT_LANGUAGE", "es"),
            smart_format=True,
            numerals=True,  # spoken digits come as digits, so they can be masked before leaving the agent
        )
    raise RuntimeError(f"STT={kind} is not wired yet (on-prem: whisper). See propuesta-6/plan-de-accion.md")


def build_tts():
    kind = env("TTS", "deepgram")
    if kind == "deepgram":
        return deepgram.TTS(model=env("TTS_VOICE", "aura-2-celeste-es"))
    raise RuntimeError(f"TTS={kind} is not wired yet (on-prem: piper). See propuesta-6/plan-de-accion.md")


# --------------------------------------------------------------------------- agent


class SupportAgent(Agent):
    def __init__(self, dialog: Dialog, say) -> None:
        super().__init__(instructions="Deterministic support flow: replies come from the core, not from an LLM.")
        self._dialog = dialog
        self._say = say

    async def on_enter(self) -> None:
        self._say(self._dialog.greet())

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        self._say(await self._dialog.on_speech(new_message.text_content or ""))
        raise StopResponse()  # the core already answered; LiveKit must not generate a reply


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server = AgentServer(setup_fnc=prewarm)


@server.rtc_session(agent_name=env("AGENT_NAME"))
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    caller = next(iter(ctx.room.remote_participants.values()), None)
    if caller is None and not ctx.is_fake_job():
        caller = await ctx.wait_for_participant()
    phone = (caller.attributes.get("sip.phoneNumber") if caller else None) or (
        f"web:{caller.identity}" if caller else "console"
    )
    session_id = f"{ctx.room.name}-{uuid.uuid4().hex[:8]}"

    core = HttpCore(env("CORE_URL", "http://localhost:8000"))
    dialog = Dialog(session_id, phone, classifier_mod.from_env(), core)
    tts_engine = build_tts()
    session = AgentSession(stt=build_stt(), tts=tts_engine, vad=ctx.proc.userdata["vad"])

    cache_dir = env("AUDIO_CACHE_DIR")
    cache = AudioCache(Path(cache_dir), env("TTS_VOICE", "aura-2-celeste-es")) if cache_dir else None
    speaker = Speaker(session, tts_engine, cache)
    background: set[asyncio.Task] = set()

    def spawn(coro) -> None:
        task = asyncio.create_task(coro)
        background.add(task)
        task.add_done_callback(background.discard)

    async def hang_up(handle) -> None:
        if handle is not None:
            await handle.wait_for_playout()
        await asyncio.sleep(1.0)
        log.info("session=%s finished", session_id)
        if ctx.is_fake_job():
            ctx.shutdown(reason="call finished")
        else:
            await ctx.delete_room()  # ends the phone call for everyone in the room

    def say(replies: list[Reply]) -> None:
        if not replies:
            return
        handle = speaker.speak(replies)
        if replies[-1].hang_up:
            spawn(hang_up(handle))

    # ---- keypad (DTMF, phone calls only). ID number: digits until '#' or a pause; anything else: one key.
    keys: list[str] = []
    flush_timer: asyncio.TimerHandle | None = None

    async def send_keys(value: str) -> None:
        session.interrupt()  # pressing a key cuts the agent off, like any phone menu
        say(await dialog.on_dtmf(value))

    def flush_id_number() -> None:
        nonlocal flush_timer
        flush_timer = None
        value, keys[:] = "".join(keys), []
        if value:
            spawn(send_keys(value))

    def on_dtmf(ev: rtc.SipDTMF) -> None:
        nonlocal flush_timer
        if not dialog.wants_id_number:
            spawn(send_keys(ev.digit))
            return
        if flush_timer:
            flush_timer.cancel()
        if ev.digit == "#":
            flush_id_number()
            return
        keys.append(ev.digit)
        flush_timer = asyncio.get_running_loop().call_later(ID_NUMBER_KEY_TIMEOUT, flush_id_number)

    ctx.room.on("sip_dtmf_received", on_dtmf)

    async def cleanup(_reason: str = "") -> None:
        await core.aclose()

    ctx.add_shutdown_callback(cleanup)
    log.info("session=%s phone=%s started", session_id, "sip" if phone.startswith("+") else phone)
    await session.start(agent=SupportAgent(dialog, say), room=ctx.room)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(server)
