# 20 entrada manual

## Decisión

La entrada manual exige permiso y step-up; actor, hora y cantidad base son servidor.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

