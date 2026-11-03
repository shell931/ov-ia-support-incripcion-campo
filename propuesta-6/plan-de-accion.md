# Propuesta 6 — Plan de acción y tareas

Documento de trabajo para ejecutar la [propuesta 6](README.md). Las tareas se marcan `[x]` a medida que se cierran. Tiempos: [tiempos.md](tiempos.md). Costos: [costos.md](costos.md).

## 1. Objetivo

Mostrar al cliente, en **5 días hábiles**, un agente que **atiende una llamada telefónica** y guía al operador en los tres casos (primer logueo, tableta sin internet, tableta no enciende). Si no resuelve, deja el caso en una consola para la mesa.

La demo se construye **con la misma arquitectura que irá a producción**, así que puede mudarse a local sin reescribirse (ver [reglas](README.md#las-reglas-que-hacen-posible-la-mudanza)).

### Criterio de hecho de la demo

- [ ] Se llama al número y el agente atiende en menos de 3 s.
- [ ] Los **tres flujos** se recorren de punta a punta por voz, siguiendo el YAML al pie de la letra.
- [ ] La cédula se ingresa por **teclado** y en los logs aparece enmascarada.
- [ ] Cuando el árbol se agota o el operador pide "una persona", el agente **dicta un número de caso**.
- [ ] El caso aparece en la **consola** con los pasos intentados y la transcripción.
- [ ] Todo levanta con `docker compose up` en una VM.
- [ ] Existe un **video de respaldo** de los tres recorridos.

## 2. Decisiones tomadas

| Decisión | Valor | Por qué |
| --- | --- | --- |
| Canal | Llamada telefónica | El cliente no tiene WhatsApp verificado; la demo es solo por voz. |
| Agente de voz | LiveKit Agents (Python) | Es el único de los evaluados que también corre en local. |
| Modo inicial | Nube: LiveKit Cloud + Deepgram + Claude Haiku 5.5 + Cartesia | Velocidad para la demo. |
| Código | Carpeta `app-demo/` en este mismo repo | Decisión del 2026-11-03: documentación y demo juntas. |
| Clasificador | **Claude Haiku 5.5** (`claude-haiku-5-5`) con el SDK oficial de Anthropic, detrás de un puerto propio `Classifier` | El más barato de los evaluados ($0,10 / $0,50 por millón de tokens de entrada / salida). En local se cambia el adaptador por uno compatible con OpenAI (Ollama o vLLM); el núcleo no se entera. |
| Lógica del flujo | Motor YAML determinista | El LLM solo clasifica; no redacta el procedimiento. |
| Datos | **Supabase** en la demo, usado como **Postgres plano** (solo `DATABASE_URL`; sin Auth, Storage ni API de Supabase). En local: Postgres propio con el perfil `local-db` del compose. | Demo totalmente en la nube con backups y panel para ver las tablas; la mudanza es cambiar una variable. RLS activado en todas las tablas para que la API REST de Supabase no las exponga. |
| Despliegue | `docker-compose.yml` (núcleo + agente) en un host en la nube; Postgres en Supabase | El mismo archivo va al datacenter, ahí con `--profile local-db`. |
| Datos de prueba | Cédulas ficticias | Ley 1581: en modo nube la voz pasa por proveedores de EE. UU. |

## 3. Decisiones pendientes (antes del día 1)

| # | Pregunta | Recomendación | Responsable | Estado |
| --- | --- | --- | --- | --- |
| P1 | ¿Dónde vive el código? | **Decidido:** carpeta `app-demo/` en este repo. | Carlos | ✅ |
| P2 | ¿Dónde corren el núcleo y el agente de voz? | Un host en la nube con Docker (VM o PaaS que corra contenedores de larga vida). En **la misma región que el proyecto de Supabase** (us-east-1): cada turno de voz toca la base varias veces. | | ⬜ |
| P3 | ¿Qué LLM chico? | **Decidido:** Claude Haiku 5.5 con el SDK oficial de Anthropic, detrás del puerto `Classifier` (ver sección 6). | Carlos | ✅ |
| P4 | ¿Qué voz en español? | Probar 2 o 3 voces de Cartesia con acento neutro latinoamericano el día 1 y elegir con el equipo. | | ⬜ |
| P5 | ¿Número de EE. UU. o de Colombia para la demo? | EE. UU. si el colombiano no está el día 1. Respaldo: llamada desde el navegador. | | ⬜ |
| P6 | ¿Consola con qué tecnología? | Renderizada en el servidor (FastAPI + plantillas), sin SPA. Es una bandeja, no un producto. | | ⬜ |

## 4. Prerrequisitos (día 0)

- [ ] Cuenta en **LiveKit Cloud** con proyecto creado.
- [ ] Cuenta y API key de **Deepgram**.
- [ ] Cuenta y API key de **Anthropic** (Claude Haiku 5.5).
- [ ] Proyecto en **Supabase** en la región **us-east-1**, con la cadena de conexión del *Session pooler* en `DATABASE_URL`.
- [ ] Cuenta y API key de **Cartesia**.
- [ ] **VM** creada con Docker y Docker Compose (P2).
- [ ] Dominio o subdominio para la consola (opcional en la demo).
- [ ] **Trámite del número colombiano iniciado**: identificación + dirección dentro de la zona del número ([Twilio — Colombia](https://www.twilio.com/en-us/guidelines/co/regulatory)).
- [ ] **Guion de la demo** escrito y validado (sección 8).
- [ ] Textos de los tres flujos validados por procesos (pueden ser los del [PDF](../fuente/incripcion-campo.pdf) en la primera versión).
- [ ] 2 o 3 celulares para probar, y un audio de **ruido de puesto** (fila, conversaciones) para las pruebas.

## 5. Estructura del código

**Convención:** todo el código va en inglés (endpoints, funciones, tablas, claves del YAML, variables de entorno, comentarios). En español solo va el **contenido**: lo que oye el operador y la documentación.

```text
app-demo/                       # dentro de este repo
├── docker-compose.yml          # core, postgres, console, voice-agent
├── .env.example                # ver sección 7
├── core/                       # NÚCLEO — no importa nada de LiveKit ni de proveedores
│   ├── flows/
│   │   ├── no_internet.yaml
│   │   ├── first_login.yaml
│   │   └── tablet_wont_power_on.yaml
│   ├── engine.py               # motor de flujos: lee YAML, avanza, cuenta intentos
│   ├── sessions.py             # puerto SessionStore + adaptadores Postgres y memoria
│   ├── cases.py                # create_case, numeración, prioridad
│   ├── masking.py              # enmascarado de cédula
│   ├── db.py                   # conexión a Postgres
│   └── api.py                  # puertos HTTP: /health, /next-step, /cases
├── voice_agent/                # ADAPTADOR — LiveKit Agents
│   ├── agent.py                # sesión de llamada, turnos, DTMF, espera activa
│   ├── providers.py            # STT / TTS elegidos por variable de entorno
│   └── classifier/             # PUERTO Classifier: texto → yes / no / unclear / human / wait
│       ├── port.py             # interfaz: classify(text, current_step) -> label
│       ├── anthropic.py        # modo nube: Claude Haiku 5.5, SDK oficial
│       └── openai_compat.py    # modo local: Ollama / vLLM
├── console/                    # bandeja de la mesa
│   ├── app.py
│   └── templates/
├── tests/
│   ├── test_engine.py          # los tres árboles recorridos sin voz
│   ├── test_api.py             # /next-step con persistencia en memoria
│   └── calls/                  # audios de regresión (desde el tramo 2)
└── migrations/
    └── 001_initial.sql         # sessions, cases, events
```

**Regla de revisión:** `core/` no puede importar nada de `voice_agent/` ni de ningún SDK de proveedor. Si pasa, la mudanza se rompe.

## 6. Contratos del núcleo (puertos)

Son la frontera hexagonal. El agente de voz solo conoce esto.

El clasificador también es un puerto: `classify(text, current_step) -> label`. La etiqueta sale de una lista cerrada (salida estructurada), así que cambiar de Haiku a un modelo local no cambia el contrato. Para la voz, la latencia manda: esfuerzo bajo, respuesta corta y medir el tiempo por turno el día 2.

```text
GET  /health                    # 200 si el núcleo y Postgres responden; 503 si no

POST /next-step
  request:  { session_id, phone, label, flow?, dtmf? }
            label ∈ { start, yes, no, unclear, human, wait }
  response: { step_id, text, active_wait, asks_dtmf, keypad_mode,
              end, create_case, destination, priority, steps_tried[] }

POST /cases
  request:  { session_id, transcript[] }        # el resto sale de la sesión
  response: { number, priority, destination }

GET  /cases?status=open                         # para la consola
POST /cases/{number}/take                       # nadie más llama al mismo operador
POST /cases/{number}/close                      # close_reason + notes
```

Forma del YAML (ejemplo, flujo "sin internet"; las claves en inglés, el texto en español):

```yaml
id: no_internet
start: mobile_data
escalate: escalate               # "human" salta acá
max_unclear_attempts: 2          # después, pasa a teclado (1 yes, 2 no, 0 human)
steps:
  - id: mobile_data
    text: "Revise que los datos móviles de la tableta estén activos. ¿Están activos?"
    on_yes: airplane_mode
    on_no: enable_data
  - id: restart
    text: "Reinicie la tableta. Me quedo en la línea; avíseme cuando prenda. ¿Ya tiene Internet?"
    active_wait: true
    on_yes: resolved
    on_no: escalate
  - id: resolved
    text: "Perfecto, quedó resuelto. Gracias por llamar."
    end: true
  - id: escalate
    text: "No pudimos resolverlo por aquí. Voy a dejar un caso para soporte técnico."
    end: true
    action: create_case
    destination: help_desk       # help_desk | census_office | logistics
    priority: normal             # normal | high
```

Las transiciones se llaman `on_yes` / `on_no` y no `yes` / `no` a propósito: en YAML 1.1, una clave `no:` sin comillas se lee como el booleano `False` (el "problema de Noruega").

## 7. Variables de entorno

```dotenv
# --- Mode (cloud | onprem): documents intent; each piece is picked below
MODE=cloud

# --- Postgres (the one in docker-compose)
DATABASE_URL=postgresql://app:<password>@postgres:5432/soporte

# --- Telephony and voice server
LIVEKIT_URL=wss://<project>.livekit.cloud       # onprem: wss://voz.cliente.local
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
SIP_TRUNK=livekit-cloud                          # onprem: operador-co

# --- Speech to text
STT=deepgram                                     # onprem: whisper
STT_BASE_URL=                                    # onprem: http://whisper:8000/v1
DEEPGRAM_API_KEY=

# --- Classifier
CLASSIFIER=anthropic                             # onprem: openai-compat
LLM_MODEL=claude-haiku-5-5                       # onprem: the model served by Ollama / vLLM
ANTHROPIC_API_KEY=
LLM_BASE_URL=                                    # onprem only: http://llm:11434/v1

# --- Text to speech
TTS=cartesia                                     # onprem: piper
TTS_BASE_URL=                                    # onprem: http://piper:5000/v1
CARTESIA_API_KEY=
TTS_VOICE=

# --- Core
CORE_URL=http://core:8000
```

## 8. Guion de la demo

Se escribe **antes** del código y se construye para él. Tres recorridos, ~3 minutos cada uno.

| # | Recorrido | Qué demuestra |
| --- | --- | --- |
| G1 | **Sin internet → resuelto.** Datos activos: sí. Modo avión: estaba prendido, lo apaga. Queda con internet. | Guía paso a paso, entiende respuestas libres ("ya, listo, ahí está"). |
| G2 | **Tableta no enciende → escalado.** Cable, tipo C, otra toma, otro adaptador: nada. Pide persona. Dicta número de caso. **Se muestra la consola** con el caso y los pasos intentados. | Escalamiento con contexto: la mesa no vuelve a preguntar lo mismo. |
| G3 | **Primer logueo → espera activa + teclado.** Cédula por teclado. Huella no reconocida tras indicar dedos correctos → caso a Dirección de Censo. Incluye una espera mientras "reinicia la app". | Teclado, espera sin colgar, prioridad del caso. |

Frases que el agente tiene que entender en la demo: "sí", "no", "ya", "listo", "todavía no", "no sé", "espere", "quiero hablar con alguien".

## 9. Tareas día por día

Formato: **ID** · tarea · criterio de aceptación · depende de.

### Día 1 — Base en pie

- [ ] **D1.1** · *(código listo en `app-demo/`; falta verificar `docker compose up`)* Crear estructura de la sección 5 · `docker compose up` contra Supabase levanta un `core` que aplica las migraciones y responde `/health` con `postgres: true` · —
- [ ] **D1.2** · *(SQL listo en `migrations/001_initial.sql`; se verifica con D1.1)* Migración inicial: tablas `sessions`, `cases`, `events` · tablas creadas al levantar (las aplica `core.migrate`), con RLS activado · D1.1
- [ ] **D1.3** · Número en LiveKit Cloud + regla de despacho al agente · llamar al número dispara una sesión del agente · Prerrequisitos
- [ ] **D1.4** · `voice_agent` mínimo: atiende y saluda con la voz elegida · se oye el saludo al llamar desde un celular · D1.3
- [ ] **D1.5** · `providers.py`: STT y TTS elegidos por variable de entorno · cambiar `TTS_VOICE` cambia la voz sin tocar código · D1.4
- [ ] **D1.6** · Probar 2–3 voces y cerrar P4 · voz elegida anotada en `.env.example` · D1.4
- [ ] **D1.7** · Confirmar que el trámite del número colombiano está iniciado · número de solicitud anotado · —

**Plan B del día:** si el número no queda activo, se avanza con llamada desde el navegador y el número se resuelve el día 2.

### Día 2 — Primer flujo completo + prueba de realidad

- [x] **D2.1** · `engine.py`: carga YAML, avanza por etiqueta, cuenta intentos, marca espera activa · `test_engine.py` recorre "sin internet" en todas sus ramas · D1.1
- [x] **D2.2** · `flows/no_internet.yaml` con los textos validados · el test pasa con el YAML real · D2.1
- [x] **D2.3** · *(probado con persistencia en memoria; Postgres se verifica con D1.1)* Puerto `POST /next-step` + sesión en Postgres · una secuencia de llamadas con curl recorre el flujo · D2.1, D1.2
- [ ] **D2.4** · Puerto `Classifier` + adaptador `anthropic.py` (Haiku 5.5, salida restringida a las 6 etiquetas) · 20 frases de la sección 8 clasificadas bien y latencia medida · D1.1
- [ ] **D2.5** · El agente conecta turno → clasificar → `/next-step` → dice el texto · "sin internet" completo por teléfono · D2.3, D2.4
- [ ] **D2.6** · **Prueba con ruido de puesto y acento colombiano** (3 personas distintas) · anotar aciertos/fallos de transcripción y latencia por turno · D2.5

**Punto de decisión:** si D2.6 sale mal (latencia de más de 1,5 s por turno o transcripción poco confiable), cambiar modelo o proveedor de STT **hoy**. Para eso existe `providers.py`.

### Día 3 — Los tres flujos + escalamiento

- [x] **D3.1** · *(adelantada)* `flows/first_login.yaml` y `flows/tablet_wont_power_on.yaml` · tests de ambos árboles pasan · D2.1
- [ ] **D3.2** · Elección de flujo al inicio ("¿Qué le pasa? ¿No tiene internet, no enciende la tableta o no puede entrar?") · el agente enruta bien los tres casos · D2.5
- [ ] **D3.3** · Cédula por teclado (DTMF) + enmascarado (`masking.py`) · la cédula nunca aparece completa en los logs · D2.5
- [ ] **D3.4** · Espera activa: en pasos marcados, el silencio no corta y se pregunta cada 20–30 s · reiniciar la tableta no corta la llamada · D2.5
- [ ] **D3.5** · Teclado como respaldo: dos `unclear` seguidos → "marque 1 para sí, 2 para no, 0 para hablar con alguien" · funciona en los tres flujos · D3.3
- [ ] **D3.6** · Puerto `POST /cases` + escalamiento: el agente dicta el número de caso · el caso queda en Postgres con pasos y transcripción · D2.3

### Día 4 — Consola + respaldo

- [ ] **D4.1** · Consola: cola por prioridad y tiempo de espera · los casos de D3.6 aparecen · D3.6
- [ ] **D4.2** · Detalle del caso: teléfono, cédula enmascarada, flujo, pasos intentados, transcripción · todo visible sin consultar la base · D4.1
- [ ] **D4.3** · Tomar y cerrar caso (causa + notas) · un caso tomado no se puede tomar de nuevo · D4.1
- [ ] **D4.4** · Correr G1, G2 y G3 completos · los tres salen sin intervención manual · D3.*
- [ ] **D4.5** · **Grabar el video de respaldo** (llamada + consola en pantalla) · video guardado fuera de la VM · D4.4

### Día 5 — Ensayo

- [ ] **D5.1** · 10 llamadas de prueba (al menos 3 con ruido) · anotar resultado de cada una · D4.4
- [ ] **D5.2** · Ajustar textos largos, pausas y latencia según D5.1 · ningún paso dura más de ~15 s hablado · D5.1
- [ ] **D5.3** · Ensayo completo del guion con cronómetro · demo en menos de 15 min, con margen · D5.2
- [ ] **D5.4** · Checklist del día de la demo: VM arriba, saldo en los proveedores, celular cargado, video a mano, respaldo con llamada desde el navegador · todo marcado · D5.3
- [ ] **D5.5** · Etiquetar la versión (`demo-v1`) · tag creado en el repo · D5.3

## 10. Después de la demo

Se detallan cuando se apruebe seguir. El orden y el esfuerzo están en [tiempos.md](tiempos.md).

### Tramo 2 — Piloto en modo nube (~40 días)

- [ ] **T2.1** · Robustez de voz: tope por paso, rellamada que retoma el caso abierto (6 d)
- [ ] **T2.2** · Audios pregrabados por paso y nueva síntesis al cambiar el texto (3 d)
- [ ] **T2.3** · Consola completa: login por persona, rol Dirección de Censo, alertas por correo, indicadores (6 d)
- [ ] **T2.4** · Número colombiano + SMS con número de caso (3 d)
- [ ] **T2.5** · CI/CD y ambientes `dev` / `piloto` (4 d)
- [ ] **T2.6** · Endurecimiento: enmascarado, retención y **set de regresión de 30–50 llamadas grabadas** (8 d)
- [ ] **T2.7** · Piloto en campo con ~15 operadores; medir contra la meta de 40–60 % resuelto sin persona (10 d)

### Tramo 3 — Mudanza a local (~15–20 días, cuando se pida)

- [ ] **T3.0** · Hardware listo: GPU, servidores CPU, red y SIP del operador hacia el datacenter (**no es código; es el camino crítico**)
- [ ] **T3.1** · LiveKit OSS + SIP en el datacenter, firewall (DMZ) (5 d)
- [ ] **T3.2** · Faster-Whisper y Piper como servidores de inferencia, conectados por el conector compatible con OpenAI (5 d)
- [ ] **T3.3** · LLM local (Ollama o vLLM) + adaptador `openai_compat.py` del clasificador; las 20 frases de D2.4 tienen que dar igual (2 d)
- [ ] **T3.4** · Set de regresión en modo local contra modo nube: la tasa de aciertos no baja (4 d)
- [ ] **T3.5** · Corte: grupo chico de operadores y después todos; el número de soporte no cambia (2–3 d)

## 11. Checklist de revisión (en cada cambio)

- [ ] `core/` no importa LiveKit ni SDKs de proveedores.
- [ ] Ningún proveedor está fijo en el código: todo sale de `.env`.
- [ ] Ningún texto de procedimiento lo genera el LLM: sale del YAML.
- [ ] La cédula no aparece completa en logs, transcripciones ni consola.
- [ ] Se usó solo Postgres (sin servicios propietarios del proveedor de base).
- [ ] `docker compose up` sigue levantando todo desde cero.
- [ ] Solo cédulas ficticias en modo nube.

## 12. Registro de avance

| Fecha | Día | Hecho | Bloqueos | Decisiones |
| --- | --- | --- | --- | --- |
| 2026-11-03 | antes de D1 | Motor YAML + 3 flujos (D2.1, D2.2, D3.1). `POST /next-step` con cédula por teclado enmascarada (D2.3 y parte de D3.3). 66 tests. Compose con Postgres, `/health`, migración. | Faltan cuentas: LiveKit Cloud, Deepgram, Cartesia, Anthropic. | Código en `app-demo/`. |
| 2026-11-03 | antes de D1 | Base de la demo en **Supabase** (Postgres plano): pool de conexiones, runner de migraciones, RLS en todas las tablas, Postgres propio como perfil `local-db`. 69 tests. | Falta crear el proyecto de Supabase. | Demo 100 % en la nube; Supabase solo como Postgres. |
| | D1 | | | |
| | D2 | | | |
| | D3 | | | |
| | D4 | | | |
| | D5 | | | |
