# 12 resolucion producto

## Decisión

La resolución es exacta, activa y acotada al tenant. Ambigüedad y desconocido bloquean aplicación automática.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

