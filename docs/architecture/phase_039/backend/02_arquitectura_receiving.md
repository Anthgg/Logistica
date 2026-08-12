# 02 arquitectura receiving

## Decisión

El bounded context separa dominio, aplicación, persistencia, jobs y presentación. La autoridad de cantidades base, actor y tiempos queda en el servidor.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

