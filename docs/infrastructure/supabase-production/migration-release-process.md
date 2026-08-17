# Proceso de Despliegue y Migración de Base de Datos

## 1. Pipeline de Migraciones en Nuevas Fases

Para cada nueva fase funcional (a partir de la Fase 004) que introduzca cambios DDL en Alembic, se debe seguir estrictamente este pipeline de 8 pasos:

```
[ 1. CI Automatizado ]
      │  • Validar ruff, mypy, pytest en GitHub Actions.
      ▼
[ 2. Dry-Run en PostgreSQL Test Limpio ]
      │  • Ejecutar alembic upgrade head sobre base local limpia desde cero.
      ▼
[ 3. Backup Lógico de Supabase ]
      │  • Generar snapshot/dump previo con timestamp y checksum SHA256.
      ▼
[ 4. Ejecución Out-of-Band de Alembic ]
      │  • Ejecutar migración controlada (Cloud Run Job o Alembic CLI Release).
      │  • NUNCA ejecutar migraciones en el startup concurrente de la app.
      ▼
[ 5. Verificación de Revisión en Supabase ]
      │  • Comprobar que SELECT version_num FROM alembic_version == target_revision.
      ▼
[ 6. Despliegue / Rollout de Cloud Run ]
      │  • Desplegar nueva revisión del contenedor apuntando al esquema actualizado.
      ▼
[ 7. Pruebas de Humo en Vivo ]
      │  • Comprobar GET /api/health (200 OK, database connected).
      │  • Ejecutar lectura autenticada y verificación de endpoints críticos.
      ▼
[ 8. Promoción de Tráfico / Cierre de Fase ]
      • Enrutar 100% del tráfico a la nueva revisión.
```

---

## 2. Política de Concurrencia de Contenedores (`RUN_MIGRATIONS=false`)

Cloud Run puede escalar horizontalmente creando múltiples instancias concurrentes. Si cada instancia intentara ejecutar `alembic upgrade` al arrancar, se producirían condiciones de carrera y bloqueos en tablas (`deadlocks` en DDL).

Por esta razón:
- **`RUN_MIGRATIONS` está establecido en `false`** en el servicio web de Cloud Run.
- Las migraciones se ejecutan exclusivamente como un paso de release independiente (Out-of-Band Job) antes de activar el tráfico.
