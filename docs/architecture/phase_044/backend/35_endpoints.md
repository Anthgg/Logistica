# 35 — Endpoints HTTP

Base: `/api/logistics/inventory`.

Movimientos:

- `GET /movements` — lista con filtros.
- `GET /movements/{movement_id}` — detalle.
- `GET /movements/{movement_id}/lines`
- `GET /movements/{movement_id}/sources`
- `GET /movements/{movement_id}/snapshot`
- `GET /movements/{movement_id}/history`
- `GET /movements/{movement_id}/integrity`
- `GET /movements/{movement_id}/capabilities`
- `GET /movements/{movement_id}/compensations`

Posting:

- `POST /ledger/posting-requests`
- `GET /ledger/posting-requests/{request_id}`
- `POST /ledger/prepared-events/{source_event_id}/validate`
- `POST /ledger/prepared-events/{source_event_id}/post`
- `POST /ledger/materialize/quality-events`
- `POST /ledger/materialize/putaway-events`
- `POST /ledger/retry-failed-posting/{request_id}`

Compensación:

- `POST /movements/{movement_id}/compensation-requests`
- `GET /movement-compensation-requests/{request_id}`
- `POST /movement-compensation-requests/{request_id}/submit`
- `POST /movement-compensation-requests/{request_id}/approve`
- `POST /movement-compensation-requests/{request_id}/reject`
- `POST /movement-compensation-requests/{request_id}/execute`
- `POST /movement-compensation-requests/{request_id}/cancel`

Kardex:

- `GET /kardex`
- `GET /kardex/technical-running-quantity`
- `GET /kardex/movement-types`
- `GET /kardex/source-types`
- `GET /kardex/state-transitions`
- `POST /kardex/exports`
- `GET /kardex/exports/{export_id}`
- `GET /kardex/exports/{export_id}/download`

Integridad:

- `GET /ledger/partitions`
- `GET /ledger/partitions/{partition_id}`
- `GET /ledger/partitions/{partition_id}/integrity`
- `POST /ledger/partitions/{partition_id}/verify`
- `POST /ledger/partitions/{partition_id}/checkpoints`
- `GET /ledger/checkpoints/{checkpoint_id}`
- `POST /ledger/reconciliation-jobs`
- `GET /ledger/reconciliation-jobs/{job_id}`
- `GET /ledger/reconciliation-jobs/{job_id}/results`

Preparación para Fase 045/046:

- `GET /movements/{movement_id}/balance-preparation`
- `GET /movements/{movement_id}/traceability-preparation`
- `GET /ledger/balance-preparation`
- `GET /ledger/traceability-preparation`

Solo lectura. No hay PATCH / DELETE sobre movimientos.
