# 47 runbook recepcion abandonada

## Decisión

Expirar sesión, preservar eventos, recalcular avance y requerir una nueva sesión autenticada.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

