# Despliegue de la demo en EC2 (us-east-1)

Una sola instancia corre todo con `docker compose`: **web** (Caddy + consola Angular), **core** y, desde D1.4, **voice-agent**. La base es el proyecto de **Supabase** que ya existe (us-east-1).

```text
Internet ──443──► EC2 (us-east-1)
                  ├─ web    Caddy: HTTPS, consola, /api/cases* (con contraseña)
                  ├─ core   API interna :8000 (no pública)
                  └─ voice-agent ──► LiveKit Cloud (conexión saliente, sin puertos abiertos)
                         │
                         └──► Supabase (us-east-1)  vía DATABASE_URL
```

## 1. Crear la instancia

| Opción | Valor | Por qué |
| --- | --- | --- |
| Región | **us-east-1** (N. Virginia) | La misma que Supabase y que los proveedores de voz. |
| AMI | Ubuntu Server 24.04 LTS (x86_64) | Estándar, con Docker oficial. |
| Tipo | **t3.medium** (2 vCPU, 4 GB) | Alcanza para la demo: la voz se procesa en LiveKit y Deepgram. Subir a t3.large si el agente pide más. |
| Disco | 30 GB gp3 | Imágenes de Docker y logs. |
| Key pair | Una nueva (`.pem`), guardada fuera del repo | Acceso por SSH. |
| IP | **Elastic IP** asociada | La dirección no cambia si se reinicia; la necesita el certificado HTTPS. |

**Security group** (lo mínimo):

| Puerto | Origen | Para qué |
| --- | --- | --- |
| 22 (SSH) | **Solo tu IP** | Administración. Nunca `0.0.0.0/0`. |
| 80 (HTTP) | 0.0.0.0/0 | Let's Encrypt valida el certificado y Caddy redirige a HTTPS. |
| 443 (HTTPS) | 0.0.0.0/0 | Consola de la mesa. |

El agente de voz **no necesita puertos de entrada**: se conecta hacia LiveKit Cloud.

## 2. Preparar la instancia

```bash
ssh -i <clave>.pem ubuntu@<elastic-ip>

# Docker oficial + plugin compose
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && exit   # volver a entrar para que tome el grupo

ssh -i <clave>.pem ubuntu@<elastic-ip>
git clone https://github.com/shell931/ov-ia-support-incripcion-campo
cd ov-ia-support-incripcion-campo/app-demo
cp .env.example .env
```

## 3. Configurar `.env` en la instancia

Las claves se escriben **directo en la instancia** (`nano .env`), nunca en el repo ni en un chat.

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | La misma cadena del *Session pooler* de Supabase, con `?sslmode=require` al final. |
| `SITE_ADDRESS` | Un dominio que apunte a la Elastic IP. Sin dominio, para la demo: `<ip-con-guiones>.sslip.io` (ej. `3-90-12-34.sslip.io`). Caddy saca el certificado HTTPS solo. |
| `CONSOLE_USER` | Usuario de la mesa, ej. `mesa`. |
| `CONSOLE_PASSWORD_HASH` | Hash de la contraseña, **entre comillas simples**: `docker run --rm caddy:2.10-alpine caddy hash-password --plaintext '<contraseña>'` |
| LiveKit, Deepgram, Anthropic | Cuando estén las cuentas (D1.3 en adelante). |

## 4. Levantar

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f core web
```

Verificación:

```bash
curl -s localhost:8000/health                  # dentro de la instancia: {"status":"ok","postgres":true,...}
curl -sI https://<SITE_ADDRESS>                # 401: pide usuario y contraseña (correcto)
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://<SITE_ADDRESS>/api/next-step   # 401/404: no expuesto
```

En el navegador: `https://<SITE_ADDRESS>` → usuario y contraseña → cola de casos.

## 5. Actualizar a una versión nueva

```bash
cd ~/ov-ia-support-incripcion-campo && git pull
cd app-demo && docker compose up -d --build
```

Las migraciones de la base se aplican solas al arrancar `core`.

## Seguridad: lo que NO hay que hacer

- Abrir el puerto 22 o el 8000 a todo internet.
- Publicar la consola sin contraseña: muestra teléfonos de operadores.
- Poner datos reales de operadores mientras el modo nube use proveedores fuera del país (Ley 1581): **cédulas ficticias en la demo**.
- Copiar el `.env` de la notebook a un repo, un chat o un documento.

## Costo aproximado

t3.medium ≈ 30 US$/mes encendida 24×7, más la Elastic IP y 30 GB de disco (unos pocos dólares). Se puede **apagar fuera de los ensayos**: la Elastic IP y los datos se conservan (la IP asociada a una instancia apagada tiene un costo chico por hora).
