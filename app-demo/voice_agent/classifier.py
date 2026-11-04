"""Classifier port: turns what the operator said into a closed label.

The LLM never decides the next step (the YAML engine in the core does). It only maps free speech
to one of a few labels. Anything unexpected -- bad output, timeout, provider down -- becomes
"unclear", which the core already handles (repeat, then keypad fallback, then escalate).

Adapters, picked with CLASSIFIER in .env:
  anthropic      Claude Haiku 5.5 through the official SDK (demo / cloud mode)
  openai-compat  any local model behind an OpenAI-compatible endpoint, e.g. Ollama or vLLM (on-prem)
"""
from __future__ import annotations

import logging
import os
import re
from typing import Protocol

log = logging.getLogger("voice_agent.classifier")

ANSWER_LABELS = ("yes", "no", "wait", "human", "unclear")
PROBLEM_LABELS = ("no_internet", "tablet_wont_power_on", "first_login", "human", "unclear")

ANSWER_PROMPT = """You classify what a field enrollment operator said on a support phone call.
The agent just asked a yes/no question or gave an instruction.
Reply with exactly one label and nothing else:
yes     - affirms, confirms, done, it worked
no      - denies, still failing, can't do it
wait    - asks for time, is doing the step now
human   - wants a person, an agent, a human
unclear - anything else, off-topic or ambiguous"""

PROBLEM_PROMPT = """You classify the problem a field enrollment operator describes on a support phone call
about their work tablet. Reply with exactly one label and nothing else:
no_internet          - no Internet, no signal, no data, can't connect, can't sync
tablet_wont_power_on - won't turn on, dead, black screen, broken, lost or stolen, no tablet
first_login          - can't log in, user or password, first time, fingerprint, enrollment of fingers
human                - wants a person, an agent, a human
unclear              - anything else or ambiguous"""


def parse_label(raw: str, allowed: tuple[str, ...]) -> str:
    """First word of the model output if it is an allowed label; otherwise 'unclear'."""
    match = re.search(r"[a-z_]+", (raw or "").strip().lower())
    word = match.group(0) if match else ""
    return word if word in allowed else "unclear"


class Classifier(Protocol):
    async def classify_answer(self, question: str, said: str) -> str: ...
    async def classify_problem(self, said: str) -> str: ...


class _LabelClassifier:
    """Shared logic; adapters only implement _complete()."""

    async def _complete(self, system: str, user: str) -> str:  # pragma: no cover - adapters
        raise NotImplementedError

    async def _label(self, system: str, user: str, allowed: tuple[str, ...]) -> str:
        try:
            return parse_label(await self._complete(system, user), allowed)
        except Exception as e:  # provider down, timeout, quota: never break the call
            log.warning("classifier failed, using 'unclear': %s", type(e).__name__)
            return "unclear"

    async def classify_answer(self, question: str, said: str) -> str:
        return await self._label(ANSWER_PROMPT, f"Agent: {question}\nOperator: {said}", ANSWER_LABELS)

    async def classify_problem(self, said: str) -> str:
        return await self._label(PROBLEM_PROMPT, f"Operator: {said}", PROBLEM_LABELS)


class AnthropicClassifier(_LabelClassifier):
    def __init__(self, model: str, api_key: str | None = None, timeout: float = 4.0) -> None:
        import anthropic  # imported here so the dialog tests don't need the SDK

        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout, max_retries=1)
        self._model = model

    async def _complete(self, system: str, user: str) -> str:
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=8,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text if msg.content else ""


class OpenAICompatClassifier(_LabelClassifier):
    """Local model (Ollama, vLLM, llama.cpp server) behind /v1/chat/completions. On-prem mode."""

    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 4.0) -> None:
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout, headers=headers)
        self._model = model

    async def _complete(self, system: str, user: str) -> str:
        r = await self._client.post(
            "/chat/completions",
            json={
                "model": self._model,
                "temperature": 0,
                "max_tokens": 8,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def from_env() -> Classifier:
    kind = os.environ.get("CLASSIFIER", "anthropic").strip()
    model = os.environ.get("LLM_MODEL", "claude-haiku-5-5").strip()
    if kind == "anthropic":
        return AnthropicClassifier(model=model)
    if kind == "openai-compat":
        base_url = os.environ.get("LLM_BASE_URL", "").strip()
        if not base_url:
            raise RuntimeError("CLASSIFIER=openai-compat requires LLM_BASE_URL")
        return OpenAICompatClassifier(base_url=base_url, model=model, api_key=os.environ.get("LLM_API_KEY", ""))
    raise RuntimeError(f"unknown CLASSIFIER '{kind}' (expected anthropic | openai-compat)")
