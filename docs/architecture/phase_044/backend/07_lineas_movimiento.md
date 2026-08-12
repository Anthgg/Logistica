# 07 — `InventoryMovementLine`

Cada movimiento tiene una o más líneas. Reglas:

- `quantity > 0` y `base_quantity > 0` (CHECK).
- `quantity_direction` ∈ `ENTRY / EXIT / TRANSFER / STATE_CHANGE /
  RESERVATION_CHANGE / COMPENSATION`.
- `source_position_id` o `source_external_boundary_kind` requerido.
- `destination_position_id` o `destination_external_boundary_kind` requerido.
- source != destination.
- `content_hash` = SHA-256(Canonical JSON de campos relevantes).
- `product_id` inmutable entre source y destination.
- `unit_id` y `base_unit_id` presentes siempre.
- `conversion_rule_id` requiere `conversion_snapshot`.
