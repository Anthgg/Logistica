# 09 — Fronteras externas

`InventoryExternalBoundaryKind`:

- `SUPPLIER`
- `CUSTOMER`
- `CARRIER`
- `OUTSIDE_WAREHOUSE`
- `OPENING_BALANCE` (solo Fase 098)
- `TECHNICAL_COMPENSATION`
- `UNKNOWN_EXTERNAL`

Una entrada de proveedor mueve cantidad desde la frontera `SUPPLIER` hacia
una posición interna. Una salida hacia cliente mueve de posición interna
a frontera `CUSTOMER`. Las fronteras externas nunca forman parte del saldo
interno.
