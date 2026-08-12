# 45 runbook serie duplicada

## Decisión

Bloquear la captura, revisar hash y alcance, conservar intentos y escalar como candidato.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

