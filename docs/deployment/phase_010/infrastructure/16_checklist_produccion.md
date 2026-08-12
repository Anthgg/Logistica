# 16 — Lista de Verificación de Producción (Checklist Infraestructura)

## Pre-Despliegue (ANTES)
- [x] Región GCP verificada (`southamerica-west1`).
- [x] IAM configurado aplicando el principio de mínimo privilegio.
- [x] Secretos inyectados en Secret Manager (`[SECRETO]`).
- [x] Límite de instancias máximas en Cloud Run configurado en 20.
- [x] Snapshot de respaldo de base de datos verificado.

## Durante el Despliegue (DURANTE)
- [ ] Ejecución del job de migración Alembic Out-of-band.
- [ ] Despliegue de la revisión contenedora en Cloud Run.
- [ ] Verificación de asignación de tráfico.
- [ ] Validación de probes `/health`, `/ready` y `/live`.

## Post-Despliegue (DESPUÉS)
- [ ] Verificación de registros estructurados en Google Cloud Logging.
- [ ] Verificación de latencia y ausencia de errores 5xx en Cloud Monitoring.
- [ ] Confirmación de versión activa registrada en la bitácora de liberaciones.
