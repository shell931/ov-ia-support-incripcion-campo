# Propuesta 6 — Tiempos de implementación

Días hábiles, **una persona**. Tres tramos independientes: **demo**, **piloto en modo nube** y **mudanza a local**.

## Tramo 1 — Demo (5 días)

El objetivo es mostrar los tres casos por llamada sin fallar delante del cliente, no tener el producto completo.

| Día | Qué queda listo |
| ---: | --- |
| **1** | Cuentas (LiveKit Cloud, Deepgram, LLM). `docker-compose.yml` con núcleo + Postgres en una VM. Número activo y una llamada que llega al `voice-agent`. **Arranca el trámite del número colombiano.** |
| **2** | Motor YAML y flujo **"sin internet"** completo por voz, con sesión por número. **Prueba con ruido de fondo y acento colombiano**: si la transcripción falla, hay tiempo de cambiar. |
| **3** | Flujos **"primer logueo"** y **"tableta no enciende"**. Cédula por teclado, espera activa y `create_case()` con número de caso dictado. |
| **4** | Consola mínima: cola, detalle (pasos intentados, transcripción enmascarada), tomar caso. **Video de respaldo grabado.** |
| **5** | 10 llamadas de prueba, ajuste de latencia y de textos, ensayo del guion de la demo. |

Antes de escribir código se escribe el **guion de la demo**: los tres recorridos exactos (qué dice el operador y qué responde el agente). Se construye para ese guion.

## Tramo 2 — De la demo al piloto en modo nube (~40–45 días más)

Se apoya en lo que ya está hecho; no se rehace nada.

| Fase | Días | Qué queda |
| --- | ---: | --- |
| Robustez de voz | 6 | Espera activa con tope por paso, rellamada que retoma el caso, teclado ante dos fallas. |
| Audios pregrabados por paso | 3 | Cada cambio de texto vuelve a sintetizar ese paso. |
| Consola completa | 6 | Login por persona, rol Dirección de Censo, alertas por correo, indicadores básicos. |
| SMS con número de caso + número colombiano | 3 | Depende del trámite iniciado el día 1. |
| CI/CD y ambientes `dev` / `piloto` | 4 | Mismo `docker-compose.yml`, distinta configuración. |
| Endurecimiento | 8 | Enmascarado en logs, retención, **set de regresión de 30–50 llamadas** con ruido. |
| Piloto en campo | 10 | ~15 operadores; se mide contra la meta de 40–60 % resuelto sin persona. |
| **Total** | **~40** | **Piloto al día ~45–50** contando la demo. |

Frente a P4 (~60–65 días) se ahorra porque no hay Terraform, ECS ni RDS: la nube es una VM con Docker Compose.

## Tramo 3 — Mudanza a local (~15–20 días, cuando se pida)

**Requisito previo que no es código: hardware listo** (GPU para Whisper, servidores CPU, red con SIP hacia el operador telefónico). Si la mudanza es urgente por datos, este es el camino crítico.

| Fase | Días | Qué queda |
| --- | ---: | --- |
| LiveKit OSS + SIP | 5 | Servidor LiveKit y SIP en el datacenter; troncal del operador colombiano apuntando adentro; firewall (DMZ). |
| Faster-Whisper + Piper como servidores | 5 | Contenedores de inferencia conectados por el conector compatible con OpenAI. Voz en español elegida y probada. |
| LLM local | 2 | Ollama o vLLM con un modelo chico; la clasificación es una tarea simple. |
| Regresión y ajuste | 4 | El set de 30–50 llamadas en modo local contra modo nube: la tasa de aciertos no puede bajar. |
| Corte | 2–3 | Grupo chico de operadores primero, después todos. El número de soporte no cambia. |
| **Total** | **~15–20** | **Sin tocar el núcleo, la base ni la consola.** |

## Hitos

| Día | Qué se puede mostrar |
| ---: | --- |
| **2** | Una llamada real guiando "sin internet". |
| **5** | **Demo**: los tres casos por llamada + consola con el caso escalado. |
| **~35** | Set de regresión pasando; consola completa. |
| **~45–50** | 15 operadores en jornada (modo nube). |
| **+15–20** | Mismo servicio corriendo en el datacenter (cuando se pida y con hardware listo). |

## Riesgos que alargan el calendario

- El número colombiano tarda más de lo esperado (para la demo hay número de EE. UU. y llamada desde el navegador).
- El reconocimiento del acento o del ruido de puesto no alcanza: se detecta el día 2, no el 5.
- Hardware para el modo local sin cotizar cuando llega el pedido por protección de datos.
- Una sola persona: cualquier bloqueo mueve el hito completo.
