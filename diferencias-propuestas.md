# Diferencias entre propuestas 1, 2 y 3

Las tres resuelven **el mismo problema de negocio**: operadores que contactan por **WhatsApp** (texto o llamada), siguen un **árbol YAML**, y si no se resuelve se **escala a la mesa** con número de caso — **sin transferencia en vivo**.

Lo que cambia es **cómo se hostea la app, la voz y los datos**.

## Dónde está cada cosa en el repo

| Contenido | Propuesta 1 | Propuesta 2 | Propuesta 3 | Común |
| --- | --- | --- | --- | --- |
| Carpeta | [propuesta-1/](propuesta-1/README.md) | [propuesta-2/](propuesta-2/README.md) | [propuesta-3/](propuesta-3/README.md) | [docs/](docs/README.md) |
| Infra / diagrama | [infraestructura.md](propuesta-1/infraestructura.md) + PNG | [README + PNG](propuesta-2/README.md) | [README](propuesta-3/README.md) | — |
| Costos detallados | [costos.md](propuesta-1/costos.md) | En propuesta-2 | Orden de magnitud en propuesta-3 | Mismos supuestos de uso |
| Calendario (1 dev) | [tiempos.md](propuesta-1/tiempos.md) (~70 d) | ~85–90 d | ~55–70 d | — |
| PDF, casos, agente | — | — | — | [analisis.md](docs/analisis.md), [analisis-agente-voz.md](docs/analisis-agente-voz.md) |

## Comparación técnica

| Tema | Propuesta 1 (AWS + SaaS voz) | Propuesta 2 (on-premise) | Propuesta 3 (stack ligero) |
| --- | --- | --- | --- |
| **Canal** | WhatsApp (Meta) | Igual | Igual |
| **Procedimiento** | YAML; LLM clasifica | Igual | Igual (Haiku clasifica; YAML en Railway) |
| **Hosting app** | ECS Fargate, SQS, Terraform | Servidores cliente | **Railway** |
| **Datos / consola** | RDS, Redis, S3, Cognito | Postgres, Redis, MinIO | **Supabase** (Postgres, Storage, Auth) |
| **Chat** | worker + LLM API | Igual lógica | Webhook Railway + **Haiku** |
| **Voz** | LiveKit Cloud + Deepgram + Cartesia | LiveKit OSS + Whisper + Piper | **GPT Live / OpenAI Realtime** (+ sideband Railway) |
| **Puente SIP WhatsApp** | LiveKit Cloud | LiveKit OSS | OpenAI SIP (PoC) o puente mínimo plan B |
| **Datos sensibles** | AWS us-east-1 + proveedores US | Red del cliente | Supabase + OpenAI + Anthropic |

## Costos mensuales (mismos supuestos)

22 días hábiles, 2 incidencias por operador y día, 50 % chat / 50 % voz, 6 min por llamada. Sin impuestos ni desarrollo.

| Escala | Propuesta 1 | Propuesta 2 | Propuesta 3 |
| ---: | ---: | ---: | ---: |
| 15 operadores | ≈ **300 US$** | ≈ **220 US$** | ≈ **130–240 US$** (estimado) |
| 1.400 operadores | ≈ **4.600 US$** | ≈ **1.800 US$** | **Variable** (Realtime por minuto puede dominar) |

Detalle: [propuesta-1/costos.md](propuesta-1/costos.md), costos en [propuesta-2/README.md](propuesta-2/README.md), [propuesta-3/README.md](propuesta-3/README.md#costos-mensuales-orden-de-magnitud).

## Tiempo de implementación (una persona)

| | P1 | P2 | P3 |
| --- | ---: | ---: | ---: |
| Hasta piloto en campo | ~70 días hábiles | ~85–90 | ~55–70 (si SIP WhatsApp→Realtime encaja) |

## Cuándo inclinarse por cada una

**Propuesta 1** — Equipo acostumbrado a AWS, piloto con proveedores de voz maduros (LiveKit + Deepgram), factura predecible a medio plazo con tablas de costo ya hechas.

**Propuesta 2** — Volumen alto, minimizar minutos a terceros, datos y transcripciones en sitio; aceptar operar GPU y SIP.

**Propuesta 3** — **Entrada WhatsApp** como hoy, pero **menos infra** (Railway + Supabase), inspiración stack “tutorial” (Haiku + GPT Live), **PoC rápido** y un solo dev. Ideal si el piloto es 15 operadores y hay que validar en semanas — **siempre** con PoC de SIP Meta + Realtime. Replantear P1/P2 si el costo por minuto Realtime explota en 1.400 operadores.

## Qué no cambia

- Tres casos YAML, DTMF / teclado si falla voz, número de caso por chat al escalar.
- Fuera del piloto: foto del cargador, nota de voz, reenvío de credenciales, inventario, guía offline.
