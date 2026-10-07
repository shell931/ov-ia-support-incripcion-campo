# Costos mensuales estimados del piloto

Estimación para 15 operadores en campo. Precios de lista consultados el 5 de octubre de 2026, en dólares, sin impuestos, sin desarrollo y sin el ambiente `dev`. Infraestructura en [infraestructura.md](infraestructura.md).

Canal único: **WhatsApp** (chat y llamada de voz). Sin número telefónico ni trunk SIP.

## Supuestos

| Supuesto | Valor |
| --- | --- |
| Operadores | 15 |
| Días de jornada al mes | 22 |
| Incidencias por operador por día | 2 |
| Incidencias al mes | ≈ 660 |
| Por llamada de WhatsApp / por chat | 50 % / 50 % |
| Duración media de una llamada | 6 min |
| Minutos de voz al mes | ≈ 2.000 |
| Mensajes salientes por conversación de chat | ≈ 12 |

## Tabla

| Concepto | Detalle | US$ / mes |
| --- | --- | ---: |
| **AWS (us-east-1)** | | **≈ 215** |
| ECS Fargate | 2 × voice-agent (1 vCPU, 2 GB), gateway y worker (0,25 vCPU, 0,5 GB) | 90 |
| Application Load Balancer | Tráfico bajo | 22 |
| NAT Gateway | Uno, más tráfico de salida | 35 |
| RDS Postgres | db.t4g.micro, 20 GB, una zona | 15 |
| ElastiCache Redis | cache.t4g.micro | 12 |
| WAF | ACL y reglas administradas | 11 |
| IPv4 públicas | ALB y NAT | 11 |
| CloudWatch | Logs, métricas, alarmas | 10 |
| S3, CloudFront, Secrets Manager, ECR, Route 53 | | 8 |
| Cognito, SES | Dentro de la capa gratuita | 0 |
| **Voz e IA** | | **≈ 82** |
| LiveKit Cloud, plan Ship | Incluye 5.000 minutos SIP; se usan ≈ 2.000 | 50 |
| Deepgram Nova-3 streaming | 2.000 min × 0,0077 | 15 |
| LLM chico | ≈ 9.000 clasificaciones de ≈ 1.000 tokens | 10 |
| Cartesia, plan Pro | Solo frases dinámicas; los pasos van presintetizados | 7 |
| **WhatsApp** | | **≈ 3** |
| Llamadas de WhatsApp iniciadas por el operador | Sin costo para la empresa | 0 |
| Mensajes de WhatsApp | 1.000 gratis por número al mes; luego 0,0008 en Colombia | 3 |
| **Total** | | **≈ 300** |

Con un cambio de ≈ 3.340 COP por dólar, son ≈ COP 1,0 millón al mes.

## Escenario 1.400 operadores

Misma arquitectura y mismos supuestos de uso (22 días, 2 incidencias por persona y día, 50 % chat / 50 % voz, 6 min por llamada, ≈ 12 mensajes salientes por chat). Cambia el volumen, no el diagrama.

| Supuesto | 15 operadores | 1.400 operadores |
| --- | ---: | ---: |
| Incidencias al mes | ≈ 660 | ≈ 61.600 |
| Incidencias al día | ≈ 30 | ≈ 2.800 |
| Minutos de voz al mes | ≈ 2.000 | ≈ 185.000 |
| Conversaciones de chat al mes | ≈ 330 | ≈ 30.800 |
| Llamadas a la vez (jornada 8 h, promedio) | ≈ 1 | ≈ 15–20 (pico ≈ 40–50) |

| Concepto | Detalle | US$ / mes |
| --- | --- | ---: |
| **AWS (us-east-1)** | | **≈ 1.080** |
| ECS Fargate | ≈ 20 × voice-agent (1 vCPU, 2 GB) en promedio, autoescalado a pico ≈ 45; gateway y worker ampliados | 810 |
| Application Load Balancer | Más unidades de carga | 35 |
| NAT Gateway | Uno, más tráfico de salida a LiveKit, Deepgram y TTS | 90 |
| RDS Postgres | db.t4g.small, más almacenamiento | 40 |
| ElastiCache Redis | cache.t4g.small | 25 |
| WAF | ACL, reglas y más requests | 20 |
| IPv4 públicas | ALB y NAT | 11 |
| CloudWatch | Más logs, métricas y alarmas | 30 |
| S3, CloudFront, Secrets Manager, ECR, Route 53 | | 15 |
| Cognito, SES | SES ya no cabe entero en la capa gratuita | 5 |
| **Voz e IA** | | **≈ 3.200** |
| LiveKit Cloud, plan Ship | 5.000 min SIP incluidos; ≈ 185.000 usados; excedente × 0,004 | 770 |
| Deepgram Nova-3 streaming | 185.000 min × 0,0077 | 1.425 |
| LLM chico | ≈ 840.000 clasificaciones de ≈ 1.000 tokens | 930 |
| Cartesia | Pasos fijos en S3; más frases dinámicas (número de caso) | 80 |
| **WhatsApp** | | **≈ 295** |
| Llamadas de WhatsApp iniciadas por el operador | Sin costo para la empresa | 0 |
| Mensajes de WhatsApp | 1.000 gratis; luego ≈ 369.000 × 0,0008 en Colombia | 295 |
| **Total** | | **≈ 4.600** |

Con un cambio de ≈ 3.340 COP por dólar, son ≈ COP 15 millones al mes.

El minuto de voz deja de costar solo 0,02: el SIP de LiveKit ya va fuera del cupo de 5.000 min y suma 0,004. Deepgram + LLM + TTS siguen en ≈ 0,02. **≈ 0,024 US$ / min** de llamada.

Alojar el `voice-agent` en LiveKit Cloud **no** ahorra los ≈ 70 US$ de este escenario: los minutos de agente también se pagan por encima de 5.000. Lo que sí hace falta es autoescalado; dos tareas Fargate no alcanzan.

Si el agente resuelve cerca de la mitad, la mesa recibe del orden de **1.400 casos al día**. Eso no cambia el software; cambia cuánta gente hace falta para devolver la llamada.

El límite de WhatsApp de 2.000 destinatarios diarios sigue cubriendo 1.400 operadores.

## Costo por minuto de llamada de WhatsApp

| Componente | US$ / min aprox. |
| --- | ---: |
| Deepgram + LLM + TTS | 0,02 |
| Telefonía (Meta / LiveKit SIP) | 0 |
| **Total** | **0,02** |

Los minutos SIP de LiveKit están dentro del plan Ship hasta 5.000 al mes; después suman 0,004 por minuto.

## Variaciones

| Cambio | Efecto mensual |
| --- | --- |
| Agente de voz alojado en LiveKit Cloud en lugar de ECS | ≈ −70 (5.000 minutos de agente incluidos en Ship) |
| Postgres en dos zonas y segundo NAT | ≈ +50 |
| Ambiente `dev` encendido todo el mes | ≈ +100 a +150 |
| Duplicar el volumen de llamadas | ≈ +35 |

## Fuentes

- [LiveKit Cloud pricing](https://livekit.com/pricing)
- [Deepgram pricing](https://deepgram.com/pricing)
- [Cartesia pricing](https://www.cartesia.ai/pricing)
- [WhatsApp Business Platform pricing](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing)
- AWS: tarifas de lista de Fargate, RDS, ElastiCache, ALB, NAT, WAF e IPv4 en us-east-1.
