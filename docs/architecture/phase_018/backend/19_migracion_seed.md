# Migración y Semilla Idempotente (Phase 018)

## Detalles de Migración `i880090018dc`
- Inserta el tipo propuesto `CPR` en la tabla `document_types`.
- Garantiza la idempotencia mediante cláusula `ON CONFLICT (code) DO NOTHING`.

## Seed de Plantillas
El método `seed_outbound_templates()` y `seed_dispatch_templates()` de los servicios se ejecutan de manera segura al inicializar las solicitudes, registrando la ruta física y hashes del HTML.
