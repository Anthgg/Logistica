# 36 endpoints

## Decisión

Los estados cambian con POST de intención; no hay PATCH de estado ni DELETE de eventos.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

