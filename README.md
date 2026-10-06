# Soporte IA — inscripción en campo

Asistente de nivel 1 para operadores de puestos de inscripción. El canal de ayuda es el celular del operador: la tableta del puesto muchas veces es justo lo que está fallando.

## Documentación

| Documento | Qué es |
| --- | --- |
| [docs/fuente/incripcion-campo.pdf](docs/fuente/incripcion-campo.pdf) | Propuesta original (levantamiento de necesidad y solución). |
| [docs/analisis.md](docs/analisis.md) | Lectura del PDF: casos, restricciones y alcance. |
| [docs/arquitectura-whatsapp-voip.md](docs/arquitectura-whatsapp-voip.md) | Qué implementar y desplegar para WhatsApp y el agente de voz. |
| [docs/analisis-agente-voz.md](docs/analisis-agente-voz.md) | Cómo se comporta el agente de voz, opciones de construcción y prueba de concepto. |
| [docs/infraestructura.md](docs/infraestructura.md) | Diagrama de infraestructura, consola de casos y dimensionamiento. |
| [docs/costos.md](docs/costos.md) | Costo mensual estimado del piloto para 15 operadores. |
| [docs/tiempos.md](docs/tiempos.md) | Calendario de implementación para una persona (PoC a piloto en campo) e historias de usuario. |

## Alcance de arranque

Un solo canal, WhatsApp, con dos modos sobre el mismo flujo guiado:

1. Chat (texto, y después foto y nota de voz).
2. Llamada de voz con un agente que acompaña paso a paso.

Casos cubiertos: primer logueo, tableta sin internet, tableta dañada o no disponible.

## Estado

Documentación inicial. Todavía no hay servicio desplegado.
