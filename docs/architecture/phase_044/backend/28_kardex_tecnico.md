# 28 — Kardex técnico

`InventoryKardexQueryService.list_movements`:

Filtros: organización, branch, almacén, ubicación, producto, SKU, familia,
tipo, status, disponibilidad, calidad, tránsito, damage, expiración,
fuente, evento, usuario, rango occurred/posted, compensado, integridad,
secuencia, correlation_id.

Cada fila (sin saldo firmado autoritativo) muestra:

- `ledger_sequence`, `movement_code`, `movement_type`, `movement_family`, `status`
- `occurred_at`, `posted_at`
- producto, cantidad, unidad, base, base_unit
- posiciones origen / destino
- `source_document_code`, `reason_code`
- `movement_hash_partial` (16 chars)
- `compensation_status`
- `signed_quantity_display` (solo si la dimensión está definida)
- `data_quality_status`
- `capabilities`
