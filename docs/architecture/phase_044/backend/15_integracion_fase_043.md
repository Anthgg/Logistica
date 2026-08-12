# 15 — Integración Fase 043 (`putaway`)

Se consumen:

- `OperationalInventoryPlacementModel`.
- `PutawayPlacementConfirmationModel`.
- `PutawayTask`, `PutawayOrder`.

Se materializa:

- `PUTAWAY_COMPLETED`: origen = staging aprobado, destino = ubicación
  física de almacenamiento.

Reglas:

- Una confirmación produce como máximo una línea activa.
- Cantidad debe coincidir con `placed_quantity`.
- No se incluyen tareas incompletas.
- No se incluye reserva como colocación.
- No se publica si la integridad del putaway falla.
