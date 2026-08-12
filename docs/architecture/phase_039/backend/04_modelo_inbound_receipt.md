# 04 modelo inbound receipt

## Decisión

InboundReceipt vincula exactamente una descarga completada activa, su almacén, proveedor, revisión y contadores proyectados.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

