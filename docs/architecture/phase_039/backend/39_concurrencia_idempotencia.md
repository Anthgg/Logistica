# 39 concurrencia idempotencia

## Decisión

Los agregados se bloquean con SELECT FOR UPDATE. Una clave repetida con payload distinto es conflicto.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

