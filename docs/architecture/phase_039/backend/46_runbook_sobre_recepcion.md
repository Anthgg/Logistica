# 46 runbook sobre recepcion

## Decisión

Detener aplicación fuera de tolerancia, validar OC y política, y preparar candidato de sobrante.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

