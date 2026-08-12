# 22 comparacion ordenado enviado recibido

## Decisión

La comparación calcula ordenado, enviado, recibido, saldo y varianza por línea sin sumar dimensiones incompatibles.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

