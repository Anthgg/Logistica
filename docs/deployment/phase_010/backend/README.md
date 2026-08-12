# Fase 010 — Preparar Ambientes y Despliegue del Backend

## Objetivo
Establecer la arquitectura y estrategia operativa de infraestructura, contenedorización, pipelines CI/CD y despliegue seguro para el backend FastAPI en los ambientes de `local`, `test`, `staging` y `production`.

## Alcance
* **Estrategia Multi-Ambiente:** Configuración por Pydantic Settings (`APP_ENV`).
* **Seguridad de Secretos:** Integración con Google Secret Manager y Cloud Run Secrets.
* **Contenedorización Reutilizable:** `Dockerfile` multi-etapa ejecutado como usuario no-root (`appuser`, UID 10001) y `.dockerignore` estricto.
* **Estrategia de Migraciones Out-of-Band:** Ejecución de Alembic mediante Cloud Run Jobs independientes sin bloquear el arranque del servicio HTTP.
* **Observabilidad & Health Probes:** Logs JSON estructurados con `request_id` / `correlation_id` y probes `/health`, `/ready`, `/live`.
* **Pipelines CI/CD:** GitHub Actions `.github/workflows/ci.yml` y `.github/workflows/cd.yml`.
* **Estrategia de Rollback & Checklist Operativo:** Protocolo de reversión de versiones y lista de verificación pre y post despliegue.

## Estado
* **Estado General:** `IMPLEMENTADO` / `COMPROBADO`
* **Pruebas de Configuración & Health:** Pasadas en la suite de Pytest.
* **Despliegue a Producción:** `NO EJECUTADO` (requiere aprobación explícita).
