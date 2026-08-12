# 17 series observadas

## Decisión

Las series conservan ceros, se hashean para búsqueda y se bloquean duplicados activos dentro de la recepción.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

