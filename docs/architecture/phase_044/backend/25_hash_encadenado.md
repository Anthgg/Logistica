# 25 — Hash encadenado

`compute_movement_hash` toma:

- `ledger_partition_key`
- `ledger_sequence`
- `movement_code`
- `movement_type`, `movement_family`
- `organization_id`, `branch_id`
- `source_event_id`, `source_event_version`
- `occurred_at`, `posted_at`
- `reason_code`, `compensation_for_movement_id`
- `previous_movement_hash`
- ordered lines
- ordered source references

Algoritmo: SHA-256 sobre canonical JSON con `canonicalization_version`.

No se llama "blockchain" ni "firma digital". No se recalcula con datos
actuales. Si una verificación falla, el movimiento se marca
`INTEGRITY_FAILED` y se bloquean las dependencias.
