# Tiempos de implementación del piloto

Estimación en **días hábiles** para el alcance documentado: WhatsApp (chat y llamada), tres flujos, consola de casos e infraestructura en AWS. Equipo de **2 ingenieros**; procesos del cliente aprueba los textos de cada paso en paralelo.

Fuera de este calendario: foto del cargador, nota de voz de WhatsApp, reenvío automático de credenciales, inventario, tablero por municipio y guía offline en la tableta.

El camino crítico no es el código: **verificar el número de WhatsApp y habilitar llamadas** (Meta). Hay que arrancarlo el día 1; suele tardar **5 a 15 días**, a veces más.

Comportamiento del agente en [analisis-agente-voz.md](analisis-agente-voz.md). Piezas en [infraestructura.md](infraestructura.md). Costos en [costos.md](costos.md).

## Fases

| Fase | Días | Qué queda listo |
| --- | ---: | --- |
| **0. Arranque** | 1–2 | Cuentas (AWS, Meta, LiveKit, Deepgram, Cartesia, LLM), dos ambientes, textos del flujo “sin internet”. |
| **1. Prueba de concepto** | 3–10 | Un flujo en simulador y agente de voz en navegador. Al cierre: llamada WhatsApp de “sin internet” con caso y devolución de la mesa. |
| **2. Chat de los 3 casos** | 11–20 | Webhook, worker, botones, sesión Redis, ticket al escalar. |
| **3. Voz de los 3 casos** | 14–28 | Mismo árbol, audio en S3, DTMF (cédula), espera activa, prueba con ruido de puesto. |
| **4. Consola y alertas** | 18–28 | Cola, detalle, tomar caso, Cognito, correo SES, indicadores básicos. |
| **5. Infra y endurecimiento** | 1–28 | Terraform y ECS en paralelo. Enmascarado, latencia, set de 30–50 llamadas. |
| **6. Piloto en campo** | 29–40 | Unos 15 operadores, ajuste de textos y audios, medición contra 40–60 % resueltas sin persona. |

**Total al criterio de hecho del piloto: ~40 días hábiles (unas 8 semanas).** La prueba de concepto se puede mostrar en **10 días**.

## Piezas (pueden solaparse)

| Pieza | Días | Notas |
| --- | ---: | --- |
| YAML + motor de flujos (3 árboles, intentos, escalar, retoma) | 8 | Base compartida de chat y voz. |
| `gateway` + SQS + `worker` WhatsApp | 8 | Chat de punta a punta de conectividad primero. |
| `voice-agent` LiveKit + Deepgram + Cartesia | 10 | Después del motor. DTMF y espera activa entran aquí. |
| Pipeline de audios a S3 | 3 | Cada cambio de texto vuelve a sintetizar ese paso. |
| Redis sesión + Postgres casos | 4 | Arranca con el motor. |
| Consola CloudFront + Cognito | 8 | Bandeja de casos, no una mesa de ayuda completa. |
| Terraform, CI/CD, `dev` y `piloto` | 10 | En paralelo desde el día 1. |
| Pruebas con ruido + circuito mesa | 5 | Incluye las 10 llamadas de la PoC y el set mayor. |
| Acompañamiento en campo | 10 | No es desarrollo nuevo; es ajuste. |

## Hitos

| Día | Qué se puede mostrar |
| ---: | --- |
| **10** | Demo grabada, tabla de latencia, un caso que la mesa recibe y devuelve. |
| **20** | Un operador resuelve “sin internet” por chat. |
| **28** | Lo mismo por llamada, más logueo y tableta, consola usable. |
| **40** | 15 operadores en jornada; se mide contra la meta. |

## Riesgos que alargan el calendario

- Meta no habilita calling a tiempo.
- Nadie aprueba los textos de los pasos (y por tanto los audios de S3).
- No hay cifras de puestos ni de pico, y hay que redimensionar LiveKit y Deepgram a mitad de camino.
