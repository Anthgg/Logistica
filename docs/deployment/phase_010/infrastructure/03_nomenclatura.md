# 03 — Estándar de Nomenclatura de Recursos

## Convención de Nombres GCP

| Recurso | Staging | Producción |
| :--- | :--- | :--- |
| **Cloud Run Backend** | `proyecto-t1-api-staging` | `autenticacion-continua-api` |
| **Cloud Run Frontend** | `proyecto-t1-web-staging` | `proyecto-t1-web-production` |
| **Artifact Registry** | `proyecto-t1-images` | `proyecto-t1-images` |
| **Cloud Storage** | `proyecto-t1-documents-staging` | `proyecto-t1-documents-production` |
| **Service Account API** | `t1-api-staging-sa` | `t1-api-production-sa` |
| **Service Account Migration** | `t1-migration-staging-sa` | `t1-migration-production-sa` |
| **Cloud Run Migration Job** | `t1-migration-job-staging` | `t1-migration-job-production` |
