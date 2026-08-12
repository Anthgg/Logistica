# 41 migracion

## Decisión

ac390110039dc crea y revierte 18 tablas. No se ejecuta contra producción en esta entrega.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

