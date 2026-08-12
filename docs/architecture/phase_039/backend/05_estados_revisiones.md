# 05 estados revisiones

## Decisión

Las transiciones se ejecutan mediante comandos. Las revisiones congeladas son inmutables y cualquier corrección exige una revisión nueva.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

