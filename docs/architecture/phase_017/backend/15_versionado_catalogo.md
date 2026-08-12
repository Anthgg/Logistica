# Versionado y Catálogo Documental (Phase 017)

## Estructura de Catálogo
Las plantillas se registran en las tablas del sistema:
- `DocumentTemplateModel`: Define la clave (ej. `inventory.movement`) y la familia (`INVENTORY`).
- `DocumentTemplateVersionModel`: Almacena la versión activa (`1.0.0`), el engine (`Jinja2+WeasyPrint/Fallback`), los paths de templates HTML/CSS y el hash de contenido.

## Seed Idempotente
- El método `seed_inventory_templates()` se ejecuta automáticamente al generar cualquier preview.
- Inserta los registros faltantes con estado `ACTIVE` (para PUT, MOV, AJI, CNT, TRA) o `ACTIVE_FOR_PREVIEW` (para EUB, ADI, CRT).
