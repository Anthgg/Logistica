# Estrategia de Respaldo y Restauración de Base de Datos

## 1. Niveles de Recuperación

Para garantizar la continuidad operativa sin ambigüedades, se definen tres niveles de recuperación:

1. **SCHEMA RECOVERY (Recuperación de Esquema DDL):**
   - **Mecanismo:** Árbol canónico de 60 revisiones Alembic en el repositorio.
   - **Capacidad:** Reconstrucción determinística del 100% del DDL (380 tablas, columnas, tipos, constraints e índices) desde cero mediante `alembic upgrade head`.

2. **DATA RECOVERY (Recuperación de Datos Operativos):**
   - **Mecanismo:** Volcado lógico estructurado en JSON (`PYTHON_LOGICAL_TABLE_DUMP_JSON`).
   - **Capacidad:** Restauración de datos tabla por tabla para todos los catálogos base, usuarios, configuraciones y registros transaccionales existentes sin alterar la revisión del esquema.

3. **APPLICATION DATABASE RECOVERY (Recuperación Aplicativa):**
   - **Mecanismo:** Reconstrucción de DDL mediante Alembic + Restauración lógica de datos mediante [`scripts/restore_supabase_backup.py`](../../../scripts/restore_supabase_backup.py).

---

## 2. Respaldo Realizado para el Baseline

- **Timestamp de Respaldo:** `2026-08-16T23:42:36Z`
- **Método de Respaldo:** `PYTHON_LOGICAL_TABLE_DUMP_JSON`
- **Ruta de Archivo:** `backups/supabase/supabase_backup_20260816_234236Z.json` (Excluido de Git vía `.gitignore`)
- **Tamaño:** `2,399,406 bytes (2,343.17 KB)`
- **Checksum SHA256:** `84a36fab7eedb5752096e073f156f9fff31afb04bf4db317cae79a0a6166b0a9`
- **Revisión Respaldada:** `gl440610044rb`
- **Contenido:** 54 tablas con datos respaldadas, totalizando 4,593 registros.

---

## 3. Utilidad Versionada de Restauración Segura

Se ha versionado la herramienta de restauración en [`scripts/restore_supabase_backup.py`](../../../scripts/restore_supabase_backup.py).

### Guardas de Seguridad y Políticas Implementadas:
1. **Requerimiento Explícito de Confirmación:** Requiere el flag obligatorio `--force-restore`.
2. **Protección Contra Host de Producción:** Bloquea por defecto cualquier conexión a hosts remotos (`*.supabase.co`).
3. **Validación de Base de Destino:** Valida que el nombre de la base de datos contenga identificadores seguros (`test`, `restore`, `staging`, `dev`, `local`).
4. **Preservación de Versión Alembic:** Por defecto, la restauración de datos no altera `alembic_version`, manteniendo el esquema en el HEAD canónico de Alembic.
5. **Auditoría Post-Restauración de Claves Foráneas (FK):** Inspecciona exhaustivamente todas las relaciones de claves foráneas entre tablas restauradas para certificar 0 registros huérfanos.
6. **Sincronización de Secuencias:** Ajusta automáticamente las secuencias de PostgreSQL al valor máximo para prevenir colisiones en inserciones posteriores.

### Ejemplo de Ejecución Segura en Entorno de Pruebas:
```bash
python scripts/restore_supabase_backup.py \
    --backup-file backups/supabase/supabase_backup_20260816_234236Z.json \
    --target-db-url postgresql+psycopg://continuous_auth_user:pass@127.0.0.1:5432/continuous_auth_restore_test \
    --force-restore
```

---

## 4. Prueba Demostrada en Base Desechable (`continuous_auth_restore_test`)

La herramienta fue validada ejecutando la restauración completa sobre una base de datos de pruebas limpia construida en el HEAD `gj450510045vr`:

- **Base de Datos de Prueba:** `continuous_auth_restore_test`
- **Tablas Restauradas:** 53 tablas de datos
- **Registros Restaurados:** 4,592 registros
  - `users`: 93
  - `logistics_permissions`: 509
  - `logistics_role_permissions`: 1390
  - `audit_logs`: 361
- **Revisión Alembic Post-Restore:** `gj450510045vr` (HEAD preservado intacto)
- **Violaciones de Claves Foráneas (FK):** `0`
- **Errores:** `0`
- **Afectación a Producción:** `NO` (Producción no fue tocada durante la prueba de restauración)
