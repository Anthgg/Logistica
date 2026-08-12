# 05 — `InventoryMovementPostingRequest`

Modelo `inventory_movement_posting_requests`.

| Campo | Tipo |
|-------|------|
| `id` | UUID |
| `organization_id` | UUID |
| `request_key` | VARCHAR(128) |
| `source_system` | VARCHAR(60) |
| `source_event_type` | VARCHAR(80) |
| `source_event_id` | VARCHAR(120) |
| `source_event_version` | INTEGER |
| `payload_hash` | VARCHAR(64) |
| `payload` | JSONB |
| `status` | VARCHAR(30) |

Estados: `RECEIVED`, `VALIDATING`, `VALID`, `POSTING`, `POSTED`, `DUPLICATE`,
`FAILED`, `CANCELLED`.

Hash SHA-256 sobre payload canónico. Constraint UNIQUE
`(organization_id, source_system, source_event_type, source_event_id,
source_event_version)`.
