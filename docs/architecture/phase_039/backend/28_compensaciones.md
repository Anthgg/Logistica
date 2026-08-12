# 28 compensaciones

## Decisión

Un evento aplicado se revierte mediante un evento compensatorio; el original no se edita ni borra.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

