# 02 — Arquitectura y Separación de Ambientes

## Diagrama de Separación de Ambientes (Mermaid)

```mermaid
graph LR
    subgraph Staging ["Ambiente Staging (proyecto-t1-staging)"]
        CR_STG[proyecto-t1-api-staging]
        DB_STG[(Cloud SQL / Supabase Staging DB)]
        GCS_STG[proyecto-t1-documents-staging]
        SEC_STG[Secret Manager Staging]
        SA_STG[t1-api-staging-sa]
    end

    subgraph Production ["Ambiente Producción (proyecto-t1-production)"]
        CR_PROD[autenticacion-continua-api]
        DB_PROD[(Cloud SQL / Supabase Production DB)]
        GCS_PROD[proyecto-t1-documents-production]
        SEC_PROD[Secret Manager Production]
        SA_PROD[t1-api-production-sa]
    end

    SA_STG --> SEC_STG
    SA_STG --> DB_STG
    SA_STG --> GCS_STG

    SA_PROD --> SEC_PROD
    SA_PROD --> DB_PROD
    SA_PROD --> GCS_PROD
```

## Reglas de Aislamiento
1. **Bases de Datos:** Staging y Producción NUNCA comparten la misma instancia o esquema de base de datos.
2. **Secretos:** Las claves de encriptación y tokens de Staging son distintos e independientes de Producción.
3. **Storage Buckets:** Buckets aislados con políticas IAM independientes.
