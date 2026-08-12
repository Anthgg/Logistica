# 10 — Pipelines CI/CD y Autenticación Workload Identity

## Workflows Integrados

1. **`ci.yml` (Integración Continua):**
   * Linter Ruff, Pytest, comprobación MyPy, OpenAPI generation, Docker build test.
2. **`staging-deploy.yml` (Entrega a Staging):**
   * Publicación de imagen inmutable a Artifact Registry (`api:sha-abc123`).
   * Ejecución de Job de Migración.
   * Actualización del servicio `proyecto-t1-api-staging`.
3. **`production-deploy.yml` (Entrega a Producción):**
   * Requiere aprobación explícita en entorno GitHub `production`.
   * Ejecución de respaldo previo y Job de Migración Out-of-band.
   * Despliegue de la nueva revisión en `autenticacion-continua-api`.
