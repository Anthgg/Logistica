# Inventario de Endpoints del Backend · Fase 001

## 1. Resumen Estadístico de Endpoints

- **Total de Rutas (Paths):** 828
- **Total de Operaciones HTTP:** 973
  - **GET:** 399
  - **POST:** 513
  - **PATCH:** 40
  - **DELETE:** 13
  - **PUT:** 8

## 2. Desglose por Módulos y Prefijos

| Prefijo de Ruta | Operaciones | Propósito | Autenticación / Acceso |
| :--- | :--- | :--- | :--- |
| `/health`, `/live`, `/ready` | 3 | Liveness & Readiness probes | Público |
| `/api/health` | 1 | Health check con estado de BD | Público |
| `/api/auth/*` | 10 | Autenticación, CSRF, sesiones | Mixto (Público / Sesión activa) |
| `/api/continuous-auth/*` | 5 | Inferencia y evaluación biométrica | Sesión activa + RBAC |
| `/api/research/*` | 18 | Consentimiento, captura multimodal | Sesión activa / Investigador |
| `/api/logistics/*` | 894 | Operaciones de almacén, transporte, inventario | Sesión activa + RBAC |
| `/api/clients/*` | 8 | Gestión de clientes | Sesión activa + RBAC |
| `/api/incidents/*` | 6 | Registro de incidentes | Sesión activa + RBAC |
| `/api/reports/*` | 8 | Reportes analíticos | Sesión activa + RBAC |
| `/api/dashboard/*` | 4 | KPIs operativos | Sesión activa + RBAC |
| `/docs`, `/redoc`, `/openapi.json` | 3 | OpenAPI Specification | Público en desarrollo |

---

## 3. Endpoints Clave de la Fase 001 (Línea Base & Autenticación)

### 3.1 Probes & Health Checks
- `GET /health` -> `200 OK` (`{"status": "ok", "environment": "development", "version": "0.9.1"}`)
- `GET /live` -> `200 OK` (`{"status": "ok"}`)
- `GET /ready` -> `200 OK` (`{"status": "ok"}`)
- `GET /api/health` -> `200 OK` (`{"status": "ok", "environment": "development", "version": "0.9.1", "database": {"status": "connected"}}`)

### 3.2 Core Authentication (`/api/auth`)
- `GET /api/auth/csrf` -> Genera y retorna token CSRF en cookie y body JSON.
- `POST /api/auth/register` -> Registro con hashing Argon2id y validación de contraseña robusta.
- `POST /api/auth/login` -> Login con soporte Remember Me, reconocimiento de dispositivo y emisión de cookies HttpOnly JWT (`session_token`, `refresh_token`, `device_token`).
- `POST /api/auth/refresh` -> Rotación atómica de tokens con detección de reutilización y revocación inmediata.
- `GET /api/auth/me` -> Retorna usuario autenticado y detalles de sesión actual.
- `POST /api/auth/logout` -> Revocación de sesión actual y borrado de cookies.
- `POST /api/auth/logout-all` -> Revocación de todas las sesiones del usuario activo.
- `POST /api/auth/change-password` -> Cambio seguro de contraseña con revocación opcional de otras sesiones.
- `GET /api/auth/sessions` -> Listado de sesiones activas del usuario.

### 3.3 Continuous Authentication (`/api/logistics/continuous-auth` & `/api/continuous-auth`)
- `POST /api/continuous-auth/evaluate` -> Evaluación multimodal y cálculo de risk score.
- `GET /api/continuous-auth/status` -> Consulta del estado de autenticación continua.
- `POST /api/continuous-auth/facial/predict` -> Predicción biométrica facial.
- `POST /api/continuous-auth/behavioral/predict` -> Predicción de patrones de tecleo y mouse.
- `POST /api/continuous-auth/pad/predict` -> Detección de ataques de presentación (liveness).

---

## 4. Convención de Envelope y Formato de Errores

Todos los errores retornan un formato canónico estandarizado:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Las credenciales no son válidas.",
    "request_id": "893d9fc0-d46e-4f1e-8e5e-6e426db4fbd3",
    "timestamp": "2026-08-15T08:27:23.123456Z",
    "details": null
  }
}
```

El header `X-Request-ID` se propaga de manera uniforme en todas las respuestas HTTP (2xx, 4xx, 5xx).
