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
| Clasificador | **Claude Haiku 5.5** (`claude-haiku-5-5`) con el SDK oficial de Anthropic, detrás de un puerto propio `Clasificador` | El más barato de los evaluados ($0,10 / $0,50 por millón de tokens de entrada / salida). En local se cambia el adaptador por uno compatible con OpenAI (Ollama o vLLM); el núcleo no se entera. |
| Lógica del flujo | Motor YAML determinista | El LLM solo clasifica; no redacta el procedimiento. |
| Datos | Postgres plano | Se muda sin dependencias de proveedor. |
| Despliegue | `docker-compose.yml` en una VM | El mismo archivo va al datacenter. |
| Datos de prueba | Cédulas ficticias | Ley 1581: en modo nube la voz pasa por proveedores de EE. UU. |

## 3. Decisiones pendientes (antes del día 1)

| # | Pregunta | Recomendación | Responsable | Estado |
| --- | --- | --- | --- | --- |
| P1 | ¿Dónde vive el código? | **Decidido:** carpeta `app-demo/` en este repo. | Carlos | ✅ |
| P2 | ¿Qué VM? | Cualquier proveedor con 4 vCPU / 8 GB y IP pública. Si es posible, cerca de us-east, que es donde responden los proveedores de voz. | | ⬜ |
| P3 | ¿Qué LLM chico? | **Decidido:** Claude Haiku 5.5 con el SDK oficial de Anthropic, detrás del puerto `Clasificador` (ver sección 6). | Carlos | ✅ |
| P4 | ¿Qué voz en español? | Probar 2 o 3 voces de Cartesia con acento neutro latinoamericano el día 1 y elegir con el equipo. | | ⬜ |
| P5 | ¿Número de EE. UU. o de Colombia para la demo? | EE. UU. si el colombiano no está el día 1. Respaldo: llamada desde el navegador. | | ⬜ |
| P6 | ¿Consola con qué tecnología? | Renderizada en el servidor (FastAPI + plantillas), sin SPA. Es una bandeja, no un producto. | | ⬜ |

## 4. Prerrequisitos (día 0)

- [ ] Cuenta en **LiveKit Cloud** con proyecto creado.
- [ ] Cuenta y API key de **Deepgram**.
- [ ] Cuenta y API key de **Anthropic** (Claude Haiku 5.5).
- [ ] Cuenta y API key de **Cartesia**.
- [ ] **VM** creada con Docker y Docker Compose (P2).
- [ ] Dominio o subdominio para la consola (opcional en la demo).
- [ ] **Trámite del número colombiano iniciado**: identificación + dirección dentro de la zona del número ([Twilio — Colombia](https://www.twilio.com/en-us/guidelines/co/regulatory)).
- [ ] **Guion de la demo** escrito y validado (sección 8).
- [ ] Textos de los tres flujos validados por procesos (pueden ser los del [PDF](../fuente/incripcion-campo.pdf) en la primera versión).
- [ ] 2 o 3 celulares para probar, y un audio de **ruido de puesto** (fila, conversaciones) para las pruebas.

## 5. Estructura del código

```text
app-demo/                       # dentro de este repo
├── docker-compose.yml          # núcleo, postgres, consola, voice-agent
├── .env.example                # ver sección 7
├── core/                       # NÚCLEO — no importa nada de LiveKit ni de proveedores
│   ├── flows/
│   │   ├── sin_internet.yaml
│   │   ├── primer_logueo.yaml
│   │   └── tableta_no_enciende.yaml
│   ├── engine.py               # motor de flujos: lee YAML, avanza, cuenta intentos
│   ├── cases.py                # crear_caso, numeración, prioridad
│   ├── masking.py              # enmascarado de cédula
│   ├── db.py                   # Postgres (sesión, casos, historial)
│   └── api.py                  # puertos HTTP: /siguiente-paso, /casos
├── voice_agent/                # ADAPTADOR — LiveKit Agents
│   ├── agent.py                # sesión de llamada, turnos, DTMF, espera activa
│   ├── providers.py            # STT / TTS elegidos por variable de entorno
│   └── classify/               # PUERTO Clasificador: texto → sí / no / no_entendí / persona / esperar
│       ├── port.py             # interfaz: clasificar(texto, paso) -> etiqueta
│       ├── anthropic.py        # modo nube: Claude Haiku 5.5, SDK oficial
│       └── openai_compat.py    # modo local: Ollama / vLLM
├── console/                    # bandeja de la mesa
│   ├── app.py
│   └── templates/
├── tests/
│   ├── test_engine.py          # los tres árboles recorridos sin voz
│   └── calls/                  # audios de regresión (desde el tramo 2)
└── migrations/
```

**Regla de revisión:** `core/` no puede importar nada de `voice_agent/` ni de ningún SDK de proveedor. Si pasa, la mudanza se rompe.

## 6. Contratos del núcleo (puertos)

El clasificador también es un puerto: `clasificar(texto, paso_actual) -> etiqueta`. La etiqueta sale de una lista cerrada de 6 valores (salida estructurada), así que cambiar de Haiku a un modelo local no cambia el contrato. Para la voz, la latencia manda: esfuerzo bajo, respuesta corta y medir el tiempo por turno el día 2.

Son la frontera hexagonal. El agente de voz solo conoce esto.

```text
POST /siguiente-paso
  entrada: { sesion_id, telefono, etiqueta, dtmf? }
           etiqueta ∈ { inicio, si, no, no_entendi, persona, esperar }
  salida:  { paso_id, texto, espera_activa: bool, pide_dtmf: bool,
             fin: bool, caso?: { numero, prioridad } }

POST /casos
  entrada: { sesion_id, telefono, cedula_enmascarada, flujo,
             pasos_intentados[], transcripcion[], motivo }
  salida:  { numero, prioridad }

GET  /casos?estado=abierto      # para la consola
POST /casos/{numero}/tomar      # nadie más llama al mismo operador
POST /casos/{numero}/cerrar     # causa + notas
```

Forma del YAML (ejemplo, flujo "sin internet"):

```yaml
id: sin_internet
max_intentos_no_entendi: 2       # después, pasa a teclado
pasos:
  - id: datos_moviles
    texto: "Revise que los datos móviles de la tableta estén activos. ¿Están activos?"
    si: modo_avion
    no: activar_datos
  - id: activar_datos
    texto: "Deslice desde arriba y toque el ícono de datos móviles. Avíseme cuando lo haga."
    espera_activa: true
    si: modo_avion
    no: escalar
  - id: modo_avion
    texto: "Revise que el modo avión esté apagado. ¿Ya tiene internet?"
    si: resuelto
    no: reiniciar
  - id: reiniciar
    texto: "Reinicie la tableta. Me quedo en línea; avíseme cuando prenda."
    espera_activa: true
    si: resuelto
    no: escalar
  - id: resuelto
    texto: "Perfecto, quedó resuelto. Gracias."
    fin: true
  - id: escalar
    texto: "Voy a dejar un caso para la mesa de ayuda. Lo van a llamar a este número."
    accion: crear_caso
    fin: true
```

## 7. Variables de entorno

```dotenv
# --- Modo (nube | local): documenta la intención; las piezas se eligen abajo
MODO=nube

# --- Telefonía y servidor de voz
LIVEKIT_URL=wss://<proyecto>.livekit.cloud      # local: wss://voz.cliente.local
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
SIP_TRUNK=livekit-cloud                          # local: operador-co

# --- Voz a texto
STT=deepgram                                     # local: whisper
STT_BASE_URL=                                    # local: http://whisper:8000/v1
DEEPGRAM_API_KEY=

# --- Clasificador
CLASIFICADOR=anthropic                           # local: openai-compat
LLM_MODEL=claude-haiku-5-5                       # local: el modelo servido por Ollama / vLLM
ANTHROPIC_API_KEY=
LLM_BASE_URL=                                    # solo local: http://llm:11434/v1

# --- Texto a voz
TTS=cartesia                                     # local: piper
TTS_BASE_URL=                                    # local: http://piper:5000/v1
CARTESIA_API_KEY=
TTS_VOZ=

# --- Núcleo
DATABASE_URL=postgresql://app:app@postgres:5432/soporte
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

- [ ] **D1.1** · Crear repo y estructura de la sección 5 · `docker compose up` levanta Postgres y un `core` que responde `/salud` · —
- [ ] **D1.2** · Migración inicial: tablas `sesiones`, `casos`, `eventos` · tablas creadas al levantar · D1.1
- [ ] **D1.3** · Número en LiveKit Cloud + regla de despacho al agente · llamar al número dispara una sesión del agente · Prerrequisitos
- [ ] **D1.4** · `voice_agent` mínimo: atiende y saluda con la voz elegida · se oye el saludo al llamar desde un celular · D1.3
- [ ] **D1.5** · `providers.py`: STT y TTS elegidos por variable de entorno · cambiar `TTS_VOZ` cambia la voz sin tocar código · D1.4
- [ ] **D1.6** · Probar 2–3 voces y cerrar P4 · voz elegida anotada en `.env.example` · D1.4
- [ ] **D1.7** · Confirmar que el trámite del número colombiano está iniciado · número de solicitud anotado · —

**Plan B del día:** si el número no queda activo, se avanza con llamada desde el navegador y el número se resuelve el día 2.

### Día 2 — Primer flujo completo + prueba de realidad

- [ ] **D2.1** · `engine.py`: carga YAML, avanza por etiqueta, cuenta intentos, marca espera activa · `test_engine.py` recorre "sin internet" en todas sus ramas · D1.1
- [ ] **D2.2** · `flows/sin_internet.yaml` con los textos validados · el test pasa con el YAML real · D2.1
- [ ] **D2.3** · Puerto `POST /siguiente-paso` + sesión en Postgres · una secuencia de llamadas con curl recorre el flujo · D2.1, D1.2
- [ ] **D2.4** · Puerto `Clasificador` + adaptador `anthropic.py` (Haiku 5.5, salida restringida a las 6 etiquetas) · 20 frases de la sección 8 clasificadas bien y latencia medida · D1.1
- [ ] **D2.5** · El agente conecta turno → clasificar → `/siguiente-paso` → dice el texto · "sin internet" completo por teléfono · D2.3, D2.4
- [ ] **D2.6** · **Prueba con ruido de puesto y acento colombiano** (3 personas distintas) · anotar aciertos/fallos de transcripción y latencia por turno · D2.5

**Punto de decisión:** si D2.6 sale mal (latencia de más de 1,5 s por turno o transcripción poco confiable), cambiar modelo o proveedor de STT **hoy**. Para eso existe `providers.py`.

### Día 3 — Los tres flujos + escalamiento

- [ ] **D3.1** · `flows/primer_logueo.yaml` y `flows/tableta_no_enciende.yaml` · tests de ambos árboles pasan · D2.1
- [ ] **D3.2** · Elección de flujo al inicio ("¿Qué le pasa? ¿No tiene internet, no enciende la tableta o no puede entrar?") · el agente enruta bien los tres casos · D2.5
- [ ] **D3.3** · Cédula por teclado (DTMF) + enmascarado (`masking.py`) · la cédula nunca aparece completa en los logs · D2.5
- [ ] **D3.4** · Espera activa: en pasos marcados, el silencio no corta y se pregunta cada 20–30 s · reiniciar la tableta no corta la llamada · D2.5
- [ ] **D3.5** · Teclado como respaldo: dos `no_entendi` seguidos → "marque 1 para sí, 2 para no, 0 para hablar con alguien" · funciona en los tres flujos · D3.3
- [ ] **D3.6** · Puerto `POST /casos` + escalamiento: el agente dicta el número de caso · el caso queda en Postgres con pasos y transcripción · D2.3

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
| | D1 | | | |
| | D2 | | | |
| | D3 | | | |
| | D4 | | | |
| | D5 | | | |
