# Comparación Exhaustiva de Esquemas · Modelos, Clean DB, Dev DB y Supabase

## 1. Métricas Comparativas Globales

| Conjunto | Nombre del Conjunto | Total Tablas Base | Revisión Alembic |
| :--- | :--- | :---: | :---: |
| **Set A** | `SQLALCHEMY_MODEL_TABLES` (Registradas en `Base.metadata`) | 335 | N/A |
| **Set B** | `ALEMBIC_CLEAN_DATABASE_TABLES` (PostgreSQL Clean Test DB) | 380 | `gi450410045dk` |
| **Set C** | `SUPABASE_APPLICATION_TABLES` (PostgreSQL 17.6 Remoto) | 370 | `gi450410045dk` |
| **Set D** | `LOCAL_DEV_APPLICATION_TABLES` (Docker Local Dev DB) | 390 | `gi450410045dk` |

---

## 2. Resolución de la Discrepancia de Conteo (380 vs 370 Tablas)

### Análisis Causa Raíz
La diferencia de exactamente 10 tablas entre `ALEMBIC_CLEAN_DATABASE_TABLES` (380) y `SUPABASE_APPLICATION_TABLES` (370) corresponde al conjunto de verificación vehicular creado en la Fase 028:

- **Revisión Alembic:** `s310110028dc_phase_028_vehicle_verifications.py`
- **Fase de Origen:** Fase 028 (`Phase 028 — Vehicle Verifications 10 tables DDL migration`)

### Las 10 Tablas de Verificación Vehicular:
1. `assisted_vehicle_verifications`
2. `vehicle_verification_conflicts`
3. `vehicle_verification_evidence`
4. `vehicle_verification_field_provenance`
5. `vehicle_verification_provider_configurations`
6. `vehicle_verification_requirements`
7. `vehicle_verification_results`
8. `vehicle_verification_review_tasks`
9. `vehicle_verification_sources`
10. `vehicle_verifications`

**Por qué existen en Clean Test DB:** La base limpia ejecuta la totalidad de las 59 revisiones de Alembic desde `20260723_0001` hasta el HEAD `gi450410045dk`, creando todas las tablas históricas intermedias.  
**Por qué no estaban en Supabase:** Supabase fue inicializado y sellado históricamente en una rama que no ejecutó la revisión DDL de Fase 028, encontrándose en `gl440610044rb` antes del baseline. La migración controlada ejecutó únicamente las 4 revisiones pendientes de Fase 045 (`hh450110045dc` -> `gi450410045dk`).

---

## 3. Comparación de Columnas y Tipos de Datos (370 Tablas Comunes)

Se ejecutó una comparación exhaustiva columna por columna entre Supabase PostgreSQL 17.6 y la base limpia de Alembic:

- **Tablas Comunes Comparadas:** 370 tablas
- **Atributos Analizados:** Nombre de columna, tipo de dato (`data_type`), nulabilidad (`is_nullable`), valores por defecto (`column_default`), claves primarias y foráneas.
- **Discrepancias Detectadas:** `0` (Paridad del 100% en todas las columnas de las 370 tablas compartidas).

---

## 4. Tablas Incorporadas en Fase 045

Durante la migración controlada se crearon las 11 tablas de saldos y proyecciones de inventario:

1. `inventory_position_balances`
2. `inventory_balance_checkpoints`
3. `inventory_balance_deltas`
4. `inventory_balance_export_jobs`
5. `inventory_balance_formula_definitions`
6. `inventory_balance_formula_versions`
7. `inventory_balance_projection_cursors`
8. `inventory_balance_rebuild_differences`
9. `inventory_balance_rebuild_jobs`
10. `inventory_balance_reconciliation_differences`
11. `inventory_balance_reconciliation_jobs`

---

## 5. Diferencias en Local Dev DB (390 Tablas)

La base local de desarrollo (`continuous_authentication`) contiene 10 tablas adicionales no gestionadas en la línea principal correspondientes a esquemas experimentales de evaluación (`evaluation_*`, `supplier_*_snapshots`), las cuales no forman parte del esquema de producción ni de la base limpia.
