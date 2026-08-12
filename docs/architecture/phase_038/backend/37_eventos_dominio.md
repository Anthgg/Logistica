# 37. Eventos de dominio

Eventos principales: queued, planned, assigned, movement started, arrived, readiness completed, responsible assigned, seal opened, unloading started/paused/resumed/aborted/completed, reassigned, released y correcciones.

El outbox reutiliza la infraestructura transaccional de avisos de llegada con `aggregate_type` específico y clave de deduplicación.

