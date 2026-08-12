# Auditoría previa

Se encontraron maestros reutilizables para organizaciones, sedes, almacenes, socios de negocio, roles de proveedor/transportista, vehículos, conductores, unidades, archivos y documentos. También se reutilizaron las órdenes de compra modulares de procurement y el motor documental existente.

Los riesgos encontrados fueron: coexistencia de routers legacy, ausencia de un outbox genérico, deriva histórica entre metadata y Alembic y falta de documentación de la Fase 035. Por eso la Fase 036 introduce únicamente un outbox acotado a inbound y no elimina componentes legacy.

No se usa `user.organization_id`; el tenant se obtiene desde `LogisticsPrincipal` y `resolve_organization_id`.

