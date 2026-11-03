# app-demo — demo por llamada (propuesta 6)

Código de la demo de la [propuesta 6](../propuesta-6/README.md). Plan y tareas: [plan-de-accion.md](../propuesta-6/plan-de-accion.md).

## Qué hay hoy

| Pieza | Estado |
| --- | --- |
| `core/engine.py`: motor de flujos determinista | ✅ |
| `core/flows/*.yaml`: los tres flujos (textos del PDF, **pendientes de validación por procesos**) | ✅ |
| `core/api.py`: `GET /health` | ✅ |
| `migrations/001_initial.sql`: `sessions`, `cases`, `events` | ✅ |
| `docker-compose.yml`: Postgres 16 + núcleo | ✅ (falta probar `docker compose up`) |
| `POST /next-step`: sesión, teclado de respaldo, cédula por teclado enmascarada | ✅ (tests en memoria; el adaptador Postgres falta probarlo con `docker compose up`) |
| `core/masking.py`: cédula, solo los 3 últimos dígitos | ✅ |
| `POST /cases` | ⬜ D3.6 |
| Tests | 66 en total, todos pasan |
| `voice_agent/` (LiveKit Agents) | ⬜ D1.4, necesita las cuentas |
| `console/` | ⬜ D4.1 |

## Correr los tests (sin Docker ni cuentas)

```bash
cd app-demo
uv run --python 3.12 --with-requirements requirements-dev.txt pytest -q
```

## Levantar el núcleo

```bash
cd app-demo
cp .env.example .env      # completar; .env no se sube al repo
docker compose up --build
curl localhost:8000/health
```

Postgres corre **dentro del compose** (imagen oficial `postgres:16-alpine`), igual en la notebook, en la VM y en el datacenter. Si algún día se usa uno administrado (Supabase, RDS…), se cambia solo `DATABASE_URL` y se usa como Postgres plano.

## Reglas (resumen del plan)

- Código en inglés; en español solo los textos que oye el operador y la documentación.

- `core/` no importa nada de LiveKit ni de SDKs de proveedores.
- El texto que oye el operador sale **del YAML**; el LLM solo clasifica.
- La cédula nunca se guarda completa.
- Ningún proveedor fijo en el código: todo sale de `.env`.

## Escribir un flujo

Claves en inglés, textos en español (es lo que oye el operador):

```yaml
id: my_flow
start: first_step
escalate: escalate            # end step that creates a case; "human" jumps here
max_unclear_attempts: 2       # then keypad fallback (1 yes, 2 no, 0 human)
steps:
  - id: first_step
    text: "¿Una acción por turno?"
    on_yes: resolved
    on_no: escalate
    active_wait: false        # true: silence does not end the turn; check back every 20–30 s
  - id: resolved
    text: "Listo."
    end: true
  - id: escalate
    text: "Dejo un caso."
    end: true
    action: create_case
    destination: help_desk    # help_desk | census_office | logistics
    priority: normal          # normal | high
```

El motor **valida al arrancar**: transiciones a pasos inexistentes, pasos sin `on_yes` / `on_no`, ids repetidos o un `escalate` que no crea caso hacen fallar el arranque, no una llamada en vivo.

Las transiciones se llaman `on_yes` / `on_no` a propósito: en YAML 1.1 una clave `no:` sin comillas se lee como el booleano `False` (el "problema de Noruega").
