# 18. Estructura de la Migración

La migración Alembic `k220110020dc_add_document_lifecycle_tables.py` crea la estructura física relacional en la base de datos de PostgreSQL.

## Tablas Creadas
- `logistics_document_instances`: Instancias de documentos.
- `logistics_document_snapshots`: Payloads inmutables serializados en JSONB.
- `logistics_document_artifacts`: Binarios PDF y archivos ZIP.
- `logistics_document_reprints`: Bitácora de reimpresiones.
- `logistics_document_cancellations`: Bitácora de anulaciones.
- `logistics_document_export_jobs`: Trabajos de exportación masiva en lote.
