# Alembic Baseline · Árbol de Revisiones y Estado

## 1. Topología del Árbol de Revisiones

- **Total de Archivos de Migración en Repositorio:** 59 revisiones
- **Heads en Repositorio:** Único HEAD canónico -> `gi450410045dk`
- **Revisión Inicial Base:** `20260723_0001` (Core Authentication)
- **Revisión Supabase Inicial (Pre-baseline):** `gl440610044rb` (Phase 044 RBAC sync)
- **Revisión Supabase Final (Post-baseline):** `gi450410045dk` (Phase 045 Dimension key expand)

---

## 2. Linaje de las Migraciones Aplicadas en Baseline

Supabase se encontraba exactamente en `gl440610044rb`. Se ejecutaron secuencialmente las 4 migraciones de la Fase 045:

```
gl440610044rb (Phase 044 RBAC Catalog Sync)
      │
      ▼
hh450110045dc (Phase 045: Inventory balances materialized projection tables)
      │
      ▼
gg450210045sw (Phase 045: Add rebuild staging support to inventory_position_balances)
      │
      ▼
gh450310045pu (Phase 045: Add partial unique active index to inventory_position_balances)
      │
      ▼
gi450410045dk (Phase 045: Expand dimension_key column to VARCHAR(255)) [HEAD]
```

---

## 3. Verificación de Integridad

- **Comando Ejecutado:** `python -m alembic upgrade head`
- **Código de Salida:** `0`
- **Consulta Post-Migración en Supabase:**
  ```sql
  SELECT version_num FROM alembic_version;
  -- Resultado: ['gi450410045dk']
  ```
- **Conclusión:** El esquema de Supabase está perfectamente sincronizado con el HEAD de Alembic.
