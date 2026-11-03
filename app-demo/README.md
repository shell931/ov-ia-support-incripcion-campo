# app-demo — demo por llamada (propuesta 6)

Código de la demo de la [propuesta 6](../propuesta-6/README.md). Plan y tareas: [plan-de-accion.md](../propuesta-6/plan-de-accion.md).

## Qué hay hoy

| Pieza | Estado |
| --- | --- |
| `core/engine.py`: motor de flujos determinista | ✅ con 42 tests |
| `core/flows/*.yaml`: los tres flujos (textos del PDF, **pendientes de validación por procesos**) | ✅ |
| `core/api.py`: `GET /salud` | ✅ |
| `migrations/001_inicial.sql`: `sesiones`, `casos`, `eventos` | ✅ |
| `docker-compose.yml`: Postgres 16 + núcleo | ✅ (falta probar `docker compose up`) |
| `POST /siguiente-paso`, `POST /casos` | ⬜ D2.3 / D3.6 |
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
curl localhost:8000/salud
```

Postgres corre **dentro del compose** (imagen oficial `postgres:16-alpine`), igual en la notebook, en la VM y en el datacenter. Si algún día se usa uno administrado (Supabase, RDS…), se cambia solo `DATABASE_URL` y se usa como Postgres plano.

## Reglas (resumen del plan)

- `core/` no importa nada de LiveKit ni de SDKs de proveedores.
- El texto que oye el operador sale **del YAML**; el LLM solo clasifica.
- La cédula nunca se guarda completa.
- Ningún proveedor fijo en el código: todo sale de `.env`.

## Escribir un flujo

```yaml
id: mi_flujo
inicio: primer_paso
escalar: escalar              # paso final que crea caso; "persona" salta acá
max_intentos_no_entendi: 2    # después, respaldo por teclado (1 sí, 2 no, 0 persona)
pasos:
  - id: primer_paso
    texto: "¿Una acción por turno?"
    si: resuelto
    no: escalar
    espera_activa: false      # true: el silencio no corta, se pregunta cada 20–30 s
  - id: resuelto
    texto: "Listo."
    fin: true
  - id: escalar
    texto: "Dejo un caso."
    fin: true
    accion: crear_caso
    destino: mesa             # mesa | direccion_censo | logistica
    prioridad: normal         # normal | alta
```

El motor **valida al arrancar**: transiciones a pasos inexistentes, pasos sin `si`/`no`, ids repetidos o un `escalar` que no crea caso hacen fallar el arranque, no una llamada en vivo.

`no:` sin comillas funciona: YAML 1.1 lo lee como booleano (el "problema de Noruega") y el cargador lo contempla.
