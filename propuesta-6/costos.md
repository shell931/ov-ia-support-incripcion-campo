# Propuesta 6 — Costos mensuales estimados

Dos modos con el mismo código: **nube** (demo y arranque) y **local** (cuando el cliente lo pida). Arquitectura: [README.md](README.md).

## Supuestos

Los mismos de [P4](../propuesta-4/costos.md) y [P5](../propuesta-5/costos.md), para poder comparar:

| Supuesto | Valor |
| --- | --- |
| Operadores | 15 / 1.400 |
| Días de jornada al mes | 22 |
| Incidencias por operador por día | 2 |
| Medio | **100 % llamada** de 6 min |
| Minutos de voz al mes | ≈ **4.000** / ≈ **370.000** |

Precios orientativos, USD, sin impuestos ni desarrollo. Tarifas de voz tomadas de P4 (Deepgram 0,0077/min, LiveKit Ship con 5.000 min incluidos y 0,004/min de excedente). Hay que revalidarlas antes de presentar.

## Semana de demo (una vez)

| Concepto | US$ |
| --- | ---: |
| VM (2–4 vCPU) con Docker Compose, prorrateada | 5–15 |
| LiveKit Cloud | 0–50 según plan |
| Deepgram, LLM y Cartesia: unos cientos de minutos de prueba | 5–15 |
| Número telefónico | 1–5 |
| **Total** | **≈ 20–80** |

## Modo nube — 15 operadores

Igual a P4 en voz, pero **sin ECS, RDS ni Terraform**: una VM con el mismo `docker-compose.yml` que después va al datacenter.

| Concepto | Detalle | US$ / mes |
| --- | --- | ---: |
| **Infraestructura** | | **≈ 50** |
| VM 4 vCPU / 8 GB | Núcleo, Postgres, consola, voice-agent ×2 | 40 |
| Backups + dominio | Snapshots diarios | 10 |
| **Voz e IA** | | **≈ 97** |
| LiveKit Cloud (Ship) | ≈ 4.000 min dentro de los 5.000 incluidos | 50 |
| Deepgram | 4.000 × 0,0077 | 31 |
| LLM chico | ≈ 12.000 clasificaciones | 12 |
| Cartesia | Frases dinámicas; pasos pregrabados | 4 |
| **Telefonía** | Número + minutos entrantes | **≈ 15** |
| **SMS (opcional)** | Número de caso al escalar | **10** |
| **Total** | | **≈ 170–180** |

## Modo nube — 1.400 operadores

| Concepto | Detalle | US$ / mes |
| --- | --- | ---: |
| **Infraestructura** | 4 VMs para agentes + Postgres administrado | **≈ 380** |
| **Voz e IA** | | **≈ 5.370** |
| LiveKit Cloud | 50 + (370.000 − 5.000) × 0,004 | 1.510 |
| Deepgram | 370.000 × 0,0077 | 2.850 |
| LLM | ≈ 840.000 clasificaciones (cifra de P4) | 930 |
| Cartesia | | 80 |
| **Telefonía** | Minutos entrantes, tarifa por volumen | **≈ 450** |
| **SMS** | | **≈ 80** |
| **Total** | | **≈ 6.300** |

## Modo local

Es el mismo hardware y la misma operación que [P5](../propuesta-5/costos.md); no se repite el desglose.

| Escala | US$ / mes |
| --- | ---: |
| 15 operadores (1 GPU + 1 CPU, amortizados a 36 meses) | ≈ **240** |
| 1.400 operadores (6–8 GPU T4 + 3 CPU) | ≈ **2.030** |

## Lectura

| Escala | Nube | Local | Qué conviene |
| --- | ---: | ---: | --- |
| 15 operadores | ≈ 180 | ≈ 240 | **Nube.** Una GPU para ~1 llamada simultánea no se paga sola. |
| 1.400 operadores | ≈ 6.300 | ≈ 2.030 | **Local.** Ahorra ≈ 2/3: Deepgram + LiveKit Cloud por minuto dominan. |

El punto de quiebre que reporta un análisis de terceros es **7.000–10.000 min/mes** ([Meetrix](https://meetrix.io/blogs/ai-phone-agent-cost/)). Este proyecto lo pasa con unos **25–35 operadores** (≈ 264 min/mes por operador). Es orientativo.

Ese es el argumento económico de P6: **no hay que elegir hoy**. Se arranca barato en la nube y se muda cuando el volumen (o la ley) lo justifique.

## Nota sobre los costos de P4

En [propuesta-4/costos.md](../propuesta-4/costos.md), tabla de 1.400 operadores, el subtotal "Voz e IA" dice **≈ 3.250**. Las líneas de esa misma tabla suman **5.350** (1.490 + 2.850 + 930 + 80). Con eso, el total de P4 a 1.400 operadores queda cerca de **6.900**, no 4.800. Conviene corregirlo, porque cambia la comparación nube contra local en todas las propuestas.
