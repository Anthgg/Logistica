# Fase 010 — Arquitectura de Infraestructura GCP y Despliegue Repetible

## Objetivo
Diseñar e implementar una arquitectura de infraestructura en Google Cloud Platform (GCP) separada, reproducible, segura y con control de costes para los ambientes de `staging` y `production` de **Proyecto T1**.

## Alcance Infraestructura
* **Separación de Ambientes:** Isolación de recursos, permisos, secretos y bases de datos para `staging` y `production`.
* **Región Estratégica:** `southamerica-west1` (Santiago, Chile) para optimización de latencia (< 40 ms a Perú) y costes.
* **Artifact Registry:** Repositorio privado inmutable (`proyecto-t1-images`) con análisis de vulnerabilidades.
* **IAM con Mínimo Privilegio:** Cuentas de servicio dedicadas (`t1-api-staging-sa`, `t1-api-production-sa`, `t1-migration-sa`) sin permisos de Owner/Editor en runtime.
* **Secret Manager:** Gestión aislada de secretos (`DATABASE_URL`, `SECRET_KEY`, `CSRF_SECRET`).
* **Cloud Run Backend & Frontend:** Servicios escalados horizontalmente con probes de salud `/health`, `/ready` y `/live`.
* **Migraciones Out-of-Band:** Alembic ejecutado como Cloud Run Job antes del despliegue HTTP.
* **Monitoreo & Presupuesto:** Alertas de presupuesto, cuotas máximas de instancias y dashboards de latencia/errores.
* **Runbook de Rollback:** Protocolo de reversión de tráfico y restauración de esquemas.

## Estado
* **Estado General:** `CONFIGURADO` / `DOCUMENTADO`
* **Despliegue a Producción:** `NO EJECUTADO` (requiere aprobación explícita).
