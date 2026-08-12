# 27 — `InventoryMovementSnapshotProvider`

El snapshot incluye:

- Movimiento (header).
- Líneas.
- Fuentes.
- Posiciones (snapshot, no estado actual).
- Compensación (si aplica).
- `captured_at`.
- `content_hash` sobre el snapshot canónico.

No consulta maestros actuales al reimprimir: usa snapshots embebidos.
