# 26 — Checkpoints

`InventoryLedgerCheckpoint`:

- `from_sequence`, `to_sequence`.
- `first_hash`, `last_hash`, `manifest_hash`.
- `verification_status`.
- `verified_at`, `verified_by_service`.

Se generan asincronamente. Permiten verificar rangos grandes sin
recorrer cada movimiento. No modifican el libro.
