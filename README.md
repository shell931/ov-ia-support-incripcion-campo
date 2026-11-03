# Soporte IA — inscripción en campo

Asistente de nivel 1 para operadores de puestos de inscripción. El canal de ayuda es el celular del operador: la tableta del puesto muchas veces es justo lo que está fallando.

## Cinco formas de desplegarlo

Mismo árbol YAML y consola de casos; cambian canal de entrada, hosting y voz:

| | Carpeta | Idea |
| --- | --- | --- |
| **Propuesta 1 — nube AWS** | [propuesta-1/](propuesta-1/README.md) | **WhatsApp** + LiveKit + Deepgram + Cartesia + ECS |
| **Propuesta 2 — on-premise** | [propuesta-2/](propuesta-2/README.md) | WhatsApp + LiveKit OSS + Whisper + Piper en datacenter |
| **Propuesta 3 — stack ligero** | [propuesta-3/](propuesta-3/README.md) | WhatsApp + Railway + Supabase + Haiku + GPT Live |
| **Propuesta 4 — PSTN como P1** | [propuesta-4/](propuesta-4/README.md) | **Llamada telefónica normal** + misma pila AWS/voz que P1 |
| **Propuesta 5 — PSTN on-prem** | [propuesta-5/](propuesta-5/README.md) | **Teléfono PSTN** + servidores locales (mezcla P4 × P2) |
| **Comparación** | [diferencias-propuestas.md](diferencias-propuestas.md) | Tabla side-by-side, costos y cuándo elegir |

## Documentación común

Requisitos, casos y comportamiento del agente (válidos para todas las propuestas): [docs/](docs/README.md). PDF de levantamiento: [fuente/incripcion-campo.pdf](fuente/incripcion-campo.pdf).

## Alcance de arranque

Un canal de ayuda al operador (WhatsApp o teléfono), con flujo guiado:

1. Chat cuando el canal es WhatsApp (texto, y después foto y nota de voz).
2. Llamada de voz con un agente que acompaña paso a paso (WhatsApp Calling o PSTN según la propuesta).

Casos cubiertos: primer logueo, tableta sin internet, tableta dañada o no disponible.

## Estado

Documentación inicial. Todavía no hay servicio desplegado.
