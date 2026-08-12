# 01 — Definición y Separación de Ambientes

## Matriz de Ambientes (`APP_ENV`)

| Ambiente | Propósito | Base de Datos | Formato Logs | Debug | CORS Frontend Allowed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`local`** | Desarrollo individual | PostgreSQL local (`5432`) | Coloreado / Texto | `True` | `http://localhost:5173` |
| **`test`** | Pruebas automatizadas | DB efímera / Aislada | Texto plano | `False` | Restringido |
| **`staging`** | Pruebas UAT & Sandbox | Cloud SQL / Supabase Staging | JSON Estructurado | `False` | `https://staging.proyecto-t1.com` |
| **`production`** | Entorno real en producción | Base de datos administrada | JSON Estructurado | `False` | Dominios oficiales |

## Reglas Estrictas
1. `production` requiere obligatoriamente `COOKIE_SECURE=true`.
2. Las claves y secretos de producción DEBEN ser inyectados desde Google Secret Manager.
