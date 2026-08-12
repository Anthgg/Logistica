# 04 — Modelo `InventoryMovement`

## Tabla: `inventory_movements`

Campos clave:

| Campo | Tipo | Restricción |
|-------|------|-------------|
| `id` | UUID | PK |
| `organization_id` | UUID | not null, index |
| `branch_id` | UUID | not null, index |
| `warehouse_scope_id` | UUID | null, index |
| `movement_code` | VARCHAR(80) | not null |
| `normalized_movement_code` | VARCHAR(80) | not null, unique por org |
| `ledger_partition_key` | VARCHAR(120) | not null, index |
| `ledger_sequence` | INTEGER | not null, unique dentro de la partición |
| `movement_type` | VARCHAR(60) | not null, index |
| `movement_family` | VARCHAR(40) | not null, index |
| `status` | VARCHAR(40) | default = POSTED |
| `source_event_id` | VARCHAR(120) | not null, index |
| `occurred_at` | TIMESTAMP | not null, index |
| `posted_at` | TIMESTAMP | not null, server time |
| `line_count` | INTEGER | not null |
| `previous_movement_hash` | VARCHAR(64) | null, index |
| `movement_hash` | VARCHAR(64) | not null, index |
| `compensation_for_movement_id` | UUID | null, FK |
| `compensated_by_movement_id` | UUID | null, FK |
| `row_version` | INTEGER | not null, default = 1 |

## Estados

- `POSTED` — único estado mutable al alta.
- `COMPENSATED` — se setea desde `InventoryMovementCompensationService`.
- `PARTIALLY_COMPENSATED` — deriva de compensaciones parciales.
- `INTEGRITY_FAILED` — se setea por verificación fallida.
- `SUPERSEDED_BY_MIGRATION` — reservado para la Fase 098.

## Inmutabilidad

- No hay endpoint PATCH.
- No hay endpoint DELETE.
- Correcciones via `InventoryMovementCompensationService`.
- `posted_at` siempre proviene del servidor.
