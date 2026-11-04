"""Voice agent: an adapter around the core.

Layers (hexagonal):
  dialog.py       pure conversation logic, no LiveKit, fully unit-tested
  classifier.py   port + adapters (Anthropic for the demo, OpenAI-compatible for on-prem)
  core_client.py  HTTP adapter to the core (/next-step, /cases)
  speech.py       says replies through LiveKit, caching fixed phrases (TTS cost)
  main.py         LiveKit entrypoint: STT, TTS, VAD, DTMF wiring
"""
