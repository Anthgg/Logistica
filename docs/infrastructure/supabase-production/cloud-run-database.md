# Google Cloud Run · Configuración y Operación del Servicio

## 1. Identificación del Servicio

- **Servicio:** `autenticacion-continua-api`
- **Proyecto GCP:** `gen-lang-client-0356667380`
- **Región:** `southamerica-west1` (Santiago de Chile)
- **URL Pública:** `https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app`
- **Revisión Activa:** `autenticacion-continua-api-v0-9-8-final-20260810`
- **Imagen:** `southamerica-west1-docker.pkg.dev/gen-lang-client-0356667380/cloud-run-source-deploy/autenticacion-continua-api:v0.9.8-20260810-2248-final`

---

## 2. Variables de Entorno y Configuración de Runtime

| Variable | Valor / Tipo | Propósito |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Activa validaciones estrictas y modo producción |
| `COOKIE_SECURE` | `true` | Exige cookies HTTPS exclusivamente |
| `RUN_MIGRATIONS` | `false` | Deshabilita migraciones automáticas al inicio de contenedores para evitar colisiones concurrentes |
| `APP_VERSION` | `0.9.8` | Versión del backend expuesta en OpenAPI y health |
| `DATABASE_URL` | *Secret Redacted* | Cadena de conexión hacia Supabase PostgreSQL |
| `FRONTEND_URL` | *Configured Domain* | Origen permitido para CORS y cabeceras de seguridad |
| `SECRET_KEY` | *Secret Redacted* | Firma de tokens JWT y sesiones |

---

## 3. Pruebas de Humo en Vivo

### Health Check (`GET /api/health`):
- **HTTP Status:** `200 OK`
- **Database Status:** `connected`
- **Payload:**
  ```json
  {
    "status": "ok",
    "service": "Continuous Authentication API",
    "version": "0.9.8",
    "environment": "production",
    "database": {
      "status": "connected"
    },
    "timestamp": "2026-08-16T23:51:29.633177Z"
  }
  ```

### Catálogo OpenAPI (`GET /openapi.json`):
- **Total Rutas Registradas:** `818`
- **Estado:** `200 OK`
