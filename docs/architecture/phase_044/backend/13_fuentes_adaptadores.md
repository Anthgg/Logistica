# 13 — `InventoryMovementSourceRegistry`

Adaptadores habilitados en Fase 044:

- `QUALITY_QUARANTINE_APPLIED`
- `QUALITY_APPROVED`
- `QUARANTINE_RELEASED`
- `QUALITY_REJECTED`
- `DISPOSITION_SPLIT`
- `PUTAWAY_COMPLETED`

Adaptadores futuros (deshabilitados):

- `ADJUSTMENT_APPROVED`
- `PHYSICAL_COUNT_VARIANCE_APPROVED`
- `TRANSFER_DISPATCHED`
- `TRANSFER_RECEIVED`
- `RESERVATION_CREATED`
- `RESERVATION_RELEASED`
- `OUTBOUND_PICK_CONFIRMED`
- `OUTBOUND_DISPATCH_CONFIRMED`
- `RETURN_RECEIVED`

Cada adaptador implementa `InventoryMovementSourceAdapter`:
- `validate_source(organization_id, payload)`
- `build(organization_id, payload) -> PreparedMovement`
- `adapter_name`, `adapter_version`, `enabled`

El adaptador construye las líneas con `quantity_direction`, snapshots de
origen / destino, referencias y emite un `idempotency_key` por source event.
