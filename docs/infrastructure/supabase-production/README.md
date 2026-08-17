# Supabase + Google Cloud Run · Production Database Baseline

Este directorio documenta la arquitectura, estrategia de migración, conexiones, gestión de secretos, procedimientos de respaldo y ciclo de vida de la base de datos de producción basada en **Supabase PostgreSQL** y servida por **Google Cloud Run**.

---

## 1. Resumen Ejecutivo

- **Base de Datos de Producción:** Supabase PostgreSQL 17.6 administrado (Host: `db.nrrgwibyiekacisdtgiq.supabase.co`, Región: AWS sa-east-1 / São Paulo).
- **Entorno de Cómputo Backend:** Google Cloud Run (`autenticacion-continua-api`, Región: `southamerica-west1`).
- **Motor de Migraciones:** Alembic (Single Source of Truth) con 60 revisiones versionadas.
- **Revisión Remota Actual en Supabase:** `gj450510045vr` (Alembic HEAD Reconciliado).
- **Paridad de Esquema:** Paridad exacta del 100% (380 tablas base en Clean DB == 380 tablas base en Supabase).
- **Modo de Conexión Aplicativa:** Conexión directa / Session Pooling vía SQLAlchemy 2.0 (`postgresql+psycopg://`).
- **Aislamiento de Entornos:** PostgreSQL 16 Docker local para desarrollo/CI; Supabase PostgreSQL 17 para producción.

---

## 2. Mapa Documental

| Documento | Descripción |
| :--- | :--- |
| [`architecture.md`](./architecture.md) | Arquitectura integral de ambientes (Desarrollo, CI, Staging y Producción). |
| [`database-connections.md`](./database-connections.md) | Estrategia de conectividad, pooling de conexiones, SSL y separación de roles. |
| [`alembic-baseline.md`](./alembic-baseline.md) | Historial de revisiones Alembic, validación de un solo HEAD y linaje de migraciones. |
| [`schema-comparison.md`](./schema-comparison.md) | Matriz comparativa entre modelos SQLAlchemy, PostgreSQL Local y Supabase Remoto. |
| [`cloud-run-database.md`](./cloud-run-database.md) | Configuración del servicio Cloud Run, variables de entorno y escalado. |
| [`migration-release-process.md`](./migration-release-process.md) | Flujo y pipeline para ejecución de migraciones en despliegues futuros. |
| [`backup-restore.md`](./backup-restore.md) | Estrategia de respaldos lógicos, comprobación de FKs y procedimiento de recuperación aplicativa. |
| [`security.md`](./security.md) | Políticas de seguridad, RBAC vs RLS, cifrado en tránsito/reposo y auditoría de Data API. |

---

## 3. Estado de Aceptación

```
ESTADO OFICIAL:
SUPABASE_PRODUCTION_BASELINE_READY_FOR_ACCEPTANCE
```
