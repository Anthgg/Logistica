# 03 — Gestión Segura de Secretos

## Almacenamiento e Inyección de Secretos
En `staging` y `production`, los secretos son administrados mediante **Google Secret Manager** e inyectados directamente como variables de entorno a las revisiones de **Google Cloud Run**.

## Inventario de Secretos (`[SECRETO]`)

| Nombre del Secreto en Secret Manager | Descripción | Servicio Consumidor | Policy de Rotación |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Cadena de conexión PostgreSQL cifrada | SQLAlchemy Pool | 90 días |
| `SECRET_KEY` | Clave maestra para firma de cookies/tokens | Security Middleware | 90 días |
| `CSRF_SECRET` | Clave secreta para tokens CSRF | CSRF Middleware | 90 días |

## Prohibiciones de Seguridad
* NUNCA incluir claves reales en archivos `.env`, `.env.example`, Dockerfiles o imágenes subidas a repositorios públicos.
* NUNCA imprimir variables catalogadas como secretas en los registros estructurados de aplicación.
