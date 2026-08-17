# Comparación Exhaustiva de Esquemas · Modelos, Clean DB, Dev DB y Supabase

## 1. Métricas Comparativas Globales Post-Reconciliación

| Conjunto | Nombre del Conjunto | Total Tablas Base | Revisión Alembic | Paridad vs Clean DB |
| :--- | :--- | :---: | :---: | :---: |
| **Set A** | `SQLALCHEMY_MODEL_TABLES` (Registradas en `Base.metadata`) | 335 | N/A | Ver Sección 4 (Model-Only Drift) |
| **Set B** | `ALEMBIC_CLEAN_DATABASE_TABLES` (PostgreSQL Clean Test DB) | 380 | `gj450510045vr` | Referencia Canónica |
| **Set C** | `SUPABASE_APPLICATION_TABLES` (PostgreSQL 17.6 Remoto) | 380 | `gj450510045vr` | **100% Exact Parity (`[]` Diff)** |
| **Set D** | `LOCAL_DEV_APPLICATION_TABLES` (Docker Local Dev DB) | 390 | `gj450510045vr` | Contiene 10 tablas experimentales |

---

## 2. Reconciliación DDL Completada (Revisión `gj450510045vr`)

La discrepancia previa de 10 tablas entre Supabase (370) y la base limpia (380) fue resuelta determinísticamente mediante la migración idempotente de reconciliación `gj450510045vr_reconcile_phase_028_vehicle_verifications.py`.

### Tablas Reconciliadas e Incorporadas en Supabase:
1. `vehicle_verification_sources`
2. `vehicle_verification_provider_configurations`
3. `vehicle_verifications`
4. `vehicle_verification_results`
5. `vehicle_verification_field_provenance`
6. `vehicle_verification_evidence`
7. `assisted_vehicle_verifications`
8. `vehicle_verification_conflicts`
9. `vehicle_verification_requirements`
10. `vehicle_verification_review_tasks`

### Diffs de Conjuntos Resultantes:
- **`ALEMBIC_CLEAN_MINUS_SUPABASE`:** `[]` (0 tablas faltantes en Supabase)
- **`SUPABASE_MINUS_ALEMBIC_CLEAN`:** `[]` (0 tablas extra en Supabase)

---

## 3. Comparación de Columnas y Tipos de Datos (380 Tablas Comunes)

Se ejecutó una verificación exhaustiva columna por columna entre Supabase PostgreSQL 17.6 y la base limpia de Alembic:

- **Tablas Comunes Comparadas:** 380 tablas (100% del catálogo)
- **Atributos Analizados:** Nombre de columna, tipo de dato (`data_type`), nulabilidad (`is_nullable`), valores por defecto (`column_default`), claves primarias y foráneas.
- **Discrepancias Detectadas:** `0` (Paridad perfecta del 100% en todas las columnas de las 380 tablas).

---

## 4. Clasificación de Model-Only Drift (335 Tablas en `Base.metadata`)

El catálogo de modelos ORM SQLAlchemy en `Base.metadata` registra 335 tablas. Existen 10 tablas definidas en el código de modelos (`app/modules/logistics/procurement/evaluations/infrastructure/persistence/models.py`) que no están gestionadas en el árbol canónico de migraciones Alembic:

1. `evaluation_conflict_of_interest_declarations`
2. `evaluation_exchange_rate_snapshots`
3. `evaluation_export_jobs`
4. `evaluation_rubric_levels`
5. `evaluation_rubrics`
6. `evaluation_score_overrides`
7. `quotation_line_evaluations`
8. `supplier_quality_snapshots`
9. `supplier_risk_snapshots`
10. `technical_compliance_assessments`

### Diagnóstico Formal:
- **Clasificación:** `MODEL_ONLY_DRIFT` (Módulo experimental de evaluaciones de compras no incorporado a producción).
- **Alembic Managed:** `NO`
- **Production Required:** `NO`
- **Owner Phase:** Fase Futura de Evaluaciones de Compras.
- **Principio Rector:** **Alembic es la única fuente de verdad (`Single Source of Truth`) para la base de datos de producción**. Los modelos experimentales sin migración no bloquean el baseline de producción y serán formalizados en su fase respectiva.
