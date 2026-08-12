# 37 permisos step up

## Decisión

Los permisos son granulares y no dependen de roles hardcodeados. Las acciones sensibles fallan cerradas.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

