# 38 — Auditoría

Eventos emitidos a `LogisticsAuditEvent`:

- `logistics.inventory_ledger.posting_requested`
- `logistics.inventory_ledger.source_validated`
- `logistics.inventory_ledger.movement_posted`
- `logistics.inventory_ledger.duplicate_source_detected`
- `logistics.inventory_ledger.posting_failed`
- `logistics.inventory_ledger.compensation_requested`
- `logistics.inventory_ledger.compensation_approved`
- `logistics.inventory_ledger.compensation_rejected`
- `logistics.inventory_ledger.compensation_executed`
- `logistics.inventory_ledger.integrity_verification_started`
- `logistics.inventory_ledger.integrity_valid`
- `logistics.inventory_ledger.integrity_failed`
- `logistics.inventory_ledger.checkpoint_created`
- `logistics.inventory_ledger.reconciliation_started`
- `logistics.inventory_ledger.reconciliation_completed`
- `logistics.inventory_ledger.export_requested`
- `logistics.inventory_ledger.export_downloaded`

Cada evento registra:

- `actor_user_id`, `effective_actor_user_id`
- `service_actor_id`
- `session_id`
- `organization_id`, `branch_id`, `warehouse_id`
- `movement_id`, `movement_code`, `ledger_sequence`
- `source_event_id`, `source_document_id`
- `original_movement_id`, `compensation_movement_id`
- `previous_status`, `new_status`
- `result`, `reason`, `correlation_id`

No se registran cookies, tokens, prueba de step-up, archivos, datos
biométricos, payload completo ni series completas.
