# 12 — Secuencias y códigos MOV

## Particiones

`InventoryLedgerPartition` con:

- `partition_key` = `organization_id:warehouse_id|GLOBAL:fiscal_year|OPEN`
- `current_sequence` monotónico, asignado en transacción
- `last_movement_id`, `last_movement_hash`

`SELECT FOR UPDATE` sobre la fila de la partición, luego `current_sequence + 1`.

## Códigos MOV

Si el `DocumentTypeModel` con `code = 'MOV'` está configurado (Fase 013),
se usa el formato `MOV-SITE-YEAR-CORRELATIVE` (e.g. `MOV-LIM-2026-000001`).

Si no existe, se registra **PENDIENTE_CATÁLOGO_DOCUMENTAL** y se usa un código
técnico UUID. En desarrollo se acepta un fallback; en producción el
`InventoryMovementCodeService` levanta un error claro.

## Decisión PENDIENTE

La Fase 099 debería sembrar el `DocumentType` con code `MOV` para eliminar
el fallback técnico.
