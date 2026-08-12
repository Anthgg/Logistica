# 10 — `InventoryStateTransitionPolicy`

La política `LEGAL_STATE_TRANSITIONS` define las transiciones legales
entre estados de cantidad preservada. Cada transición declara:

- availability_state (from → to)
- quality_state (from → to)
- transit_state (from → to)
- damage_state (from → to)
- expiration_state (from → to)
- reason_code

Una transición de estado **no** modifica la cantidad física total: misma
`base_quantity` para source y destination. La causa queda registrada en
`reason_code`.

Ejemplos soportados:

- `QUARANTINE_RELEASE_TO_STAGING`
- `PUTAWAY_COMPLETED`
- `RESERVATION_CREATED/RELEASED/CONSUMED`
- `QUALITY_REJECTED`
- `DAMAGED_APPLIED`
- `EXPIRED_APPLIED`
- `TRANSIT_APPLIED/RELEASED`
