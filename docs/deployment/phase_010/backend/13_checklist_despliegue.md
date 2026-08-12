# 13 — Lista de Verificación de Despliegue (Checklist Operativo)

## Pre-Despliegue (ANTES)
- [x] Código fuente analizado mediante Ruff linter y MyPy.
- [x] Pruebas automatizadas aprobadas (100% de tasa de éxito en Pytest).
- [x] Construcción de imagen Docker validada sin errores.
- [x] Variables de entorno documentadas y sincronizadas en Google Secret Manager.
- [x] Respaldo de base de datos verificado antes de aplicar cambios de esquema.
- [x] Plan y revisión de rollback identificada.

## Durante el Despliegue (DURANTE)
- [ ] Ejecutar job de migración Alembic Out-of-band.
- [ ] Desplegar la nueva revisión de contenedor a Cloud Run.
- [ ] Verificar asignación progresiva de tráfico.
- [ ] Comprobar probes `/health`, `/ready` y `/live`.
- [ ] Ejecutar suite de smoke tests post-despliegue.

## Post-Despliegue (DESPUÉS)
- [ ] Inspeccionar registros en Google Cloud Logging buscando anomalías o errores 5xx.
- [ ] Probar flujo de autenticación, `/auth/me`, cookies HTTP-only y protección CSRF.
- [ ] Probar operaciones logísticas protegidas y desafíos Step-Up de la Fase 009.
- [ ] Registrar la revisión activa desplegada en el registro de liberaciones.
