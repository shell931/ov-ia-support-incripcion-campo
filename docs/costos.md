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
