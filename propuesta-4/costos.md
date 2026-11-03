# Propuesta 4 — Costos mensuales estimados

Misma base AWS y voz que [propuesta 1](../propuesta-1/costos.md), pero **canal PSTN** (sin WhatsApp). Infraestructura: [README.md](README.md).

Canal único en el piloto: **llamada telefónica** al número de soporte. Sin chat.

## Supuestos

| Supuesto | Valor |
| --- | --- |
| Operadores | 15 (tabla 1) / 1.400 (tabla 2) |
| Días de jornada al mes | 22 |
| Incidencias por operador por día | 2 |
| Incidencias al mes | ≈ 660 / ≈ 61.600 |
| Medio | **100 % llamada telefónica** |
| Duración media | 6 min |
| Minutos de voz al mes | ≈ **4.000** / ≈ **370.000** |

Precios orientativos, USD, sin impuestos ni desarrollo. PSTN: rango típico inbound Colombia vía Twilio/Telnyx; revisar contrato local.

## 15 operadores

| Concepto | Detalle | US$ / mes |
| --- | --- | ---: |
| **AWS (us-east-1)** | | **≈ 200** |
| ECS Fargate | 2 × voice-agent; gateway (API consola); **sin worker WhatsApp** | 75 |
| ALB, NAT, RDS, Redis, WAF, IPv4, CloudWatch, S3, CloudFront, etc. | Igual orden que P1 | 125 |
| **Voz e IA** | | **≈ 97** |
| LiveKit Cloud, plan Ship | ≈ 4.000 min SIP (dentro de 5.000 incluidos) | 50 |
| Deepgram Nova-3 | 4.000 × 0,0077 | 31 |
| LLM chico | ≈ 12.000 clasificaciones | 12 |
| Cartesia Pro | Frases dinámicas; pasos en S3 | 4 |
| **Telefonía PSTN** | | **≈ 15** |
| Número DID | Renta mensual | 3 |
| Minutos entrantes | 4.000 × ~0,003 (promedio conservador) | 12 |
| **SMS (opcional)** | Número de caso al escalar (~330 SMS) | 10 |
| **Total** | Sin SMS ≈ 312; con SMS ≈ **322** | **≈ 310–320** |

Comparable a P1 (~300): sube minutos de voz (100 % llamadas) y PSTN; baja WhatsApp y se quita worker de chat.

## 1.400 operadores

| Concepto | Detalle | US$ / mes |
| --- | --- | ---: |
| **AWS (us-east-1)** | | **≈ 1.050** |
| ECS Fargate | Autoescalado voice-agent (~20 tareas media, pico 45) | 780 |
| Resto AWS | RDS small, Redis, NAT, ALB, etc. | 270 |
| **Voz e IA** | | **≈ 3.250** |
| LiveKit Ship | ≈ 370.000 min; excedente × 0,004 | 1.490 |
| Deepgram | 370.000 × 0,0077 | 2.850 |
| LLM | ≈ 840.000 clasificaciones | 930 |
| Cartesia | | 80 |
| **Telefonía PSTN** | | **≈ 450** |
| Número / trunks | | 20 |
| Minutos entrantes | 370.000 × ~0,0012 (volumen; negociable) | 430 |
| **SMS** | Escalamientos | 80 |
| **Total** | | **≈ 4.800** |

En escala alta, **Deepgram + minutos LiveKit** dominan igual que P1; PSTN suma una fracción si se negocia tarifa.

## Costo por minuto de llamada (aprox.)

| Componente | US$ / min |
| --- | ---: |
| Deepgram + LLM + TTS | 0,02 |
| LiveKit SIP (tras cupo) | 0–0,004 |
| PSTN inbound | 0,001–0,02 (según proveedor) |
| **Total** | **≈ 0,02–0,04** |

## Fuentes

- [LiveKit Cloud pricing](https://livekit.com/pricing)
- [Deepgram pricing](https://deepgram.com/pricing)
- [Cartesia pricing](https://www.cartesia.ai/pricing)
- Twilio / Telnyx / Zernio: tarifas de número y minuto entrante Colombia.
