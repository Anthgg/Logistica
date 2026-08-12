# 20 — `InventoryMovementValidationService`

Valida:

- Organización, branch, almacén, source.
- Idempotencia.
- Adapter autorizado.
- Producto, unidad, conversión, cantidad.
- Posición origen / destino.
- Frontera externa.
- Política de movimiento.
- Step-up cuando corresponde.
- Cross-tenant.

Salida:

- `validation_status`: `VALID`, `VALID_WITH_WARNINGS`, `INVALID`.
- `blocking_errors`, `warnings`.
- `movement_type`, `movement_family`.
- `source_hash`, `payload_hash`.
- `validation_hash` (canonical JSON SHA-256).
- `server_time`.

No se publica con errores bloqueantes.
