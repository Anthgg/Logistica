# 43 rendimiento

## Decisión

Los índices priorizan tenant, fuente, línea, código hash, estado y fechas. Las metas masivas requieren benchmark dedicado.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

