# 01 auditoria recepcion existente

## Decisión

Se reutilizan descarga completada, avisos, órdenes DDD, productos, unidades, archivos, RBAC, step-up y outbox. No existía un agregado de recepción física.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

