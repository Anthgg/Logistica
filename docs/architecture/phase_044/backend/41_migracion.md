# 41 — Migración Alembic

Migración de tablas: `gg440110044dc_phase_044_inventory_ledger.py`.

Head único: `gh440210044mg_merge_phase044_and_driver_repair.py`, revisión de
merge sin DDL que une `gg440110044dc` con la reparación ya desplegada
`ad390210039dr` sin reescribir historia.

Tablas creadas:

1. `inventory_ledger_partitions`
2. `inventory_positions`
3. `inventory_external_boundaries`
4. `inventory_movement_posting_requests`
5. `inventory_movements`
6. `inventory_movement_lines`
7. `inventory_movement_source_references`
8. `inventory_movement_compensation_requests`
9. `inventory_ledger_checkpoints`
10. `inventory_ledger_reconciliation_jobs`
11. `inventory_ledger_reconciliation_results`
12. `inventory_kardex_export_jobs`
13. `inventory_ledger_outbox_events`

Constraints:

- UNIQUE `(organization_id, normalized_movement_code)`.
- UNIQUE `(ledger_partition_key, ledger_sequence)`.
- UNIQUE `(organization_id, source_system, source_event_type,
  source_event_id, source_event_version)`.
- UNIQUE `(inventory_movement_id, line_number)`.
- UNIQUE `(ledger_partition_key, from_sequence, to_sequence)`.
- CHECK `quantity > 0`, `base_quantity > 0`.
- CHECK `source_position_id` OR `source_external_boundary_kind`.
- CHECK `destination_position_id` OR `destination_external_boundary_kind`.

Antes de crear el ledger, la migración detecta el esquema legacy por sus
columnas y renombra `inventory_movements` a `inventory_movements_legacy`. El
downgrade elimina las tablas nuevas y restaura el nombre legacy cuando existe.
Las líneas tienen FKs a posiciones/fronteras y checks XOR de origen/destino.

Validación local: `alembic heads` devuelve sólo `gh440210044mg`. No se ejecutó
`upgrade` contra la base remota o producción en esta fase.
