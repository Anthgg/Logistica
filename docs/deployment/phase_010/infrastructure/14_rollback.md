# 14 — Runbook de Rollback de Infraestructura

## Diagrama de Rollback (Mermaid)

```mermaid
graph TD
    A[Detección de Anomalía Post-Despliegue] --> B{¿Fallo de Código o Infra?}
    B -->|Código / Revisión| C[gcloud run services update-traffic -> Revertir a Revisión Anterior]
    B -->|Esquema de DB| D{¿Migración Reversible?}
    D -->|Sí| E[Cloud Run Job: alembic downgrade -1]
    D -->|No| F[Restaurar Snapshot Pre-Despliegue de PostgreSQL]
```

## Comandos Operativos
```bash
# Inmediata reversión de tráfico al 100% hacia la revisión anterior en producción
gcloud run services update-traffic autenticacion-continua-api \
  --to-revisions=autenticacion-continua-api-00028-9nd=100 \
  --region=southamerica-west1
```
