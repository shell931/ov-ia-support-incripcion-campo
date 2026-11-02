# Documentación común

Material que aplica **a las tres propuestas** de arquitectura (mismo producto, distinto despliegue de voz, IA y datos).

| Documento | Qué es |
| --- | --- |
| [incripcion-campo.pdf](../fuente/incripcion-campo.pdf) | Propuesta original (levantamiento de necesidad y solución). |
| [analisis.md](analisis.md) | Lectura del PDF: casos, restricciones y alcance. |
| [arquitectura-whatsapp-voip.md](arquitectura-whatsapp-voip.md) | Qué implementar y desplegar para WhatsApp y el agente de voz. |
| [analisis-agente-voz.md](analisis-agente-voz.md) | Comportamiento del agente, opciones de construcción y prueba de concepto. |

## Arquitecturas (elegir una)

| | P1 — AWS | P2 — on-premise | P3 — ligero |
| --- | --- | --- | --- |
| Carpeta | [../propuesta-1/](../propuesta-1/README.md) | [../propuesta-2/](../propuesta-2/README.md) | [../propuesta-3/](../propuesta-3/README.md) |
| Resumen | LiveKit Cloud, Deepgram, Cartesia | Whisper, Piper, datacenter | Railway, Supabase, Haiku, GPT Live, WhatsApp |
| Comparación | [../diferencias-propuestas.md](../diferencias-propuestas.md) | | |
