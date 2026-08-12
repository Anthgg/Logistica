# 27 escaneos no resueltos

## Decisión

Se permite asociar a producto o línea existentes, rechazar o marcar duplicado. No se crea catálogo permanente.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

