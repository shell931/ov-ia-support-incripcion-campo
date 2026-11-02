# Soporte IA — inscripción en campo

Asistente de nivel 1 para operadores de puestos de inscripción. El canal de ayuda es el celular del operador: la tableta del puesto muchas veces es justo lo que está fallando.

## Dos formas de desplegarlo

Mismo producto (WhatsApp chat + voz, árbol YAML, consola de casos). Distinto hosting de voz, IA y datos:

| | Carpeta | Idea |
| --- | --- | --- |
| **Propuesta 1 — nube** | [propuesta-1/](propuesta-1/README.md) | AWS + LiveKit Cloud + Deepgram + Cartesia |
| **Propuesta 2 — on-premise** | [propuesta-2/](propuesta-2/README.md) | LiveKit OSS + Whisper + Piper + datos en el datacenter; Meta en la nube |
| **Comparación** | [diferencias-propuestas.md](diferencias-propuestas.md) | Tabla side-by-side, costos y cuándo elegir cada una |

## Documentación común

Requisitos, casos y comportamiento del agente (válidos para ambas propuestas): [docs/](docs/README.md). PDF de levantamiento: [fuente/incripcion-campo.pdf](fuente/incripcion-campo.pdf).

## Alcance de arranque

Un solo canal, WhatsApp, con dos modos sobre el mismo flujo guiado:

1. Chat (texto, y después foto y nota de voz).
2. Llamada de voz con un agente que acompaña paso a paso.

Casos cubiertos: primer logueo, tableta sin internet, tableta dañada o no disponible.

## Estado

Documentación inicial. Todavía no hay servicio desplegado.
