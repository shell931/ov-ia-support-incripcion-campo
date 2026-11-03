# Propuesta 5 — Tiempos de implementación

Estimación en **días hábiles**, **una persona**. Combina el calendario de telefonía de [propuesta 4](../propuesta-4/tiempos.md) con el trabajo on-premise de [propuesta 2](../propuesta-2/README.md) (LiveKit OSS, GPU, Whisper, Piper).

Sin fases de chat WhatsApp ni espera de Meta Calling.

## Fases

| Fase | Días | Qué queda listo |
| --- | ---: | --- |
| **0. Arranque** | 1–2 | Cuentas proveedor PSTN; inventario de rack/GPU; textos del flujo “sin internet” |
| **1. Datacenter base** | 3–14 | Servidores CPU, Postgres, Redis, MinIO, reverse proxy, CI/CD interno |
| **2. LiveKit OSS + GPU** | 15–28 | LiveKit, Faster-Whisper, Piper, LLM chico; smoke de STT/TTS |
| **3. Telefonía** | 29–38 | DID, trunk SIP → LiveKit on-prem, prueba de llamada entrante |
| **4. PoC voz** | 39–50 | Motor YAML “sin internet” + voice-agent; una llamada PSTN de punta a punta |
| **5. Tres flujos voz** | 51–64 | Audios MinIO, DTMF, espera activa, ruido de puesto |
| **6. Consola y alertas** | 65–74 | Cola, tomar caso, SMS/correo de caso, login local |
| **7. Endurecimiento + piloto** | 75–85 | Enmascarado, latencia, set de llamadas, ~15 operadores en campo |

**Total al piloto: ~75–85 días hábiles (~15–17 semanas).**

El camino crítico es **doble**: número colombiano activo + calidad de audio PSTN, **y** estabilizar Whisper/LiveKit en GPU propia. No hay espera de verificación Meta, pero sí compra o asignación de GPU si no existe.

## Frente a P2 y P4

| | P2 | P4 | **P5** |
| --- | ---: | ---: | ---: |
| Hasta piloto | ~85–90 | ~60–65 | ~**75–85** |
| Motivo | Meta + chat + on-prem | PSTN + nube lista | PSTN + on-prem (sin chat Meta) |
