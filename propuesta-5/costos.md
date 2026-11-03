# Propuesta 5 — Costos mensuales estimados

Entrada **PSTN** (como [propuesta 4](../propuesta-4/costos.md)) + **voz e IA on-premise** (como [propuesta 2](../propuesta-2/README.md#costos-mensuales)). Sin WhatsApp.

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

Precios orientativos en USD, sin impuestos, sin desarrollo y **sin el pico de compra del año 1** (hardware amortizado a 36 meses). Sin sueldo de quien opera el datacenter. Si ya hay rack y energía, esa línea baja.

## 15 operadores

| Concepto | Detalle | US$ / mes |
| --- | ---: | ---: |
| **On-premise** | | **≈ 215** |
| 1 servidor GPU | T4 / L4 / RTX equivalente, amortizado 36 meses | 50 |
| 1 servidor CPU | LiveKit, voice-agent, Postgres, Redis, MinIO, consola | 55 |
| Energía y rack | Si el datacenter ya existe, sobre todo energía | 40 |
| Respaldo y recambio | Discos, snapshots | 20 |
| Mantenimiento software | Parches LiveKit, modelos, SO (sin contar persona) | 50 |
| **Telefonía PSTN** | | **≈ 15** |
| Número DID | Renta mensual | 3 |
| Minutos entrantes | 4.000 × ~0,003 (promedio conservador) | 12 |
| **SMS (opcional)** | Número de caso al escalar (~330 SMS) | 10 |
| **Total** | Sin SMS ≈ 230; con SMS ≈ **240** | **≈ 230–240** |

Frente a ≈ 310 de la propuesta 4 (nube) y ≈ 220 de la propuesta 2 (WhatsApp on-prem). En 15 personas el ahorro vs P4 es moderado; el motivo de P5 no es ese número, es no pagar STT/SIP cloud cuando crezca y no mandar transcripciones a terceros, **sin depender de Meta**.

## 1.400 operadores

| Concepto | Detalle | US$ / mes |
| --- | ---: | ---: |
| **On-premise** | | **≈ 1.500** |
| 6–8 GPU T4 (o 4 L4) | Pico ≈ 40–50 llamadas; amortizado 36 meses | 550 |
| 3 servidores CPU | LiveKit, apps, Postgres/Redis/MinIO | 180 |
| Energía | GPUs + CPU, 24×7 | 280 |
| Red, backup, recambio | | 140 |
| Mantenimiento software | | 350 |
| **Telefonía PSTN** | | **≈ 450** |
| Número / trunks | | 20 |
| Minutos entrantes | 370.000 × ~0,0012 (volumen; negociable) | 430 |
| **SMS** | Escalamientos | 80 |
| **Total** | ≈ COP 6,8 millones a 3.340 COP/US$ | **≈ 2.030** |

Frente a ≈ 4.800 de la propuesta 4 en nube. El minuto de voz **deja de tener tarifa de Deepgram y de SIP LiveKit Cloud**. Queda el carrier PSTN (que la propuesta 2 no paga porque usa WhatsApp Calling sin costo de minutos empresa).

## Lectura rápida

| Escala | P2 | P4 | **P5** |
| ---: | ---: | ---: | ---: |
| 15 | ≈ 220 | ≈ 310 | ≈ **240** |
| 1.400 | ≈ 1.800 | ≈ 4.800 | ≈ **2.030** |
