# 41. Jobs

Jobs persistentes: vencer planes, alertar movimientos estancados, alertar descargas abandonadas, refrescar proyecciones y generar exportaciones operativas. Usan `FOR UPDATE SKIP LOCKED`, batches y outbox deduplicado. No hay timers in-process.

Comando: `python -m app.modules.logistics.inbound.dock_operations.infrastructure.jobs.run_phase038_jobs all`.
