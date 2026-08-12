# Migración de Tipos de Documento (Phase 017)

## Detalles de la Migración `h770080017dc`
- **upgrade()**: Inserta de manera segura los 3 tipos de documento propuestos (`EUB`, `ADI`, `CRT`) en la tabla `document_types`.
  - Utiliza `ON CONFLICT (code) DO NOTHING` para garantizar la idempotencia de la migración.
  - Verifica la existencia previa de la tabla para evitar fallas en ambientes limpios.
- **downgrade()**: Elimina los registros insertados limpiando el catálogo de tipos propuestos.
