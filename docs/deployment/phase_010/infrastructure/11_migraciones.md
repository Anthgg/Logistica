# 11 — Flujo Operativo de Migraciones (Cloud Run Jobs)

## Arquitectura de Ejecución de Migraciones

```mermaid
sequenceDiagram
    autonumber
    participant CD as GitHub Actions CD
    participant Job as Cloud Run Migration Job (t1-migration-job)
    participant DB as Managed PostgreSQL DB
    participant API as Cloud Run API Service

    CD->>Job: Execute gcloud run jobs execute t1-migration-job --wait
    Job->>DB: Execute alembic upgrade head
    DB-->>Job: Migration Applied Successfully
    Job-->>CD: Exit Code 0 (Success)
    CD->>API: Deploy New Container Revision
```

## Garantías del Proceso
* Evita ejecuciones concurrentes de `alembic` en instancias web escaladas.
* Permite rollback de código sin corrupción de esquema mediante la estrategia *Expand-and-Contract*.
