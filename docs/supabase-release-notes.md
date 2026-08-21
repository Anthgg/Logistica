# Supabase release notes: warehouse geolocation

Estado: preparado, no aplicado en producción.

La revisión `km490110049wh` alinea el DDL canónico de Alembic con el RLS que el baseline Supabase ya habilita para `public.warehouses`. No introduce policies permisivas, grants nuevos, índices nuevos ni cambios de tenancy.

Validación requerida por el job de integración antes de promover:

- head Alembic único;
- columnas y tres check constraints presentes;
- filas legacy en modo heredado, sin coordenadas inventadas;
- RLS habilitado;
- conjunto y definiciones de policies sin cambios;
- foreign keys e índices existentes preservados;
- backend desplegado antes del frontend que envía el DTO aditivo.

Rollback de aplicación: revertir backend/frontend. El downgrade de esquema elimina únicamente las tres columnas y sus checks; no deshabilita RLS porque su estado puede ser anterior a esta revisión.
