# 24 — Compensaciones

`InventoryMovementCompensationService`:

- `request_compensation`
- `submit_for_review`
- `approve`
- `reject`
- `cancel`
- `execute`

Reglas:

- El original no se edita.
- La compensación es un MOV nuevo con `movement_type =
  TECHNICAL_COMPENSATION`.
- Invierte origen ↔ destino.
- Misma `base_quantity`.
- Marca `compensation_for_movement_id` y `compensated_by_movement_id`.
- Aprobación separada del solicitante (separación de funciones).
- Step-up CRITICAL para `approve` y `execute`.
