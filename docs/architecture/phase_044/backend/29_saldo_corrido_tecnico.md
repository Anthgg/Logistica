# 29 — Saldo corrido técnico

`InventoryKardexRunningQuantityService.compute_technical_running_quantity` requiere:

- `organization_id`
- `warehouse_id`
- `product_id`
- `base_unit_id`
- `position_id` o conjunto exacto de estados
- `sequence_from` / `sequence_to`

Salida:

- `ledger_sequence`
- `signed_delta`
- `running_quantity_reference`
- `data_quality_status`
- `calculation_scope = TECHNICAL_REPLAY`

Ámbitos ambiguos → `InventoryKardexScopeAmbiguous`. Mezcla de unidades →
`InventoryKardexUnitMismatch`. Es **consulta derivada**, no saldo
operativo. La Fase 045 implementará saldos persistentes.
