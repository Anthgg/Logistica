# 30 cierre snapshot

## Decisión

El cierre congela revisión y snapshots, usa operador autenticado y tiempo del servidor.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

