# Consola de la mesa

Aplicación web interna (Angular 22, componentes standalone, signals) para el personal de la mesa de ayuda del demo de soporte por voz. Muestra la cola de casos que el agente de voz no pudo resolver, permite abrir un caso, ver qué intentó el agente (pasos y transcripción), tomarlo, llamar al operador y cerrarlo con un motivo.

No hay inicio de sesión: la primera vez que alguien toma un caso se le pide su nombre, que se guarda en `localStorage` y se envía como `taken_by`.

## Ejecutar en local

Requiere Node 22 y el core corriendo en `http://localhost:8000`.

```bash
npm ci
npm start
```

Abra http://localhost:4200. El archivo `proxy.conf.json` redirige `/api/*` a `http://localhost:8000/*` (quitando el prefijo `/api`).

Pruebas unitarias: `npm test`.

## Docker

El `Dockerfile` es multi-etapa:

1. `node:22-alpine`: `npm ci` y `npx ng build --configuration production`.
2. `caddy:2.10-alpine`: copia `dist/console/browser` a `/srv`.

El Caddyfile no está en esta carpeta: se monta en `/etc/caddy/Caddyfile` (lo provee `app-demo/Caddyfile`). Caddy sirve la app en `/` y reenvía `/api` al core (mismo origen, sin CORS).

## API utilizada

Prefijo `/api`. Los errores llegan como `{ "detail": string }` y se muestran en pantalla.

- `GET /api/cases?status=open|taken|closed` (sin `status`: abiertos y tomados). La cola consulta cada 5 s.
- `GET /api/cases/{number}`: detalle con `steps_tried`, `transcript`, `close_reason`, `notes`.
- `POST /api/cases/{number}/take` con `{ "taken_by": string }`. 409 si otra persona ya lo tomó.
- `POST /api/cases/{number}/close` con `{ "close_reason": "resolved_by_phone" | "tablet_replaced" | "sent_to_census" | "other", "notes": string }`. 409 si ya está cerrado.

## Estructura

- `src/app/cases/`: modelo, servicio HTTP, cola y detalle.
- `src/app/shared/labels.ts`: textos en español (destinos, prioridad, estados, motivos de cierre).
- `src/app/shared/staff-name.service.ts`: nombre del funcionario en `localStorage`.
