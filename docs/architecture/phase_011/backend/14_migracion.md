# 14 — Migración Alembic del Catálogo Documental

## Archivo de Migración
* **Revisión:** `b119420011dc`
* **Revisión Previa (`down_revision`):** `f0424c5e9d46`
* **Tablas Creadas:**
  1. `document_families`
  2. `document_retention_policies`
  3. `document_types`
  4. `document_type_versions`
  5. `document_catalog_versions`

## Comprobación Reversible
Tanto la función `upgrade()` como `downgrade()` han sido diseñadas e inspeccionadas sintácticamente para permitir reversión limpia.
