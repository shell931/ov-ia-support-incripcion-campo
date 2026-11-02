# Documentación común

Material que aplica **a las dos propuestas** de arquitectura (mismo producto, distinto despliegue de voz, IA y datos).

| Documento | Qué es |
| --- | --- |
| [incripcion-campo.pdf](../fuente/incripcion-campo.pdf) | Propuesta original (levantamiento de necesidad y solución). |
| [analisis.md](analisis.md) | Lectura del PDF: casos, restricciones y alcance. |
| [arquitectura-whatsapp-voip.md](arquitectura-whatsapp-voip.md) | Qué implementar y desplegar para WhatsApp y el agente de voz. |
| [analisis-agente-voz.md](analisis-agente-voz.md) | Comportamiento del agente, opciones de construcción y prueba de concepto. |

## Arquitecturas (elegir una)

| | Propuesta 1 — nube | Propuesta 2 — on-premise |
| --- | --- | --- |
| Carpeta | [../propuesta-1/](../propuesta-1/README.md) | [../propuesta-2/](../propuesta-2/README.md) |
| Resumen | LiveKit Cloud, Deepgram, Cartesia, AWS (ECS, RDS, S3) | LiveKit OSS, Whisper, Piper, LLM local, datos en el datacenter |
| Comparación | [../diferencias-propuestas.md](../diferencias-propuestas.md) | |
