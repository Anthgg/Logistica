# 08 lineas recibidas

## Decisión

La cantidad base es derivada por el backend mediante reglas aprobadas. Las líneas inesperadas quedan para revisión.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

