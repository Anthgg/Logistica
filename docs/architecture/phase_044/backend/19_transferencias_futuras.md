# 19 — Transferencias entre almacenes (sólo contrato)

Tipos:

- `TRANSFER_DISPATCH_FUTURE`: ubicación origen → IN_TRANSIT.
- `WAREHOUSE_TRANSFER_IN_TRANSIT_FUTURE`: IN_TRANSIT.
- `TRANSFER_RECEIPT_FUTURE`: IN_TRANSIT → almacén destino.

No se implementa la lógica de despacho/recepción. La Fase 049 y 050 lo
harán. Cualquier transferencia debe pasar por el estado `IN_TRANSIT`.
