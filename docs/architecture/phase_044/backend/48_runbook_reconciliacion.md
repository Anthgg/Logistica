# 48 — Runbook: reconciliación

## Procedimiento

1. Lanzar job `run_reconciliation`.
2. Revisar `result_code` por evento.
3. Para `SOURCE_EVENT_MISSING_MOVEMENT`: reintentar publicación.
4. Para `MOVEMENT_WITHOUT_SOURCE`: investigar.
5. Para `HASH_MISMATCH`: ejecutar runbook de hash.
6. Para `QUANTITY_MISMATCH`: comparar payload fuente vs libro.
7. Para `ADAPTER_VERSION_MISMATCH`: actualizar adaptador.
