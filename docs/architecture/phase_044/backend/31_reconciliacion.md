# 31 — Reconciliación

`InventoryLedgerReconciliationService.run`:

Resultados posibles:

- `RECONCILED`
- `SOURCE_EVENT_MISSING_MOVEMENT`
- `MOVEMENT_WITHOUT_SOURCE`
- `QUANTITY_MISMATCH`
- `DUPLICATE_SOURCE`
- `HASH_MISMATCH`
- `ADAPTER_VERSION_MISMATCH`
- `REQUIRES_REVIEW`

No corrige automáticamente. No edita movimientos. Genera reporte.
Step-up HIGH.
