# 17 — Migración y Seed de Catálogo

## Migración: `g660970016dc_add_inbound_document_templates`

**Revisión:** `g660970016dc`  
**Predecesora:** `f550860015dc` (Phase 015 — Purchasing Templates)

### Upgrade
Inserta 5 tipos documentales en la tabla `document_types`:

```sql
INSERT INTO document_types (id, family_code, code, name, description, is_active, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'INBOUND', 'CIT', 'Cita de Recepción', '...', true, now(), now()),
    (gen_random_uuid(), 'INBOUND', 'CPV', 'Control de Puerta Vehicular', '...', true, now(), now()),
    (gen_random_uuid(), 'INBOUND', 'AREC', 'Acta de Recepción', '...', true, now(), now()),
    (gen_random_uuid(), 'INBOUND', 'DIF', 'Acta de Diferencias', '...', true, now(), now()),
    (gen_random_uuid(), 'QUALITY', 'NC', 'No Conformidad', '...', true, now(), now())
ON CONFLICT (code) DO NOTHING;
```

> `ON CONFLICT DO NOTHING` garantiza **idempotencia** — ejecutar la migración varias veces no duplica filas.

> **Nota:** El tipo `NI` (Nota de Ingreso) no se insertó en esta migración porque ya puede existir en el catálogo como tipo genérico. Verificar en la Fase 017.

### Downgrade
```sql
DELETE FROM document_types WHERE code IN ('CIT', 'CPV', 'AREC', 'DIF', 'NC');
```

## Seed de Plantillas en Memoria
`InboundRenderingService.seed_inbound_templates()` registra adicionalmente las 6 entradas en `document_templates` y `document_template_versions` usando los repositorios ORM. El seed es idempotente: verifica existencia antes de insertar.
