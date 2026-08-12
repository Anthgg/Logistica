# 33 — Preparación para Fase 046 (trazabilidad)

`InventoryTraceabilityPreparationService`:

- `movement_id`, `movement_line_id`
- `product_id`, `product_version_id`
- `source_position`, `destination_position` (snapshots)
- `traceability_reference_type`
- `observed_lot_references`, `observed_serial_references`,
  `expiration_observations`
- `packaging_snapshot`
- `handling_unit_reference_hash`
- `quantity`, `unit`
- `movement_hash`

No se crean entidades `lot_master` ni `serial_master` en esta fase.
