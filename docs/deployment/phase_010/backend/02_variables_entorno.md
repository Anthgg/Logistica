# 02 — Catálogo de Variables de Entorno

## Variables Principales

| Categoría | Nombre | Tipo | Default | Requerido en Prod |
| :--- | :--- | :--- | :--- | :--- |
| **Aplicación** | `APP_ENV` | `local\|test\|staging\|production` | `local` | Sí |
| **Aplicación** | `APP_NAME` | String | `"Continuous Auth API"` | Sí |
| **Aplicación** | `APP_VERSION` | String | `"0.9.1"` | Sí |
| **Aplicación** | `PORT` | Integer | `8080` (Cloud Run) | Sí |
| **Aplicación** | `LOG_LEVEL` | `DEBUG\|INFO\|WARNING\|ERROR` | `"INFO"` | Sí |
| **Aplicación** | `LOG_FORMAT` | `text\|json` | `"text"` | Sí |
| **Seguridad** | `SECRET_KEY` | SecretStr | `[SECRETO]` | Sí |
| **Seguridad** | `COOKIE_SECURE` | Boolean | `true` (prod) | Sí |
| **Seguridad** | `SESSION_COOKIE_SAMESITE` | `lax\|strict\|none` | `"strict"` | Sí |
| **Base de Datos** | `DATABASE_URL` | SecretStr | `[SECRETO]` | Sí |
| **Base de Datos** | `DATABASE_POOL_SIZE` | Integer | `10` | No |
| **Biometría** | `CONTINUOUS_AUTH_ENABLED` | Boolean | `true` | No |
| **Biometría** | `STEP_UP_ENABLED` | Boolean | `true` | No |
| **Biometría** | `RISK_POLICY_VERSION` | String | `"1.0.0"` | No |
