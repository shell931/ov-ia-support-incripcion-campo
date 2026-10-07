# Propuesta 2 — voz e IA on-premise

Misma solución de negocio que la [propuesta 1](../docs/infraestructura.md): WhatsApp (chat y llamada), tres flujos en YAML, sin transferencia en vivo, consola de casos.

Cambia **dónde corre la inteligencia**. Meta se queda en la nube (no hay alternativa). LiveKit, el STT, el TTS, el LLM chico y los datos pasan al **datacenter del cliente**.

Imagen (diagrama + piezas + costos): [arquitectura.png](arquitectura.png). Solo el diagrama: [arquitectura-diagrama.png](arquitectura-diagrama.png). Regenerar: `python3 propuesta-2/generate_arquitectura.py`.

## Qué es esta arquitectura

Dos recintos, no dos productos.

**Nube (solo el canal).** El operador usa WhatsApp. Meta entrega el chat por webhook y la llamada por SIP. No interpretan, no guardan el caso, no hablan el procedimiento.

**On-premise (todo lo demás).** Un LiveKit propio termina el SIP. Un `voice-agent` orquesta la llamada. Faster-Whisper (GPU) pasa voz a texto. El motor YAML decide el paso. Piper habla. El chat entra por el mismo motor. Redis, Postgres y MinIO quedan en la red del cliente.

Sigue siendo un toma y dame: texto → sí/no/persona → id de paso → audio o mensaje. El LLM no redacta.

## Dónde va cada pieza

| Pieza | Dónde | Qué es | Por qué así |
| --- | --- | --- | --- |
| Celular del operador | Campo | WhatsApp: escribe o llama. | La tableta del puesto es lo que falla. |
| Meta WhatsApp Cloud API | **Nube** | Recibe chat y llamada; webhook HTTPS y SIP hacia el datacenter. | WhatsApp no se hospeda. Sin esto no hay canal. |
| Reverse proxy / firewall | **On-premise (DMZ)** | HTTPS del webhook y SIP de Meta hacia adentro. | Meta tiene que alcanzar el datacenter; el resto no se publica. |
| LiveKit (open source) | **On-premise** | Termina el SIP, salas, mezcla, ruido, despacha al agente. | Sustituye LiveKit Cloud y el cobro por minuto SIP. |
| `gateway` + cola + `worker` | **On-premise** | Webhook 200, cola, conversación de chat, casos. | Igual que la propuesta 1; SQS se vuelve Redis o RabbitMQ. |
| `voice-agent` | **On-premise** | LiveKit Agents: escucha, clasifica, habla, DTMF, caso. | Misma orquestación; ya no corre en Fargate ni en LiveKit Cloud. |
| Motor de flujos (YAML) | **On-premise** | Árbol de logueo, tableta sin internet y tableta dañada. | Un árbol para chat y voz. No depende de la nube. |
| Faster-Whisper (STT) | **On-premise, GPU** | Voz a texto en streaming. | Sustituye Deepgram. En 15 operadores 1 GPU; en 1.400, varias para el pico. |
| LLM chico local | **On-premise, CPU** | Sí / no / no entendí / persona. No escribe pasos. | Sustituye Haiku/GPT-mini. No hace falta GPU para clasificar. |
| Piper (TTS) | **On-premise, CPU** | Voz del agente. Pasos fijos se presintetizan a MinIO. | Sustituye Cartesia. GPU innecesaria si los pasos ya están grabados. |
| Redis | **On-premise** | Sesión: teléfono, caso, paso, intentos. | Retomar chat o voz. |
| Postgres | **On-premise** | Casos, historial enmascarado, métricas. | Una base para agente y consola. |
| MinIO (u object storage local) | **On-premise** | Fotos y audios de pasos. | Equivalente a S3, sin salir de la red. |
| Consola de casos | **On-premise** | Bandeja de la mesa, login local. | Cognito/CloudFront no aplican. |
| Correo de alertas | **On-premise** o correo que ya tengan | Aviso de caso alto. | Sustituye SES. |

## Por qué on-premise aquí (y no en todo)

- **STT y TTS por minuto** es lo que infla el escenario de 1.400 en la propuesta 1 (~US$ 1.425 de Deepgram + SIP de LiveKit). En casa se paga hardware, no cada minuto.
- **Datos de la llamada** (transcripción, cédula enmascarada, sesión) no salen a Deepgram, Cartesia ni LiveKit Cloud. Meta sigue viendo el audio de WhatsApp: eso no se puede evitar.
- **GPU sí**, pero solo para Whisper en tiempo real. El clasificador y Piper van en CPU. No hace falta un cluster de entrenamiento.
- **No es más barato en 15 operadores** si hay que comprar GPU de cero y dejarla ociosa. **Sí lo es en 1.400**, frente a ~US$ 4.600/mes en nube.

## Qué se necesita en el datacenter

| Escala | Cómputo | Red |
| --- | --- | --- |
| 15 operadores (~1 llamada a la vez) | 1 servidor GPU (T4, L4 o RTX 4060 Ti / 4070) + 1 servidor CPU (LiveKit, apps, Postgres, Redis) | IP pública o NAT con puertos SIP/HTTPS hacia Meta |
| 1.400 operadores (pico ~40–50 llamadas) | 6–8 GPU T4 (o menos L4) para Whisper + 3 servidores CPU (LiveKit, apps, datos) | Lo mismo, con más ancho de banda de audio |

Si el reconocimiento falla dos veces, el agente pasa a teclado (`1` sí, `2` no, `0` persona), igual que en la propuesta 1: el puesto es ruidoso.

## Costos mensuales

Mismos supuestos de uso que [docs/costos.md](../docs/costos.md): 22 días, 2 incidencias por persona y día, 50 % chat / 50 % voz, 6 min por llamada. **Sin impuestos, sin sueldo de quien opera el datacenter, sin el pico de compra del año 1** (abajo está el equivalente mensual a 36 meses).

Si ya tienen rack y energía, la línea de energía/rack baja.

### 15 operadores

| Concepto | Detalle | US$ / mes |
| --- | ---: | ---: |
| **On-premise** | | **≈ 215** |
| 1 servidor GPU | T4 / L4 / RTX equivalente, amortizado 36 meses | 50 |
| 1 servidor CPU | LiveKit, gateway, worker, Postgres, Redis, MinIO, consola | 55 |
| Energía y rack | Si el datacenter ya existe, sobre todo energía | 40 |
| Respaldo y recambio | Discos, snapshots | 20 |
| Mantenimiento software | Parches LiveKit, modelos, SO (sin contar persona) | 50 |
| **WhatsApp (nube)** | | **≈ 3** |
| Llamadas iniciadas por el operador | Sin costo empresa | 0 |
| Mensajes | 1.000 gratis; luego 0,0008 en Colombia | 3 |
| **Total** | ≈ COP 0,7 millón a 3.340 COP/US$ | **≈ 220** |

Frente a ≈ 300 US$ de la propuesta 1. En 15 personas el ahorro es chico; el motivo de esta propuesta no es ese número, es no pagar STT por minuto cuando crezca y no mandar transcripciones a terceros.

### 1.400 operadores

| Concepto | Detalle | US$ / mes |
| --- | ---: | ---: |
| **On-premise** | | **≈ 1.500** |
| 6–8 GPU T4 (o 4 L4) | Pico ≈ 40–50 llamadas; amortizado 36 meses | 550 |
| 3 servidores CPU | LiveKit, apps, Postgres/Redis/MinIO | 180 |
| Energía | GPUs + CPU, 24×7 | 280 |
| Red, backup, recambio | | 140 |
| Mantenimiento software | | 350 |
| **WhatsApp (nube)** | | **≈ 295** |
| Llamadas iniciadas por el operador | Sin costo empresa | 0 |
| Mensajes | ≈ 369.000 × 0,0008 | 295 |
| **Total** | ≈ COP 6 millones a 3.340 COP/US$ | **≈ 1.800** |

Frente a ≈ 4.600 US$ de la propuesta 1 en nube. El minuto de voz **deja de tener tarifa de Deepgram y de SIP LiveKit Cloud**. WhatsApp no se recorta.

## Frente a la propuesta 1

| | Propuesta 1 (nube) | Propuesta 2 (esta) |
| --- | --- | --- |
| Canal | WhatsApp, Meta | Igual |
| Procedimiento | YAML, LLM solo clasifica | Igual |
| STT | Deepgram | Faster-Whisper en GPU propia |
| TTS | Cartesia + S3 | Piper + MinIO |
| SIP / salas | LiveKit Cloud | LiveKit en el datacenter |
| Datos de caso | AWS us-east-1 | Red del cliente |
| 15 operadores / mes | ≈ 300 US$ | ≈ 220 US$ |
| 1.400 operadores / mes | ≈ 4.600 US$ | ≈ 1.800 US$ |
| Tiempo de armar (1 persona) | ~70 días | **~85–90 días** (LiveKit propio, GPU, Whisper) |
| Riesgo | Factura que crece con los minutos | Operar GPU, SIP y modelos; compra inicial |

## Qué no entra

Igual que la propuesta 1: foto del cargador, nota de voz, reenvío de credenciales, inventario, guía offline. Tampoco un LLM voz-a-voz grande: sube GPU y suelta el control del paso.
