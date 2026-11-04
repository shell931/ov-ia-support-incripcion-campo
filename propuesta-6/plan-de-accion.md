# Propuesta 6 — Plan de acción y tareas

Documento de trabajo para ejecutar la [propuesta 6](README.md). Las tareas se marcan `[x]` a medida que se cierran. Tiempos: [tiempos.md](tiempos.md). Costos: [costos.md](costos.md).

## 0. Estado actual — leer primero si retomás el proyecto

*Actualizado: 2026-11-04.* Esta sección se reescribe en cada avance. El detalle de cada tarea está en la sección 9, y el historial en la sección 12.

### Dónde estamos

**Una llamada completa ya funciona de punta a punta, sin teléfono.** El 2026-11-04 se probó con un "operador" simulado que habla con frases grabadas, a través de LiveKit Cloud:

> saludo → el operador dice "la tableta no tiene internet" → Haiku elige el flujo → el agente recorre `no_internet` (datos móviles, modo avión, "espéreme" → "aquí lo espero", reinicio) → escala → **crea el caso #8 en Supabase** con la transcripción → dicta el número de caso → cuelga.

| Pieza | Estado |
| --- | --- |
| Núcleo (`app-demo/core/`): motor YAML, `/next-step`, `/cases`, API de la consola, migraciones | ✅ Probado contra Supabase |
| Flujos YAML: `no_internet`, `first_login`, `tablet_wont_power_on`, `other` | ✅ Textos del PDF, **pendientes de validación por procesos** |
| Agente de voz (`app-demo/voice_agent/`) | ✅ Llamada simulada OK. ⬜ Falta número de teléfono y prueba con personas |
| Consola Angular (`app-demo/console/`) | ✅ Revisada en el navegador con casos reales |
| Docker Compose (núcleo + agente + Caddy) | ⬜ Escrito, **nunca levantado completo** (D1.1) |
| EC2 en us-east-1 | ⬜ No creada. Guía: [app-demo/DEPLOY.md](../app-demo/DEPLOY.md) |
| Tests | ✅ 118 en Python (núcleo + diálogo) y 7 en Angular |

### Cuentas (todas validadas el 2026-11-04)

| Servicio | Para qué | Notas |
| --- | --- | --- |
| Supabase (us-east-1) | Base de datos | Solo como Postgres. RLS activo sin políticas. |
| LiveKit Cloud | Servidor de la llamada | Proyecto `support-14bu3me2`, región US East. |
| Deepgram | Oído (`nova-3`, `es`) **y** voz (Aura-2 `aura-2-celeste-es`) | Una sola key para las dos cosas. Crédito inicial: 200 US$. |
| Anthropic | Clasificador (`claude-haiku-5-5`) | Organización de la empresa en platform.claude.com. |
| ~~Cartesia~~ | — | Descartada: Deepgram hace la voz. |

Las keys están **solo** en `app-demo/.env` de la notebook del líder técnico; nunca en el repo ni en un chat. Quien retome necesita sus propias keys, o que se las pasen por un canal seguro.

### Cómo levantarlo hoy

Ver [app-demo/README.md → El agente de voz](../app-demo/README.md#el-agente-de-voz-voice_agent): núcleo en el puerto 8000 + `python -m voice_agent.main console` (micrófono) o `dev` (LiveKit Cloud).

**Trampa conocida:** el `.env` trae `CORE_URL=http://core:8000`, que es la dirección dentro de Docker. Corriendo el agente fuera de Docker hay que pasar `CORE_URL=http://localhost:8000`.

### Lo que sigue, en orden

1. **Probar con la voz de una persona** (`console`, micrófono) los tres flujos. Anotar qué frases no entiende (D2.4, D2.6).
2. **Número de teléfono** en LiveKit Cloud + regla de despacho al agente (D1.3). Con eso se prueban el teclado y la cédula (D3.3, D3.5).
3. **`docker compose up` completo** en la notebook y después en la EC2 (D1.1, DEPLOY.md).
4. **Latencia**: con el clasificador estructurado pasan ~2 s entre que el operador termina de hablar y el agente ya decidió (≈0,6 s de fin de turno + ≈1,2 s de Haiku + núcleo; medido desde Colombia). Medir desde la EC2 en us-east-1. Si sigue alta, `CLASSIFIER_STRUCTURED=false` ahorra ~0,45 s, pero entiende peor (10/16 contra 15/16).
5. Validar los textos de los flujos con el equipo de procesos.

### Pendientes técnicos conocidos

- **Espera activa (D3.4):** el agente responde "aquí lo espero", pero no vuelve a preguntar solo cada 20–30 s si el operador se queda callado.
- **Caché de audio:** las frases fijas se guardan en disco la primera vez que se dicen (`AUDIO_CACHE_DIR`). No se precalientan al arrancar, así que la primera llamada paga la síntesis de cada frase una vez. Para hacerlo bien: precalentar con los textos del YAML (T2.2).
- **STT y TTS on-prem (Whisper y Piper)** no están conectados: `main.py` falla con un mensaje claro si se elige `STT=whisper` o `TTS=piper` (T3.2). El clasificador local (`CLASSIFIER=openai-compat`) sí está escrito, pero sin probar contra un modelo real (T3.3).
- **Dónde viven los flujos:** `app-demo/core/flows/*.yaml`. El núcleo los valida al arrancar (si uno está mal, no levanta). Para cambiar un texto se edita el YAML y se reinicia el núcleo. El agente no lee YAML; la caché de audio se invalida sola porque la clave es el texto.
- **Interrupciones:** si el operador habla encima del saludo, el agente se calla (comportamiento por defecto de LiveKit). Revisar con personas reales si conviene.
- Caso #8 y sesiones `e2e-*` en Supabase: datos de prueba, se pueden borrar.

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
| Modo inicial | Nube: LiveKit Cloud + Deepgram (oído y voz) + Claude Haiku 5.5 | Velocidad para la demo. |
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
| P2 | ¿Dónde corren el núcleo y el agente de voz? | **Decidido:** una instancia **EC2 en us-east-1** con `docker compose` (web + core + voice-agent), conectada al Supabase existente. Guía: [`app-demo/DEPLOY.md`](../app-demo/DEPLOY.md). | Carlos | ✅ |
| P3 | ¿Qué LLM chico? | **Decidido:** Claude Haiku 5.5 con el SDK oficial de Anthropic, detrás del puerto `Classifier` (ver sección 6). | Carlos | ✅ |
| P4 | ¿Qué voz en español? | Deepgram Aura-2 con acento colombiano: Celeste o Gloria (muestras generadas el 2026-11-04). | **Celeste** (`aura-2-celeste-es`), elegida 2026-11-04 | ✅ |
| P5 | ¿Número de EE. UU. o de Colombia para la demo? | EE. UU. si el colombiano no está el día 1. Respaldo: llamada desde el navegador. | | ⬜ |
| P6 | ¿Consola con qué tecnología? | **Decidido: Angular** (el equipo lo conoce y la consola sigue en el piloto). Servida por Caddy en `/`, API en `/api` del mismo origen (sin CORS). | Carlos | ✅ |

## 4. Prerrequisitos (día 0)

### Cuentas

Las claves van **solo** en `app-demo/.env` (no se sube al repo): nunca en el chat, en un commit ni en un documento.

| # | Cuenta | Dónde | Qué hay que hacer | Qué va en `.env` | ¿Bloquea? |
| --- | --- | --- | --- | --- | --- |
| C1 | **LiveKit Cloud** | cloud.livekit.io | Crear un proyecto. En *Telephony*: comprar un número para la demo y crear la regla de despacho hacia el agente (D1.3). | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | Sí, desde D1.3 |
| C2 | **Deepgram** | console.deepgram.com | Crear una API key. | `DEEPGRAM_API_KEY` | Sí, desde D2.5 |
| C3 | ~~Cartesia~~ **descartada** (2026-11-04) | — | La voz la pone Deepgram Aura-2 con la misma key de C2: una cuenta menos. La cuenta creada se puede borrar. | `TTS=deepgram`, `TTS_VOICE` | No |
| C4 | **Anthropic** | platform.claude.com | Crear una API key y cargar saldo (Claude Haiku 5.5). | `ANTHROPIC_API_KEY` | Sí, desde D2.4 |
| C5 | **Supabase** | supabase.com/dashboard | Crear un proyecto en **us-east-1** con una contraseña fuerte para la base. En *Connect* copiar la cadena del ***Session pooler***. | `DATABASE_URL` | Sí, desde D1.1 |
| C6 | **AWS (EC2)** | console.aws.amazon.com | Instancia t3.medium Ubuntu 24.04 en **us-east-1**, Elastic IP y security group mínimo (22 solo tu IP, 80/443). Paso a paso en [`app-demo/DEPLOY.md`](../app-demo/DEPLOY.md). | `SITE_ADDRESS`, `CONSOLE_USER`, `CONSOLE_PASSWORD_HASH` | Sí, para la demo en vivo (antes se puede correr en una notebook) |
| C7 | **GitHub** | github.com | Ya existe: `shell931/ov-ia-support-incripcion-campo`. | — | No |
| C8 | **Número colombiano** (Twilio u otro operador) | twilio.com/console | Iniciar el trámite: identificación + dirección dentro de la zona del número ([Twilio — Colombia](https://www.twilio.com/en-us/guidelines/co/regulatory)). Para la demo alcanza el número de C1. | `SIP_TRUNK` (en el piloto) | No para la demo; sí para el piloto |
| C9 | **Dominio** | cualquier registrador | Subdominio para la consola (ej. `consola.<dominio>`). | — | No (opcional en la demo) |

Casi todas piden tarjeta de crédito. Conviene usar una tarjeta de la empresa y poner **alertas o tope de gasto** donde la plataforma lo permita.

### Además de las cuentas

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
│   │   ├── tablet_wont_power_on.yaml
│   │   └── other.yaml          # "quiero una persona" / problema no entendido → caso directo
│   ├── engine.py               # motor de flujos: lee YAML, avanza, cuenta intentos
│   ├── sessions.py             # puerto SessionStore + adaptadores Postgres y memoria
│   ├── cases.py                # create_case, numeración, prioridad
│   ├── masking.py              # enmascarado de cédula
│   ├── db.py                   # conexión a Postgres
│   └── api.py                  # puertos HTTP: /health, /next-step, /cases
├── voice_agent/                # ADAPTADOR — LiveKit Agents 1.8
│   ├── dialog.py               # lógica de la llamada, SIN LiveKit (tests/test_dialog.py)
│   ├── classifier.py           # PUERTO Classifier + adaptadores anthropic (Haiku 5.5) y openai-compat (local)
│   ├── core_client.py          # HTTP al núcleo: /next-step, /cases
│   ├── speech.py               # dice las respuestas; caché en disco de frases fijas
│   ├── main.py                 # sesión LiveKit: STT/TTS por variable de entorno, VAD, DTMF
│   ├── requirements.txt
│   └── Dockerfile
├── console/                    # bandeja de la mesa — Angular (build estático servido por Caddy)
│   ├── src/app/cases/          # cola, detalle, servicio HTTP
│   └── Dockerfile              # node build → caddy
├── Caddyfile                   # HTTPS, contraseña, consola en /, solo /api/cases* expuesto
├── DEPLOY.md                   # paso a paso en EC2
├── tests/
│   ├── test_engine.py          # los tres árboles recorridos sin voz
│   ├── test_api.py             # /next-step con persistencia en memoria
│   ├── test_dialog.py          # el diálogo del agente con el motor real y un clasificador falso
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
TTS=deepgram                                     # onprem: piper
TTS_BASE_URL=                                    # onprem: http://piper:5000/v1
TTS_VOICE=aura-2-celeste-es                     # uses DEEPGRAM_API_KEY

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

- [ ] **D1.1** · *(núcleo verificado contra Supabase: `/health` 200 con `postgres: true` y `/next-step` de punta a punta; falta solo correrlo con `docker compose up`)* Crear estructura de la sección 5 · `docker compose up` contra Supabase levanta un `core` que aplica las migraciones y responde `/health` con `postgres: true` · —
- [x] **D1.2** · *(aplicada en Supabase el 2026-11-03: 4 tablas con RLS; segunda corrida sin cambios)* Migración inicial: tablas `sessions`, `cases`, `events` · tablas creadas al levantar (las aplica `core.migrate`), con RLS activado · D1.1
- [ ] **D1.3** · Número en LiveKit Cloud + regla de despacho al agente · llamar al número dispara una sesión del agente · Prerrequisitos
- [ ] **D1.4** · *(agente hecho y probado por LiveKit Cloud con un operador simulado el 2026-11-04; falta oírlo desde un celular, depende de D1.3)* `voice_agent` mínimo: atiende y saluda con la voz elegida · se oye el saludo al llamar desde un celular · D1.3
- [x] **D1.5** · *(en `voice_agent/main.py`: `build_stt()` y `build_tts()` leen `STT`, `STT_MODEL`, `TTS`, `TTS_VOICE`)* `providers.py`: STT y TTS elegidos por variable de entorno · cambiar `TTS_VOICE` cambia la voz sin tocar código · D1.4
- [x] **D1.6** · *(Celeste, Deepgram Aura-2, acento colombiano)* Probar 2–3 voces y cerrar P4 · voz elegida anotada en `.env.example` · D1.4
- [ ] **D1.7** · Confirmar que el trámite del número colombiano está iniciado · número de solicitud anotado · —

**Plan B del día:** si el número no queda activo, se avanza con llamada desde el navegador y el número se resuelve el día 2.

### Día 2 — Primer flujo completo + prueba de realidad

- [x] **D2.1** · `engine.py`: carga YAML, avanza por etiqueta, cuenta intentos, marca espera activa · `test_engine.py` recorre "sin internet" en todas sus ramas · D1.1
- [x] **D2.2** · `flows/no_internet.yaml` con los textos validados · el test pasa con el YAML real · D2.1
- [x] **D2.3** · *(probado con persistencia en memoria; Postgres se verifica con D1.1)* Puerto `POST /next-step` + sesión en Postgres · una secuencia de llamadas con curl recorre el flujo · D2.1, D1.2
- [ ] **D2.4** · *(puerto y adaptadores en `voice_agent/classifier.py`, con **salida estructurada** (JSON schema, `CLASSIFIER_STRUCTURED=true`): 15/16 frases bien, mediana 1,2 s desde Colombia; en texto plano 10/16 y 0,75 s. Faltan las 20 frases de la sección 8)* Puerto `Classifier` + adaptador `anthropic.py` (Haiku 5.5, salida restringida a las 6 etiquetas) · 20 frases de la sección 8 clasificadas bien y latencia medida · D1.1
- [x] **D2.5** · *(probado por LiveKit Cloud con operador simulado: "sin internet" completo hasta el caso #8; falta repetirlo por teléfono con D1.3)* El agente conecta turno → clasificar → `/next-step` → dice el texto · "sin internet" completo por teléfono · D2.3, D2.4
- [ ] **D2.6** · **Prueba con ruido de puesto y acento colombiano** (3 personas distintas) · anotar aciertos/fallos de transcripción y latencia por turno · D2.5

**Punto de decisión:** si D2.6 sale mal (latencia de más de 1,5 s por turno o transcripción poco confiable), cambiar modelo o proveedor de STT **hoy**. Para eso existe `providers.py`.

### Día 3 — Los tres flujos + escalamiento

- [x] **D3.1** · *(adelantada)* `flows/first_login.yaml` y `flows/tablet_wont_power_on.yaml` · tests de ambos árboles pasan · D2.1
- [x] **D3.2** · *(por voz con Haiku, o teclas 1/2/3; "una persona" o 3 intentos fallidos abren un caso con el flujo `other`)* Elección de flujo al inicio ("¿Qué le pasa? ¿No tiene internet, no enciende la tableta o no puede entrar?") · el agente enruta bien los tres casos · D2.5
- [ ] **D3.3** · *(código hecho: dígitos hasta `#` o 5 s de pausa; una cédula dicha en voz alta se enmascara antes de salir del agente y no cuenta; falta probar con teléfono)* Cédula por teclado (DTMF) + enmascarado (`masking.py`) · la cédula nunca aparece completa en los logs · D2.5
- [ ] **D3.4** · *(parcial: "espéreme" → "aquí lo espero" sin avanzar; falta volver a preguntar solo cada 20–30 s)* Espera activa: en pasos marcados, el silencio no corta y se pregunta cada 20–30 s · reiniciar la tableta no corta la llamada · D2.5
- [x] **D3.5** · *(lógica con tests; se prueba con teléfono en D1.3)* Teclado como respaldo: dos `unclear` seguidos → "marque 1 para sí, 2 para no, 0 para hablar con alguien" · funciona en los tres flujos · D3.3
- [x] **D3.6** · *(probado contra Supabase: crea el caso, es idempotente, transcripción enmascarada)* Puerto `POST /cases` + escalamiento: el agente dicta el número de caso · el caso queda en Postgres con pasos y transcripción · D2.3

### Día 4 — Consola + respaldo

- [x] **D4.1** · *(revisada en el navegador con casos reales el 2026-11-04)* Consola: cola por prioridad y tiempo de espera · los casos de D3.6 aparecen · D3.6
- [x] **D4.2** · *(revisada en el navegador; API y pantalla: pasos intentados con su texto, transcripción enmascarada, botón Llamar)* Detalle del caso: teléfono, cédula enmascarada, flujo, pasos intentados, transcripción · todo visible sin consultar la base · D4.1
- [x] **D4.3** · *(revisada en el navegador; API y pantalla: tomar con nombre, cerrar con causa; el 409 se muestra en español)* Tomar y cerrar caso (causa + notas) · un caso tomado no se puede tomar de nuevo · D4.1
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
- [ ] **T2.2** · *(adelantado: caché en disco de frases fijas en `voice_agent/speech.py`; falta precalentarla con los textos del YAML)* Audios pregrabados por paso y nueva síntesis al cambiar el texto (3 d)
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
| 2026-11-03 | antes de D1 | Base de la demo en **Supabase** (Postgres plano): pool de conexiones, runner de migraciones, RLS en todas las tablas, Postgres propio como perfil `local-db`. 69 tests. | — | Demo 100 % en la nube; Supabase solo como Postgres. |
| 2026-11-03 | antes de D1 | Supabase conectado (PostgreSQL 17, us-east-1). Migraciones aplicadas, RLS en las 4 tablas. `/next-step` probado de punta a punta contra la base real: la cédula queda `*******678` y no aparece en los eventos. | Latencia por turno desde Colombia ≈ 850 ms (≈ 84 ms por ida y vuelta × ~10 viajes a la base). Desde un host en us-east-1 debería bajar a decenas de ms. | Agrupar las operaciones de cada turno en una sola transacción (pendiente). |
| 2026-11-03 | antes de D1 | Cada turno pasa a 2 viajes a la base (lectura + escritura con el evento en una sola sentencia). `POST /cases` (D3.6): idempotente con la migración `002`, transcripción enmascarada, destino y prioridad desde el YAML. 81 tests. | — | Latencia por turno desde Colombia: de ≈ 850 ms a ≈ 179 ms. Desde us-east-1 serán pocos ms. |
| 2026-11-04 | antes de D1 | Cuenta **LiveKit Cloud** (C1) creada y validada: la API de servidor autentica y se generan tokens para entrar a salas. Consola Angular revisada en local con casos de prueba. Cuenta **Deepgram** (C2) validada con un audio en español: `nova-3` transcribe bien ("modo avión"); `nova-2` se equivocó ("bobo avión"). Cuenta **Cartesia** (C3) validada: 82 voces en español; 4 muestras con `sonic-3` (Ximena, Fernanda, Rodrigo, Eduardo), y Deepgram las transcribe sin errores. | — Voz elegida: **Celeste** (P4). Cuenta **Anthropic** (C4) validada: Haiku 5.5 clasificó 7/7 frases reales del operador (yes, no, wait, human, unclear) en 0,7–1,2 s desde Colombia, ~200 tokens de entrada por turno. **Las 4 cuentas de voz están listas.** | STT: Deepgram `nova-3`, `language=es`. TTS: **Deepgram Aura-2** con acento colombiano, voz **Celeste** (`aura-2-celeste-es`); se descarta Cartesia para tener una cuenta menos. El número de teléfono se compra al final (D1.3/D1.5): el agente se prueba primero sin línea telefónica. |
| 2026-11-04 | D1 | **Clasificador con salida estructurada** (JSON schema con las etiquetas como `enum`): 16 frases reales, 15/16 bien contra 10/16 en texto plano (Haiku a veces explicaba en vez de responder la etiqueta), a cambio de ~0,45 s más por turno. | — | `CLASSIFIER_STRUCTURED=true` por defecto. El único fallo ("eh… no sé, creo que sí" → `unclear`) es aceptable: el agente repregunta. |
| 2026-11-04 | D1 | **Agente de voz** (`app-demo/voice_agent/`, LiveKit Agents 1.8.10): diálogo sin LiveKit y con tests, clasificador (Anthropic y openai-compat), cliente del núcleo, teclado DTMF, caché de audio en disco. Flujo `other` para "quiero una persona" antes de elegir el problema. Servicio `voice-agent` en el compose. **Llamada simulada completa por LiveKit Cloud: caso #8 creado en Supabase.** 118 tests. | Sin número de teléfono no se prueban el teclado ni la cédula. | LiveKit no usa LLM para responder: `on_user_turn_completed` + `StopResponse`, el texto sale del YAML. Una cédula dicha en voz alta se enmascara antes de llegar al clasificador. |
| | D1 | | | |
| | D2 | | | |
| | D3 | | | |
| | D4 | | | |
| | D5 | | | |
