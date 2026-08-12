# 40 — Jobs persistentes

- `ingest_quality_events` — materializa eventos de Fase 042.
- `ingest_putaway_events` — materializa eventos de Fase 043.
- `process_posting_requests` — procesa pendientes.
- `retry_failed_posting` — reintenta fallos.
- `process_outbox` — marca lotes entregados por el transportador externo; no
  sustituye al transporte.
- `verify_chain` — verifica la cadena.
- `create_checkpoint` — genera checkpoint.
- `run_reconciliation` — ejecuta reconciliación.
- `run_export_job` — materializa exportación.
- `detect_missing_movements`
- `detect_sequence_gaps`
- `detect_duplicate_posting_requests`
- `prepare_balance_and_traceability`

Sin timers en memoria: el runner persistente los invoca.

Los jobs de Fase 042/043 crean posiciones canónicas, publican la solicitud y
sólo cuentan `processed` después de obtener un MOV. Los fallos quedan como
`FAILED`; `detect_missing_movements` devuelve solicitudes sin movimiento, no
eventos que ya tenían referencia.
