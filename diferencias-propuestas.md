# Diferencias entre propuesta 1 y propuesta 2

Las dos opciones resuelven **el mismo problema de negocio**: operadores de inscripción en campo que contactan por **WhatsApp** (texto o llamada), siguen un **árbol YAML** (primer logueo, tableta sin internet, tableta dañada), y si no se resuelve se **escala a la mesa** con número de caso — **sin pasar la llamada en vivo**.

Lo que cambia es **dónde corre el audio, el STT/TTS, el LLM y los datos del caso**.

## Dónde está cada cosa en el repo

| Contenido | Propuesta 1 | Propuesta 2 | Común |
| --- | --- | --- | --- |
| Carpeta | [propuesta-1/](propuesta-1/README.md) | [propuesta-2/](propuesta-2/README.md) | [docs/](docs/README.md) |
| Infra y diagrama principal | [propuesta-1/infraestructura.md](propuesta-1/infraestructura.md) | [propuesta-2/README.md](propuesta-2/README.md) | — |
| Costos detallados | [propuesta-1/costos.md](propuesta-1/costos.md) | Tablas en propuesta-2 | Mismos supuestos de uso |
| Calendario (1 dev) | [propuesta-1/tiempos.md](propuesta-1/tiempos.md) | ~85–90 días (en propuesta-2) | — |
| PDF, casos, agente | — | — | [docs/analisis.md](docs/analisis.md), [docs/analisis-agente-voz.md](docs/analisis-agente-voz.md) |

## Comparación técnica

| Tema | Propuesta 1 (nube) | Propuesta 2 (on-premise) |
| --- | --- | --- |
| **Canal WhatsApp** | Meta Cloud API (nube) | Igual — Meta sigue en la nube |
| **Procedimiento** | Motor YAML; LLM solo clasifica (sí / no / persona) | Igual |
| **Salas y SIP de llamada** | LiveKit **Cloud** | LiveKit **open source** en datacenter |
| **STT** | Deepgram (por minuto) | Faster-Whisper en **GPU** propia |
| **TTS** | Cartesia + audios en **S3** | Piper + **MinIO** |
| **Apps (gateway, worker, voice-agent)** | **ECS Fargate** (AWS) | Servidores CPU en el cliente |
| **Sesión y casos** | ElastiCache Redis + **RDS Postgres** + S3 | Redis + Postgres + MinIO en red del cliente |
| **Cola de chat** | SQS | Redis o RabbitMQ |
| **Consola de mesa** | CloudFront + Cognito + mismo Postgres | Consola en el datacenter |
| **Región / latencia** | `us-east-1` (cerca de proveedores de voz) | Audio y datos no salen del cliente (salvo Meta) |

## Costos mensuales (mismos supuestos)

22 días hábiles, 2 incidencias por operador y día, 50 % chat / 50 % voz, 6 min por llamada. Sin impuestos ni desarrollo.

| Escala | Propuesta 1 | Propuesta 2 |
| ---: | ---: | ---: |
| 15 operadores | ≈ **300 US$** | ≈ **220 US$** |
| 1.400 operadores | ≈ **4.600 US$** | ≈ **1.800 US$** |

En 15 operadores el ahorro de la propuesta 2 es modesto si hay que comprar GPU; el beneficio fuerte aparece con **volumen** (minutos de Deepgram y SIP LiveKit Cloud) y con **datos en sitio**.

Detalle de líneas: [propuesta-1/costos.md](propuesta-1/costos.md) y sección de costos en [propuesta-2/README.md](propuesta-2/README.md).

## Tiempo de implementación (una persona)

| | Propuesta 1 | Propuesta 2 |
| --- | ---: | ---: |
| Hasta piloto en campo | **~70 días hábiles** | **~85–90 días hábiles** |

La 2 suma operación de LiveKit propio, GPU, Whisper y despliegue on-premise. Calendario desglosado de la 1: [propuesta-1/tiempos.md](propuesta-1/tiempos.md).

## Cuándo inclinarse por cada una

**Propuesta 1** — Arrancar rápido, equipo pequeño, volumen piloto bajo, aceptar factura variable por minutos de voz y datos en AWS (con enmascarado y retención acotada).

**Propuesta 2** — Muchos operadores, costo por minuto insostenible, política de **no enviar transcripciones** a terceros, o requisito de **datos de caso en red propia**. A cambio: compra/amortización de GPU, operación de SIP y modelos.

## Qué no cambia entre propuestas

- Tres casos YAML, teclado DTMF si falla el reconocimiento, número de caso por chat al escalar.
- Fuera del piloto en ambas: foto del cargador, nota de voz, reenvío automático de credenciales, inventario, guía offline en tableta.
