# 26 — Control de Concurrencia, Bloqueos e Idempotencia

## 1. PostgreSQL Advisory Locks en Jobs

Para evitar que múltiples instancias del servidor ejecutador (ej. dos réplicas de Cloud Run Jobs) procesen la ingesta del mismo padrón en paralelo, el script solicita un bloqueo de sesión de PostgreSQL:

```python
async def acquire_job_advisory_lock(db_session, lock_id: int = 882601) -> bool:
    result = await db_session.execute(text(f"SELECT pg_try_advisory_lock({lock_id})"))
    return result.scalar()
```

---

## 2. Idempotencia basada en Hashing SHA-256 de Archivos

Antes de iniciar la descompresión e ingesta de un archivo ZIP descargado, el servicio calcula su hash SHA-256 (`archive_hash`). Si ya existe un dataset en estado `ACTIVE` o `SUPERSEDED` con el mismo hash exacto, la ingesta finaliza inmediatamente indicando idempotencia exitosa sin duplicar trabajo.
