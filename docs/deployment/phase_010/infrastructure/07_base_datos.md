# 07 — Arquitectura y Gestión de Base de Datos

## Conexión y Seguridad PostgreSQL
* **Driver:** `postgresql+psycopg://` (Psycopg 3).
* **Cifrado de Conexión:** SSL/TLS activado de forma obligatoria en producción.
* **Connection Pooling:**
  * `DATABASE_POOL_SIZE`: 10 (Staging) / 15 (Producción).
  * `DATABASE_MAX_OVERFLOW`: 20 (Staging) / 30 (Producción).
  * `DATABASE_POOL_RECYCLE`: 1800 segundos.
* **Separación de Roles:**
  * Usuario de migración: Permisos DDL completos sobre esquemas.
  * Usuario de aplicación: Permisos DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) sobre tablas existentes.
