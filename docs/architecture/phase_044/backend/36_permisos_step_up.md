# 36 — Permisos y step-up

## Capacidades

- `logistics.inventory_ledger.read`
- `logistics.inventory_ledger.read_sources`
- `logistics.inventory_ledger.read_snapshots`
- `logistics.inventory_ledger.read_history`
- `logistics.inventory_ledger.read_integrity`
- `logistics.inventory_ledger.validate_prepared_event`
- `logistics.inventory_ledger.post_prepared_event`
- `logistics.inventory_ledger.post_quality_events`
- `logistics.inventory_ledger.post_putaway_events`
- `logistics.inventory_ledger.retry_failed_posting`
- `logistics.inventory_ledger.request_compensation`
- `logistics.inventory_ledger.review_compensation`
- `logistics.inventory_ledger.approve_compensation`
- `logistics.inventory_ledger.execute_compensation`
- `logistics.inventory_kardex.read`
- `logistics.inventory_kardex.read_running_quantity`
- `logistics.inventory_kardex.export`
- `logistics.inventory_ledger.verify`
- `logistics.inventory_ledger.create_checkpoint`
- `logistics.inventory_ledger.reconcile`
- `logistics.inventory_ledger.read_balance_preparation`
- `logistics.inventory_ledger.read_traceability_preparation`

## Step-up

- Kardex: LOW.
- Snapshot sensible: MEDIUM.
- Publicar evento: MEDIUM.
- Batch publicación: HIGH.
- Reintento: HIGH.
- Solicitar compensación: HIGH.
- Aprobar / ejecutar: CRITICAL.
- Crear checkpoint: MEDIUM.
- Reconciliación: HIGH.
- Exportación masiva: HIGH.

Los 22 permisos declarados por el router existen en el catálogo RBAC 1.2.0.
Los roles específicos son `INVENTORY_OPERATOR`, `INVENTORY_AUDITOR`,
`SYSTEM_INTEGRATION_SERVICE` y `LEDGER_ADMIN`, además de los roles logísticos
existentes.

El backend toma permiso, nivel de step-up y requisito CSRF de metadatos del
endpoint. Una dependencia común los hace efectivos: valida permiso y alcance de
organización, resuelve/consume `X-Step-Up-Proof-ID` con el servicio existente y
compara cookie/header CSRF. No confía en `X-Risk-Level`, `step_up_passed` ni
`biometric_score` enviados por el cliente.
