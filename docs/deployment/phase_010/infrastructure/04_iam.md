# 04 — Gestión IAM y Mínimo Privilegio

## Cuentas de Servicio y Roles Asignados

```mermaid
graph TD
    subgraph ServiceAccounts ["Cuentas de Servicio Dedicadas"]
        SA_RUN[t1-api-production-sa]
        SA_MIG[t1-migration-production-sa]
        SA_CI[t1-ci-cd-sa]
    end

    subgraph Roles ["Roles de Mínimo Privilegio"]
        R_SEC[roles/secretmanager.secretAccessor]
        R_LOG[roles/logging.logWriter]
        R_STORAGE[roles/storage.objectUser]
        R_RUN_ADMIN[roles/run.developer]
        R_AR_WRITER[roles/artifactregistry.writer]
    end

    SA_RUN --> R_SEC
    SA_RUN --> R_LOG
    SA_RUN --> R_STORAGE

    SA_MIG --> R_SEC
    SA_MIG --> R_LOG

    SA_CI --> R_RUN_ADMIN
    SA_CI --> R_AR_WRITER
```

## Políticas de Mínimo Privilegio
* Ninguna cuenta de servicio de ejecución runtime posee permisos `roles/owner` o `roles/editor`.
* El acceso a Secret Manager está restringido únicamente a las versiones de secretos consumidas por la aplicación.
