# Comparación de Esquemas · Modelos, Local DB y Supabase

## 1. Métricas Comparativas Globales

| Origen | Total Tablas Base | Revisión Alembic | Notas |
| :--- | :---: | :---: | :--- |
| **Modelos SQLAlchemy (Base.metadata)** | 380 | N/A | Definición canónica en código |
| **PostgreSQL Test Limpio (Desde cero)** | 380 | `gi450410045dk` | Creado por `alembic upgrade head` puro |
| **Supabase Remoto (Post-Migración)** | 370 | `gi450410045dk` | Coincidencia exacta con modelos aplicables |
| **PostgreSQL Local Docker (Dev DB)** | 390 | `gi450410045dk` | Contiene 10 tablas históricas no gestionadas |

---

## 2. Tablas Incorporadas a Supabase en Fase 045

Durante la migración controlada se crearon las siguientes 11 tablas de saldos y proyecciones de inventario:

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

## 3. Clasificación de Diferencias

- **Tablas Extra en Supabase vs Local:** `0` (Ningún objeto huérfano ni contaminación externa).
- **Tablas Extra en Local Dev DB vs Supabase:** 10 tablas correspondientes a esquemas experimentales/históricos de evaluación (`evaluation_*`, `supplier_*_snapshots`) que no forman parte del árbol oficial de producción.
- **Drift de Esquema:** `0` (Todos los tipos, nullabilities, PKs y FKs coinciden con la especificación de Alembic).
