# Propuesta 4 — Tiempos de implementación

Estimación en **días hábiles**, **una persona**. Misma lógica de agente que [propuesta 1](../propuesta-1/tiempos.md), **sin fases de chat WhatsApp** ni espera de **WhatsApp Calling** de Meta.

## Fases

| Fase | Días | Qué queda listo |
| --- | ---: | --- |
| **0. Arranque** | 1–2 | Cuentas AWS, LiveKit, Deepgram, Cartesia, LLM, **proveedor PSTN** |
| **1. Infraestructura** | 3–12 | Terraform, ECS, RDS, Redis, S3, CI/CD |
| **2. Telefonía** | 10–18 | Número DID, trunk SIP → LiveKit, prueba de llamada entrante |
| **3. PoC voz** | 19–28 | Motor YAML “sin internet” + agente; una llamada PSTN de punta a punta |
| **4. Tres flujos voz** | 29–42 | Audios S3, DTMF, espera activa, ruido de puesto |
| **5. Consola y alertas** | 43–52 | Cola, tomar caso, Cognito, SES, SMS de caso (opcional) |
| **6. Endurecimiento** | 53–60 | Enmascarado, latencia, set de llamadas, mesa devuelve llamada |
| **7. Piloto en campo** | 61–68 | ~15 operadores, textos y audios |

**Total al piloto: ~60–65 días hábiles (~12–13 semanas).**

El camino crítico pasa por **número colombiano activo** y **calidad de audio PSTN** (eco, jitter), no por Meta.
