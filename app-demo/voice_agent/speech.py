"""Says replies through the LiveKit session, replaying fixed phrases from an audio cache.

Why a cache: the step texts of the YAML are the same on every call. Paying the TTS provider to
synthesize them again each time is ~7x the cost at 1,400 operators (see propuesta-6/costos.md).
So a fixed phrase is synthesized once, stored as WAV on disk, and replayed from then on. Only
dynamic text (the case number) is synthesized live. A cached phrase also starts playing at once.

First time a phrase is heard: it streams from the TTS as usual, and in the background it is
synthesized once more into the cache (one extra synthesis per distinct phrase, ever).
Changing the voice (TTS_VOICE) changes the cache key, so old audio is never mixed in.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import wave
from collections.abc import AsyncIterator
from pathlib import Path

from livekit import rtc
from livekit.agents import AgentSession, tts

from voice_agent.dialog import Reply

log = logging.getLogger("voice_agent.speech")

FRAME_MS = 20


class AudioCache:
    def __init__(self, directory: Path, voice: str) -> None:
        self._dir = directory
        self._voice = voice
        self._memory: dict[str, tuple[bytes, int, int]] = {}  # key -> (pcm16, sample_rate, channels)
        self._filling: set[str] = set()
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self._voice}\n{text}".encode()).hexdigest()[:32]

    def get(self, text: str) -> tuple[bytes, int, int] | None:
        key = self._key(text)
        if key in self._memory:
            return self._memory[key]
        path = self._dir / f"{key}.wav"
        if not path.exists():
            return None
        try:
            with wave.open(str(path), "rb") as w:
                entry = (w.readframes(w.getnframes()), w.getframerate(), w.getnchannels())
        except (wave.Error, EOFError):
            path.unlink(missing_ok=True)  # half-written file: rebuild it
            return None
        self._memory[key] = entry
        return entry

    async def fill(self, engine: tts.TTS, text: str) -> None:
        key = self._key(text)
        if key in self._filling or self.get(text) is not None:
            return
        self._filling.add(key)
        try:
            pcm, rate, channels = bytearray(), 0, 1
            async with engine.synthesize(text) as stream:
                async for ev in stream:
                    pcm += bytes(ev.frame.data)
                    rate, channels = ev.frame.sample_rate, ev.frame.num_channels
            if not pcm or not rate:
                return
            tmp = self._dir / f"{key}.wav.tmp"
            with wave.open(str(tmp), "wb") as w:
                w.setnchannels(channels)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(bytes(pcm))
            tmp.replace(self._dir / f"{key}.wav")  # atomic: readers never see half a file
            self._memory[key] = (bytes(pcm), rate, channels)
            log.info("cached phrase %s (%d bytes)", key, len(pcm))
        except Exception as e:  # the cache is an optimization: never break the call
            log.warning("could not cache phrase: %s", type(e).__name__)
        finally:
            self._filling.discard(key)


async def _frames(pcm: bytes, rate: int, channels: int) -> AsyncIterator[rtc.AudioFrame]:
    samples = rate * FRAME_MS // 1000
    step = samples * channels * 2
    for i in range(0, len(pcm), step):
        chunk = pcm[i : i + step]
        yield rtc.AudioFrame(chunk, rate, channels, len(chunk) // (2 * channels))


class Speaker:
    def __init__(self, session: AgentSession, engine: tts.TTS, cache: AudioCache | None) -> None:
        self._session = session
        self._tts = engine
        self._cache = cache
        self._tasks: set[asyncio.Task] = set()

    def speak(self, replies: list[Reply]):
        """Queues the replies in order; returns the handle of the last one (or None)."""
        handle = None
        for r in replies:
            cached = self._cache.get(r.text) if (self._cache and r.cacheable) else None
            if cached:
                handle = self._session.say(r.text, audio=_frames(*cached))
            else:
                handle = self._session.say(r.text)
                if self._cache and r.cacheable:
                    task = asyncio.create_task(self._cache.fill(self._tts, r.text))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
        return handle
