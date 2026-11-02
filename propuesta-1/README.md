# Propuesta 1 — nube (AWS + SaaS de voz)

Asistente de WhatsApp (chat y llamada), tres flujos en YAML, consola de casos, **sin transferencia en vivo**. La voz y la IA usan **LiveKit Cloud**, **Deepgram**, **Cartesia** y un LLM en la nube; la aplicación corre en **AWS** (ECS Fargate, RDS, Redis, S3).

Documentación común del producto: [../docs/](../docs/README.md). Comparación con la propuesta 2: [../diferencias-propuestas.md](../diferencias-propuestas.md).

## Documentos de esta propuesta

| Documento | Qué es |
| --- | --- |
| [infraestructura.md](infraestructura.md) | Diagrama, piezas, consola, dimensionamiento y despliegue. |
| [costos.md](costos.md) | Costo mensual estimado (15 operadores y escenario de 1.400). |
| [tiempos.md](tiempos.md) | Calendario para una persona (~70 días hábiles). |

## Diagramas

| Imagen | Uso |
| --- | --- |
| [diagramas/infraestructura.png](diagramas/infraestructura.png) | Flujo paso a paso + tablas Piezas y costos. |
| [diagramas/infraestructura-diagrama.png](diagramas/infraestructura-diagrama.png) | Solo el diagrama. |
| [diagramas/arquitectura-voz-tecnologias.png](diagramas/arquitectura-voz-tecnologias.png) | Pipeline de voz (referencia en análisis del agente). |
| [diagramas/despliegue.png](diagramas/despliegue.png) | CI/CD y ambientes. |

Regenerar el diagrama principal: `python3 propuesta-1/diagramas/generate_infraestructura.py`.
