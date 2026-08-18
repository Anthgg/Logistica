# Fase 005.3 — Despliegue productivo y rotación de secretos

## El problema

F005.2 dejó la base productiva al día (`jl480110048dk`), pero **la aplicación desplegada
seguía siendo de antes**: la imagen `v0.9.8` del 10 de agosto de 2026, anterior a F004.5
y F005.1. Consecuencia comprobable: `/api/logistics/catalogs/*` devolvía 404 en
producción. No era un problema de base de datos, sino de código sin desplegar.

Además había dos secretos productivos en mal estado, uno de ellos crítico.

## Documentos

| Documento | Contenido |
|---|---|
| [`security-incident.md`](security-incident.md) | Los dos incidentes, qué se rotó y qué quedó pendiente |
| [`deployment-pipeline.md`](deployment-pipeline.md) | Pipeline canónico, decisiones y gates |
| [`runbook.md`](runbook.md) | Desplegar, verificar, revertir y rotar secretos |
| [`infra-state.md`](infra-state.md) | Estado de Cloud Run, registry, identidad y deuda |

## Qué entrega

1. **Despliegue real** desde GitHub Actions: construye, resuelve digest inmutable,
   despliega sin tráfico, verifica y promueve. Con rollback automático.
2. **Autenticación por Workload Identity Federation**: sin claves de service account
   descargadas ni almacenadas en GitHub.
3. **Secretos por referencia a Secret Manager**, fuera de la configuración literal del
   servicio.
4. **`SECRET_KEY` rotada**: la clave HS256 que firma los JWT ya no es el valor de
   ejemplo.
5. **Detector de fugas** (`scripts/scan_for_secrets.py`) con gate en CI, nacido del
   incidente de F005.2.
6. **Un solo pipeline de despliegue**: `cd.yml` eliminado, `staging-deploy.yml`
   desactivado con su motivo escrito.

## Qué NO entrega

- No rota la contraseña de la base: requiere el panel de Supabase.
  `PENDING_SECURE_USER_ACTION`.
- No crea entorno de staging.
- No toca lógica de dominio ni migraciones.
- No crea datos de prueba en producción.
- No reconcilia el RLS heredado ni reescribe la documentación de Phase 010.
