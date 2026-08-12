# 09 sesiones escaneo

## Decisión

Las sesiones son multioperador, usan reloj de servidor y no almacenan credenciales del dispositivo.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

