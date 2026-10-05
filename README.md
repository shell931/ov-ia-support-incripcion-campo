# Soporte IA — inscripción en campo

Asistente de nivel 1 para operadores de puestos de inscripción. El canal de ayuda es el celular del operador: la tableta del puesto muchas veces es justo lo que está fallando.

## Documentación

| Documento | Qué es |
| --- | --- |
| [docs/fuente/incripcion-campo.pdf](docs/fuente/incripcion-campo.pdf) | Propuesta original (levantamiento de necesidad y solución). |
| [docs/analisis.md](docs/analisis.md) | Lectura del PDF: casos, restricciones y alcance. |
| [docs/arquitectura-whatsapp-voip.md](docs/arquitectura-whatsapp-voip.md) | Qué implementar y desplegar para WhatsApp y el agente de voz. |

## Alcance de arranque

Dos canales sobre el mismo flujo guiado:

1. WhatsApp (texto, y después foto y nota de voz).
2. Llamada VoIP con un agente de voz que acompaña paso a paso.

Casos cubiertos: primer logueo, tableta sin internet, tableta dañada o no disponible.

## Estado

Documentación inicial. Todavía no hay servicio desplegado.
