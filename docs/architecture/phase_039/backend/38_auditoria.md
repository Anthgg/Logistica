# 38 auditoria

## Decisión

Se registra actor, sesión, tenant, almacén, recepción, resultado y correlación; no tokens, biometría ni payload completo.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

