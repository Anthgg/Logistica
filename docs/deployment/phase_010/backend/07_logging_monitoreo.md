# 07 — Logging Estructurado, Trazabilidad y Monitoreo

## Estructura de Registros JSON (`LOG_FORMAT=json`)
En los ambientes de `staging` y `production`, los logs se generan en formato estructurado JSON compatible con **Google Cloud Logging**:
```json
{
  "timestamp": "2026-07-26T21:20:00.000Z",
  "level": "INFO",
  "service": "Continuous Authentication API",
  "environment": "production",
  "version": "0.9.1",
  "request_id": "req-8f3b2a1c",
  "correlation_id": "corr-9b4c3d2e",
  "method": "POST",
  "path": "/api/logistics/role-assignments",
  "status_code": 201,
  "duration_ms": 14.2
}
```

## Middleware de Request ID & Propagación
El middleware `RequestLoggingMiddleware` genera un `request_id` único para cada petición y propaga la cabecera `X-Request-ID` en la respuesta.
