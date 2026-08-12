# 40 jobs

## Decisión

Los jobs son funciones invocables por scheduler externo; no existen timers residentes en el proceso web.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

