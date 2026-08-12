# 10 — Health Probes y Smoke Tests

## Probes de Aplicación

| Endpoint | Propósito | Respuesta Esperada |
| :--- | :--- | :--- |
| `GET /health` | Probe de salud general | `{"status": "ok", "environment": "production", "version": "0.9.1"}` |
| `GET /ready` | Readiness (Servicio listo para recibir tráfico) | `{"status": "ready", "environment": "production", "version": "0.9.1"}` |
| `GET /live` | Liveness (Proceso contenedor activo) | `{"status": "ok", "environment": "production", "version": "0.9.1"}` |
| `GET /api/health` | Diagnostic check con conectividad a DB | `{"status": "ok", "database": {"status": "connected"}}` |

## Script de Smoke Testing Post-Despliegue
Tras desplegar una nueva revisión en Cloud Run, el pipeline ejecuta verificaciones automatizadas sobre `/health`, `/ready`, `/api/logistics/health` y `/openapi.json` antes de confirmar la liberación.
