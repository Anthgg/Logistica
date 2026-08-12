# 18 vencimientos

## Decisión

Se usan fechas de calendario, se valida orden fabricación-vencimiento y los vencidos generan revisión futura.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

