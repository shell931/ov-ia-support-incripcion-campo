# Diferencias entre propuestas 1, 2, 3 y 4

Las cuatro resuelven **el mismo problema de negocio** (operador en campo, árbol YAML, escalamiento con número de caso, **sin transferencia en vivo**). Cambian **canal de entrada**, **hosting** y **pipeline de voz**.

## Dónde está cada cosa en el repo

| Contenido | P1 | P2 | P3 | P4 | Común |
| --- | --- | --- | --- | --- | --- |
| Carpeta | [propuesta-1/](propuesta-1/README.md) | [propuesta-2/](propuesta-2/README.md) | [propuesta-3/](propuesta-3/README.md) | [propuesta-4/](propuesta-4/README.md) | [docs/](docs/README.md) |
| Diagrama + costos | [diagramas/](propuesta-1/diagramas/infraestructura.png) | [arquitectura.png](propuesta-2/arquitectura.png) | [arquitectura.png](propuesta-3/arquitectura.png) | [arquitectura.png](propuesta-4/arquitectura.png) | — |
| Costos detallados | [costos.md](propuesta-1/costos.md) | En README P2 | En README P3 | [costos.md](propuesta-4/costos.md) | — |
| Calendario (1 dev) | ~70 d | ~85–90 d | ~55–70 d | ~60–65 d | — |

## Canal de entrada

| | P1 | P2 | P3 | P4 |
| --- | --- | --- | --- | --- |
| **Entrada** | WhatsApp chat + llamada | Igual | Igual | **Teléfono PSTN** (marca número) |
| **Chat / fotos** | Sí | Sí | Sí | **No** en piloto |
| **Escalamiento al operador** | WhatsApp (caso + devolución) | Igual | Igual | **SMS / voz** + devolución **PSTN** |

## Comparación técnica (voz y datos)

| Tema | P1 | P2 | P3 | P4 |
| --- | --- | --- | --- | --- |
| **App / datos** | AWS ECS, RDS, Redis, S3 | On-premise | Railway + Supabase | **AWS (como P1)** |
| **SIP / salas** | LiveKit Cloud | LiveKit OSS | OpenAI Realtime (PoC) | **LiveKit Cloud** |
| **STT / TTS** | Deepgram + Cartesia | Whisper + Piper | GPT Live | **Deepgram + Cartesia** |
| **Clasificación** | LLM API | LLM local CPU | Haiku | **LLM API (como P1)** |
| **Telefonía entrada** | Meta WhatsApp | Meta WhatsApp | Meta WhatsApp | **Proveedor PSTN** |

## Costos mensuales (orientativos)

Supuestos: 22 días, 2 incidencias/día, 6 min/llamada. P1/P3: 50 % chat / 50 % voz. **P4: 100 % llamada.**

| Escala | P1 | P2 | P3 | P4 |
| ---: | ---: | ---: | ---: | ---: |
| 15 operadores | ≈ 300 | ≈ 220 | ≈ 190 | ≈ **310** |
| 1.400 operadores | ≈ 4.600 | ≈ 1.800 | ≈ 4.100 | ≈ **4.800** |

## Cuándo elegir cada una

| Propuesta | Elegir si… |
| --- | --- |
| **1** | Canal **WhatsApp** completo, piloto predecible, stack AWS ya modelado. |
| **2** | Datos en sitio, volumen alto, minimizar SaaS de voz. |
| **3** | PoC rápido WhatsApp con poco DevOps; voz Realtime tras validar SIP. |
| **4** | Misma **robustez de voz que P1** pero **sin Meta**; operadores **solo llaman**; aceptan perder chat/fotos en piloto. |

## Qué no cambia

- Tres casos YAML, DTMF, consola de mesa, sin transferencia en vivo en la llamada del operador.
