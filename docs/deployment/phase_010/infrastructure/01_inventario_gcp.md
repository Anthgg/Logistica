# 01 — Inventario de Recursos GCP

## Inventario de Infraestructura

| Componente GCP | Recurso Actual / Propuesto | Región | Estado |
| :--- | :--- | :--- | :--- |
| **Proyecto GCP** | `gen-lang-client-0356667380` | Global | `CONFIGURADO` |
| **Cloud Run API (Prod)** | `autenticacion-continua-api` | `southamerica-west1` | `IMPLEMENTADO` |
| **Cloud Run API (Staging)** | `proyecto-t1-api-staging` | `southamerica-west1` | `CONFIGURADO` |
| **Cloud Run Web (Prod)** | `proyecto-t1-web-production` | `southamerica-west1` | `CONFIGURADO` |
| **Cloud Run Web (Staging)** | `proyecto-t1-web-staging` | `southamerica-west1` | `CONFIGURADO` |
| **Artifact Registry** | `proyecto-t1-images` | `southamerica-west1` | `CONFIGURADO` |
| **Secret Manager** | `DATABASE_URL`, `SECRET_KEY` | Global | `CONFIGURADO` |
| **Base de Datos** | Supabase / Cloud SQL PostgreSQL | `southamerica-west1` | `IMPLEMENTADO` |
| **Cloud Storage** | `proyecto-t1-documents-staging/production` | `southamerica-west1` | `CONFIGURADO` |
| **Service Accounts** | `t1-api-staging-sa`, `t1-api-production-sa` | IAM Global | `CONFIGURADO` |
