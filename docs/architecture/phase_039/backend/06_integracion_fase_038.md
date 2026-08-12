# 06 integracion fase 038

## Decisión

ReceivingScanPreparationService es la fuente de traspaso. Se valida status COMPLETED y se conserva el snapshot de la descarga.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

