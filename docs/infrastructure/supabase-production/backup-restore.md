# Estrategia de Respaldo y Restauración de Base de Datos

## 1. Respaldo Realizado para el Baseline

- **Timestamp de Respaldo:** `2026-08-16T23:42:36Z`
- **Método de Respaldo:** `PYTHON_LOGICAL_TABLE_DUMP_JSON`
- **Alcance:** Todas las 359 tablas del esquema `public` en Supabase con sus 4,593 registros existentes.
- **Ruta de Archivo:** `backups/supabase/supabase_backup_20260816_234236Z.json`
- **Tamaño:** `2,399,406 bytes (2,343.17 KB)`
- **Checksum SHA256:** `84a36fab7eedb5752096e073f156f9fff31afb04bf4db317cae79a0a6166b0a9`
- **Revisión Respaldada:** `gl440610044rb`
- **Verificación:** `PASS` (Total tablas con datos: 54; Total registros validados: 4,593).

---

## 2. Procedimiento de Restauración

En caso de fallo crítico en una migración futura, se debe ejecutar el siguiente procedimiento:

1. **Detener Tráfico a Cloud Run:**
   - Redirigir el tráfico a la revisión anterior o colocar el servicio en modo mantenimiento.

2. **Reversión de Esquema:**
   - Si la migración es segura para downgrade:
     ```bash
     python -m alembic downgrade <target_revision>
     ```
   - Si la migración modificó datos de forma destructiva o no es reversible mediante downgrade:
     - Restaurar las tablas afectadas desde el archivo de backup JSON verificado utilizando el script de restauración idempotente.

3. **Verificación Post-Restauración:**
   - Consultar `alembic_version` y los conteos de registros para confirmar la integridad del estado restaurado.
   - Ejecutar `GET /api/health` en Cloud Run para validar conectividad.
