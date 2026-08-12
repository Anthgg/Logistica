# 49 integracion fase 083

## Decisión

Integraciones futuras consumirán eventos y snapshots, nunca modificarán eventos históricos.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

