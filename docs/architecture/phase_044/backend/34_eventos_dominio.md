# 34 — Eventos de dominio

Publicados (outbox):

- `InventoryMovementPostingRequested`
- `InventoryMovementValidated`
- `InventoryMovementPosted`
- `InventoryMovementDuplicateDetected`
- `InventoryMovementPostingFailed`
- `InventoryMovementCompensationRequested`
- `InventoryMovementCompensationApproved`
- `InventoryMovementCompensated`
- `InventoryLedgerIntegrityFailed`
- `InventoryLedgerCheckpointCreated`
- `InventoryLedgerCheckpointFailed`
- `QualityMovementMaterialized`
- `PutawayMovementMaterialized`
- `InventoryBalancePreparationReady`
- `InventoryTraceabilityPreparationReady`

**No publicados**:

- `InventoryBalanceUpdated` (Fase 045).
- `StockManuallyEdited`.
- `LotMasterCreated`, `SerialMasterCreated`.
