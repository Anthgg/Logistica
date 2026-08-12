# 23 tolerancias

## Decisión

Las políticas son versionadas; los excesos no se autoaprueban ni se convierten en ajustes.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

