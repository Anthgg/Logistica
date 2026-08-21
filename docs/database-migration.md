# Migración de geolocalización de almacén

Revisión Alembic: `km490110049wh`

Revisión anterior: `jl480110048dk`

La migración agrega, sin borrar ni renombrar columnas:

- `uses_branch_location BOOLEAN NOT NULL DEFAULT true`;
- `latitude NUMERIC(10,7) NULL`;
- `longitude NUMERIC(10,7) NULL`;
- checks de rango y `chk_warehouses_location_mode`.

Las filas existentes quedan heredadas con ambas coordenadas propias nulas. No se ejecuta geocoding, no se copian coordenadas de sede y no se toca `address`.

También ejecuta `ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY`. La sentencia es idempotente y no elimina, reemplaza ni amplía policies. La prueba PostgreSQL crea una policy centinela antes del upgrade y verifica que su `USING` y `WITH CHECK` sobrevivan sin cambios.

## Orden coordinado futuro

1. pipeline canónico de database release;
2. backend;
3. frontend;
4. smoke E2E.

No ejecutar `alembic upgrade head` manualmente contra producción ni aplicar SQL desde Supabase Dashboard.
