# 44 — Runbook: evento duplicado

## Síntoma

- `InventoryMovementPostingRequest` queda en estado `DUPLICATE` o `FAILED`
  con `failure_code = INVENTORY_MOVEMENT_SOURCE_CONFLICT`.

## Causa

- Mismo `(organization_id, source_system, source_event_type,
  source_event_id, source_event_version)` con payload hash distinto.

## Acción

1. Verificar el hash del payload fuente.
2. Confirmar que el evento no fue alterado.
3. Si la fuente está comprometida, abrir incidente de seguridad.
4. Si es un reintento con datos actualizados, regenerar el
   `source_event_version` en el publicador.
5. No borrar el posting request original.
