# 11 — Estrategia y Protocolo de Rollback

## Rollback de Revisión en Cloud Run (Inmediato)
Si una nueva revisión falla en los smoke tests post-despliegue o muestra un incremento en errores 5xx:
```bash
# Redirigir el 100% del tráfico a la revisión previa estable (ejemplo revision-00028)
gcloud run services update-traffic autenticacion-continua-api \
  --to-revisions=autenticacion-continua-api-00028-9nd=100 \
  --region=southamerica-west1
```

## Rollback de Base de Datos y Migraciones
* **Estrategia Expand-and-Contract:** El código de la versión anterior debe poder seguir funcionando sin fallar si el esquema ya fue expandido.
* **Downgrade Seguro:** Si la migración es estrictamente reversible, ejecutar `alembic downgrade -1` mediante el job de migración.
* **Restauración de Respaldo:** Si la migración realizó cambios destructivos irrecuperables, restaurar el snapshot de base de datos creado antes del despliegue.
