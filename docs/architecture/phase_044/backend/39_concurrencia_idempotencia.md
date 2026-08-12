# 39 — Concurrencia e idempotencia

Garantías:

- Dos publicaciones del mismo source → un solo MOV activo.
- Mismo source con payload distinto → `InventoryMovementSourceDuplicated`.
- Dos movimientos en la misma partición → `SELECT FOR UPDATE` en
  `inventory_ledger_partitions`.
- Dos códigos MOV concurrentes → `SELECT FOR UPDATE` sobre partición.
- Publicación + compensación simultáneas → la compensación espera al
  commit.
- Checkpoint durante publicación → verificación async sin locks.
- Verificación durante publicación → no bloquea.
- row_version antiguo → `IntegrityError` de SQLAlchemy.
- Compensación doble → `InventoryMovementAlreadyCompensated`.

Idempotencia requerida en:

- Posting request
- Validar evento
- Publicar evento
- Reintentar
- Solicitar / aprobar / ejecutar compensación
- Crear checkpoint / verifier / reconciliación
- Exportar
