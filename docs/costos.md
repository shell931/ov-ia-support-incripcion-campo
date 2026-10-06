# Costos mensuales estimados del piloto

Estimación para 15 operadores en campo. Precios de lista consultados el 5 de octubre de 2026, en dólares, sin impuestos, sin desarrollo y sin el ambiente `dev`. Infraestructura en [infraestructura.md](infraestructura.md).

## Supuestos

| Supuesto | Valor |
| --- | --- |
| Operadores | 15 |
| Días de jornada al mes | 22 |
| Incidencias por operador por día | 2 |
| Incidencias al mes | ≈ 660 |
| Por llamada / por chat | 50 % / 50 % |
| Duración media de una llamada | 6 min |
| Minutos de voz al mes | ≈ 2.000 |
| Llamadas que entran por el número de Colombia | 25 % (≈ 500 min) |
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
| **Telefonía y WhatsApp** | | **≈ 62** |
| Número de Colombia | Alquiler (Twilio 14, Telnyx 13,50) | 14 |
| Minutos por el número de Colombia | 500 min × 0,09 (entrante Twilio) | 45 |
| Llamadas de WhatsApp iniciadas por el operador | Sin costo para la empresa | 0 |
| Mensajes de WhatsApp | 1.000 gratis por número al mes; luego 0,0008 en Colombia | 3 |
| **Total** | | **≈ 360** |

Con un cambio de ≈ 3.340 COP por dólar, son ≈ COP 1,2 millones al mes.

## Costo por minuto de llamada

| Entrada | Deepgram + LLM + TTS | Telefonía | Total aprox. |
| --- | ---: | ---: | ---: |
| Llamada de WhatsApp | 0,02 | 0 | 0,02 |
| Número de Colombia (Twilio) | 0,02 | 0,09 | 0,11 |

Los minutos SIP de LiveKit están dentro del plan hasta 5.000 al mes; después suman 0,004 por minuto.

## Variaciones

| Cambio | Efecto mensual |
| --- | --- |
| Número y minutos con Telnyx en lugar de Twilio | Menor; pedir tarifa entrante Colombia |
| Agente de voz alojado en LiveKit Cloud en lugar de ECS | ≈ −70 (5.000 minutos de agente incluidos en Ship) |
| Postgres en dos zonas y segundo NAT | ≈ +50 |
| Ambiente `dev` encendido todo el mes | ≈ +100 a +150 |
| Duplicar el volumen de llamadas | ≈ +60 (≈ +35 si todo entra por WhatsApp) |

## Fuentes

- [LiveKit Cloud pricing](https://livekit.com/pricing)
- [Deepgram pricing](https://deepgram.com/pricing)
- [Cartesia pricing](https://www.cartesia.ai/pricing)
- [WhatsApp Business Platform pricing](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing)
- [Twilio Voice Colombia](https://www.twilio.com/en-us/voice/pricing/co)
- [Telnyx Colombia numbers](https://telnyx.com/phone-numbers/colombia)
- AWS: tarifas de lista de Fargate, RDS, ElastiCache, ALB, NAT, WAF e IPv4 en us-east-1.
