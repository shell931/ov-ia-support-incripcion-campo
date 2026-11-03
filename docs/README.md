# Documentación común

Material que aplica **a las cinco propuestas** de arquitectura (mismo producto, distinto canal y despliegue).

| Documento | Qué es |
| --- | --- |
| [incripcion-campo.pdf](../fuente/incripcion-campo.pdf) | Propuesta original (levantamiento de necesidad y solución). |
| [analisis.md](analisis.md) | Lectura del PDF: casos, restricciones y alcance. |
| [arquitectura-whatsapp-voip.md](arquitectura-whatsapp-voip.md) | Qué implementar y desplegar para WhatsApp y el agente de voz. |
| [analisis-agente-voz.md](analisis-agente-voz.md) | Comportamiento del agente, opciones de construcción y prueba de concepto. |

## Arquitecturas (elegir una)

| | P1 | P2 | P3 | P4 | P5 |
| --- | --- | --- | --- | --- | --- |
| Carpeta | [../propuesta-1/](../propuesta-1/README.md) | [../propuesta-2/](../propuesta-2/README.md) | [../propuesta-3/](../propuesta-3/README.md) | [../propuesta-4/](../propuesta-4/README.md) | [../propuesta-5/](../propuesta-5/README.md) |
| Entrada | WhatsApp | WhatsApp | WhatsApp | **Teléfono PSTN** | **Teléfono PSTN** |
| Resumen | AWS + LiveKit + Deepgram | On-premise | Railway + Supabase | Como P1, sin WhatsApp | **PSTN + on-prem (P4×P2)** |
| Comparación | [../diferencias-propuestas.md](../diferencias-propuestas.md) | | | | |
