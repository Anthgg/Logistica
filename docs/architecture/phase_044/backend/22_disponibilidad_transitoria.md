# 22 — `InventoryAvailabilityProvider`

Esta fase implementa `SourceBackedAvailabilityProvider`:

- `INBOUND_ALLOCATION` → `InboundInventoryDispositionAllocation`.
- `OPERATIONAL_PLACEMENT` → `OperationalInventoryPlacement`.

Los métodos:

- `get_available_quantity`
- `validate_source_quantity`
- `validate_reservation_quantity`
- `validate_transfer_quantity`

Fase 045 reemplazará con `InventoryBalanceAvailabilityProvider`. Hasta
entonces los movimientos respaldados por eventos son los únicos
habilitados. No se permiten salidas genéricas.
