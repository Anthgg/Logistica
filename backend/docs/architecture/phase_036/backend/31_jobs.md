# Jobs

Runner: `python -m app.modules.logistics.inbound.arrival_notices.infrastructure.jobs.run_phase036_jobs all`.

Jobs disponibles: expirar holds; recordatorios 24h/2h; marcar ventanas transcurridas; detectar CIT pendiente; licencia próxima/vencida; verificación vehicular vencida; citas afectadas por blackout; reintentar y publicar outbox; limpiar sesiones externas cuando exista portal; reconciliar allocations; y generar paquetes.

Cada job es reentrante, opera por lotes, usa locks y persiste el resultado. La lógica crítica no depende de timers en memoria del proceso web.

