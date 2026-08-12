# 32 — Preparación para Fase 045 (saldos)

`InventoryBalancePreparationService.for_ledger` produce por línea:

- `movement_id`, `movement_line_id`
- `ledger_sequence`
- `organization_id`, `warehouse_id`, `position_id`
- `product_id`, `product_version_id`
- `unit_id`, `base_unit_id`
- `entry_base_quantity`, `exit_base_quantity`
- `signed_delta_for_position`
- `availability_state`, `quality_state`, `transit_state`, `damage_state`,
  `expiration_state`
- `occurred_at`, `posted_at`
- `movement_hash`, `source_hash`
- `compensation_status`
- `balance_materialization_key`

La Fase 045 consumirá este servicio como **única fuente** para construir
la tabla de saldos. No se crea tabla de saldos en esta fase.
