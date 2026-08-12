# 16 — Reservas (sólo contrato)

Tipos:

- `RESERVATION_CREATED`: AVAILABLE → RESERVED.
- `RESERVATION_RELEASED`: RESERVED → AVAILABLE.
- `RESERVATION_CONSUMED`: RESERVED → PICKED_FUTURE.
- `RESERVATION_EXPIRED`: RESERVED → AVAILABLE.

Reglas:

- No se implementa negocio de reserva.
- No hay cambio de cantidad física.
- Adapter deshabilitado: `RESERVATION_CREATED`, `RESERVATION_RELEASED`.
- La Fase 045 proveerá los saldos para validar.
