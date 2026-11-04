"""Conversation logic of one call. No LiveKit here: speech and keys come in, replies go out.

Who decides what:
  - The operator's words -> Classifier -> a closed label (yes / no / wait / human / unclear).
  - The label -> core /next-step -> the YAML engine picks the next step and its text.
  - This class only glues them and phrases the in-between moments (greeting, "I'll wait",
    "I didn't understand", the case number).

Before a flow is chosen the agent asks what is wrong with the tablet and maps the answer to a flow
(speech through the classifier, or keys 1/2/3; 0 or "a person" goes straight to a case).
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

from voice_agent.classifier import Classifier
from voice_agent.core_client import Core, Step

log = logging.getLogger("voice_agent.dialog")

# --- Spoken texts (content: Spanish). Fixed texts are cacheable: synthesized once, replayed for free.
GREETING = (
    "Hola, soy el asistente de soporte de inscripción en campo. "
    "Cuénteme qué le pasa a la tableta: ¿no tiene internet, no enciende, o no puede ingresar o registrar la huella?"
)
PROBLEM_QUESTION = "¿La tableta no tiene internet, no enciende, o no puede ingresar o registrar la huella?"
PROBLEM_KEYPAD = (
    "Si prefiere, marque uno si no tiene internet, dos si la tableta no enciende, "
    "tres si no puede ingresar o con la huella, o cero para hablar con una persona."
)
NOT_UNDERSTOOD = "Perdón, no le entendí."
WAIT_ACK = "Tranquilo, aquí lo espero. Avíseme cuando esté."
KEYPAD_HINT = "Si prefiere, marque uno para sí, dos para no, o cero para hablar con una persona."
ID_BY_KEYPAD = "La cédula márquela en el teclado del teléfono y al final la tecla numeral."
CASE_NUMBER = "Su número de caso es el {number}."
TECH_ERROR = "Disculpe, tenemos un problema técnico. Por favor llame de nuevo en unos minutos."

PROBLEM_BY_KEY = {"1": "no_internet", "2": "tablet_wont_power_on", "3": "first_login", "0": "human"}
FLOWS = ("no_internet", "tablet_wont_power_on", "first_login")
FALLBACK_FLOW = "other"  # one-step flow that opens a case: "a person, please" or never understood
MAX_PROBLEM_ATTEMPTS = 3

_DIGIT_RUN = re.compile(r"\d(?:[\s.\-]?\d){4,}")


def _mask_run(match: re.Match) -> str:
    digits = re.sub(r"\D", "", match.group(0))
    return "*" * (len(digits) - 3) + digits[-3:]


def mask_digits(text: str) -> str:
    """Hide digit runs (an ID number said out loud) before the text reaches the classifier or the case."""
    return _DIGIT_RUN.sub(_mask_run, text)


@dataclass(frozen=True)
class Reply:
    text: str
    cacheable: bool = True  # fixed text: may be replayed from the audio cache
    hang_up: bool = False  # last reply of the call


class Dialog:
    def __init__(self, session_id: str, phone: str, classifier: Classifier, core: Core) -> None:
        self.session_id = session_id
        self.phone = phone
        self._classifier = classifier
        self._core = core
        self._lock = asyncio.Lock()  # speech and keys can arrive at the same time
        self._step: Step | None = None
        self._problem_attempts = 0
        self.transcript: list[dict] = []
        self.finished = False

    # ------------------------------------------------------------------ state seen by the adapter
    @property
    def wants_id_number(self) -> bool:
        """True while the current step collects the ID number by keypad (digits until '#')."""
        return bool(self._step and self._step.asks_dtmf)

    # ------------------------------------------------------------------ inputs
    def greet(self) -> list[Reply]:
        return self._say([Reply(GREETING)])

    async def on_speech(self, text: str) -> list[Reply]:
        text = mask_digits(text.strip())
        if not text or self.finished:
            return []
        async with self._lock:
            self.transcript.append({"speaker": "operator", "text": text})
            try:
                if self._step is None:
                    return await self._choose_problem(await self._classifier.classify_problem(text))
                label = await self._classifier.classify_answer(self._step.text, text)
                log.info("step=%s label=%s", self._step.step_id, label)
                return await self._advance(label=label)
            except Exception:
                log.exception("turn failed")
                return self._fail()

    async def on_dtmf(self, keys: str) -> list[Reply]:
        if not keys or self.finished:
            return []
        async with self._lock:
            try:
                if self._step is None:
                    return await self._choose_problem(PROBLEM_BY_KEY.get(keys[:1], "unclear"))
                log.info("step=%s dtmf=%s", self._step.step_id, "id_number" if self._step.asks_dtmf else keys[:1])
                return await self._advance(label="unclear", dtmf=keys)
            except Exception:
                log.exception("dtmf failed")
                return self._fail()

    # ------------------------------------------------------------------ internals
    async def _choose_problem(self, problem: str) -> list[Reply]:
        if problem in FLOWS:
            return await self._start(problem)
        if problem == "human":
            return await self._start(FALLBACK_FLOW)
        self._problem_attempts += 1
        if self._problem_attempts >= MAX_PROBLEM_ATTEMPTS:
            return await self._start(FALLBACK_FLOW)
        if self._problem_attempts == 1:
            return self._say([Reply(f"{NOT_UNDERSTOOD} {PROBLEM_QUESTION}")])
        return self._say([Reply(f"{NOT_UNDERSTOOD} {PROBLEM_KEYPAD}")])

    async def _start(self, flow: str) -> list[Reply]:
        log.info("flow=%s", flow)
        step = await self._core.next_step(self.session_id, self.phone, "start", flow=flow)
        return await self._present(step, previous=None, label="start")

    async def _advance(self, label: str, dtmf: str | None = None) -> list[Reply]:
        previous = self._step
        step = await self._core.next_step(self.session_id, self.phone, label, dtmf=dtmf)
        return await self._present(step, previous=previous, label=label if dtmf is None else "dtmf")

    async def _present(self, step: Step, previous: Step | None, label: str) -> list[Reply]:
        self._step = step
        same_step = previous is not None and previous.step_id == step.step_id

        if same_step and label == "wait":
            replies = [Reply(WAIT_ACK)]
        elif same_step and step.asks_dtmf and label != "dtmf":
            replies = [Reply(ID_BY_KEYPAD)]
        elif same_step:  # not understood (spoken) or invalid keys: repeat, with keypad help when due
            replies = [Reply(NOT_UNDERSTOOD), Reply(step.text)]
            if step.keypad_mode and not step.asks_dtmf:
                replies.append(Reply(KEYPAD_HINT))
        else:
            replies = [Reply(step.text)]

        if step.create_case:
            number = await self._core.create_case(self.session_id, self.transcript + self._agent_turns(replies))
            replies.append(Reply(CASE_NUMBER.format(number=number), cacheable=False))
        if step.end:
            replies[-1] = Reply(replies[-1].text, replies[-1].cacheable, hang_up=True)
            self.finished = True
        return self._say(replies)

    def _fail(self) -> list[Reply]:
        self.finished = True
        return self._say([Reply(TECH_ERROR, hang_up=True)])

    @staticmethod
    def _agent_turns(replies: list[Reply]) -> list[dict]:
        return [{"speaker": "agent", "text": r.text} for r in replies]

    def _say(self, replies: list[Reply]) -> list[Reply]:
        self.transcript.extend(self._agent_turns(replies))
        return replies
