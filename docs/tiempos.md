# Tiempos de implementación del piloto

Estimación en **días hábiles** para **una sola persona** de desarrollo. Procesos del cliente aprueba los textos de cada paso en paralelo (no cuenta como día de ingeniería).

Alcance: WhatsApp (chat y llamada), tres flujos, consola de casos e infraestructura en AWS.

Fuera de este calendario: foto del cargador, nota de voz de WhatsApp, reenvío automático de credenciales, inventario, tablero por municipio y guía offline en la tableta.

El camino crítico no es el código: **verificar el número de WhatsApp y habilitar llamadas** (Meta). Hay que arrancarlo el día 1; suele tardar **5 a 15 días**, a veces más. Esa espera se usa para infra, YAML y el motor.

Comportamiento del agente en [analisis-agente-voz.md](analisis-agente-voz.md). Piezas en [infraestructura.md](infraestructura.md). Costos en [costos.md](costos.md).

Con una persona no hay solape de chat, voz y consola: cada fase empieza cuando la anterior está usable. El esfuerzo de las piezas no cambia; el calendario se alarga porque las hace la misma persona en serie.

## Fases

| Fase | Días | Qué queda listo |
| --- | ---: | --- |
| **0. Arranque** | 1–2 | Cuentas (AWS, Meta, LiveKit, Deepgram, Cartesia, LLM), ambientes, textos del flujo “sin internet”. |
| **1. Infraestructura** | 3–12 | Terraform, ECS, RDS, Redis, S3, CI/CD, `dev` y `piloto`. |
| **2. Prueba de concepto** | 13–22 | Motor + YAML “sin internet”, agente de voz en navegador. Si Meta ya habilitó calling: una llamada WhatsApp con caso y devolución de la mesa. |
| **3. Chat de los 3 casos** | 23–32 | Webhook, worker, botones, sesión, ticket al escalar. |
| **4. Voz de los 3 casos** | 33–46 | Mismo árbol, audios en S3, DTMF (cédula), espera activa, prueba con ruido de puesto. |
| **5. Consola y alertas** | 47–56 | Cola, detalle, tomar caso, Cognito, correo SES, indicadores básicos. |
| **6. Endurecimiento** | 57–64 | Enmascarado, latencia, set de 30–50 llamadas, circuito completo de mesa. |
| **7. Piloto en campo** | 65–74 | Unos 15 operadores, ajuste de textos y audios, medición contra 40–60 % resueltas sin persona. |

**Total al criterio de hecho del piloto: ~70 días hábiles (unas 14 semanas).** La prueba de concepto se puede mostrar alrededor del **día 22**.

## Piezas (esfuerzo; una persona las hace en serie)

| Pieza | Días | Notas |
| --- | ---: | --- |
| Terraform, CI/CD, `dev` y `piloto` | 10 | Primero. Sin esto no hay webhook ni agente en AWS. |
| YAML + motor de flujos (3 árboles, intentos, escalar, retoma) | 8 | Base compartida de chat y voz. |
| Redis sesión + Postgres casos | 4 | Arranca con el motor. |
| `gateway` + SQS + `worker` WhatsApp | 8 | Chat de punta a punta de conectividad primero. |
| `voice-agent` LiveKit + Deepgram + Cartesia | 10 | Después del motor y, en lo posible, del chat. |
| Pipeline de audios a S3 | 3 | Cada cambio de texto vuelve a sintetizar ese paso. |
| Consola CloudFront + Cognito | 8 | Bandeja de casos, no una mesa de ayuda completa. |
| Pruebas con ruido + circuito mesa | 5 | Incluye las 10 llamadas de la PoC y el set mayor. |
| Acompañamiento en campo | 10 | No es desarrollo nuevo; es ajuste. |

Suma de piezas: **66 días**. Más arranque (2) y un margen corto de integración: **~70 días**.

## Hitos

| Día | Qué se puede mostrar |
| ---: | --- |
| **12** | Infra en pie (`dev`). |
| **22** | Demo grabada de “sin internet”, tabla de latencia; si hay calling, un caso que la mesa recibe y devuelve. |
| **32** | Un operador resuelve los tres casos por chat. |
| **46** | Lo mismo por llamada, con cédula por teclado y audios de S3. |
| **56** | Consola usable por la mesa. |
| **70** | 15 operadores en jornada; se mide contra la meta. |

## Riesgos que alargan el calendario

- Meta no habilita calling a tiempo (el chat puede seguir; la voz no).
- Nadie aprueba los textos de los pasos (y por tanto los audios de S3).
- No hay cifras de puestos ni de pico, y hay que redimensionar LiveKit y Deepgram a mitad de camino.
- Una sola persona: cualquier bloqueo (cuenta, permiso, enfermedad) mueve el hito entero.

## Historias de usuario

Esfuerzo en días hábiles de **una persona**, alineado con la tabla de piezas. Las de infraestructura van primero; las de valor las reutilizan. El total vuelve a ~70 días con el piloto en campo.

### Infraestructura

| ID | Historia | Días | Pieza |
| --- | --- | ---: | --- |
| I1 | Como desarrollo, dejo AWS listo para correr gateway, worker y voice-agent en `dev` y `piloto`. | 10 | Terraform, CI/CD |
| I2 | Como procesos, defino los tres árboles en YAML (texto, transiciones, tope de intentos, escalar) y el motor los ejecuta sin que el LLM redacte el procedimiento. | 8 | Motor de flujos |
| I3 | Como agente, guardo sesión por teléfono (paso, intentos, caso) y persisto el caso en Postgres. | 4 | Redis + Postgres |

### Operador — chat

| ID | Historia | Días | Pieza |
| --- | --- | ---: | --- |
| O1 | Como operador, escribo por WhatsApp, elijo logueo / internet / tableta y me guían el caso **sin internet** con una acción por turno y botones de sí / no / persona. | 5 | `gateway` + `worker` |
| O2 | Como operador, me guían el **primer logueo** por chat (sin huella; cédula enmascarada en logs). | 2 | `worker` + YAML logueo |
| O3 | Como operador, me guían si la **tableta no enciende** o no está en el puesto, y si no cierra queda novedad de equipo. | 1 | `worker` + YAML tableta |

### Operador — voz

| ID | Historia | Días | Pieza |
| --- | --- | ---: | --- |
| O4 | Como operador, llamo por WhatsApp y oigo la guía de **sin internet**: el paso es el id del YAML y el audio sale de S3. | 7 | `voice-agent` + LiveKit |
| O5 | Como operador, marco la **cédula por teclado** (DTMF) y, si hay que reiniciar la tableta, el agente espera en línea y pregunta cada 20–30 s. | 3 | `voice-agent` (DTMF, espera) |
| O6 | Como operador, los flujos de logueo y tableta funcionan igual por voz que por chat. | 3 | `voice-agent` + motor |
| O7 | Como procesos, al cambiar el texto de un paso el pipeline vuelve a sintetizar **ese** audio en S3. | 3 | Pipeline de audios |

### Escalamiento y mesa

| ID | Historia | Días | Pieza |
| --- | --- | ---: | --- |
| M1 | Como operador, si el árbol se agota o pido una persona, recibo el **número de caso por WhatsApp**; no me transfieren en vivo. | 2 | worker / voice-agent → Meta |
| M2 | Como persona de la mesa, veo la cola por prioridad, tomo el caso (nadie más llama al mismo operador) y veo pasos intentados y transcripción enmascarada. | 6 | Consola + Cognito |
| M3 | Como mesa (y Dirección de Censo en casos altos), recibo correo al entrar un caso alto y veo indicadores básicos en la consola. Dirección de Censo solo ve huella y credenciales. | 2 | SES + consola |

### Cierre del piloto

| ID | Historia | Días | Pieza |
| --- | --- | ---: | --- |
| P1 | Como equipo, corro 10 llamadas ruidosas en la PoC y luego un set de 30–50, con latencia, resueltas y fallas. | 5 | Pruebas + circuito mesa |
| P2 | Como operador en campo, uso el piloto ~15 personas en jornada; se ajustan textos/audios y se mide 40–60 % resueltas sin persona en conectividad y carga. | 10 | Acompañamiento en campo |

| | Días |
| --- | ---: |
| Infraestructura I1–I3 | 22 |
| Chat O1–O3 | 8 |
| Voz O4–O7 | 16 |
| Mesa M1–M3 | 10 |
| Cierre P1–P2 | 15 |
| **Total** | **71** |

Los ~70 días de las fases y los 71 de las historias son el mismo trabajo, partido de dos maneras. No se suman entre sí.
