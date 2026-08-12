# 10 eventos escaneo

## Decisión

Los eventos son append-only, ordenados por server_sequence e idempotentes por sesión y client_scan_id.

## Invariantes

Aplican aislamiento por organización, reloj y actor de servidor, idempotencia en comandos y ausencia de efectos de inventario.

## Verificación

Consultar backend/tests/test_logistics_phase039.py y el contrato OpenAPI efectivo.

