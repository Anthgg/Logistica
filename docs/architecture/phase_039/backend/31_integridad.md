# 31 integridad

## Decisión

Hashes SHA-256 con canonicalización versionada detectan alteraciones; no se denominan firma digital.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

