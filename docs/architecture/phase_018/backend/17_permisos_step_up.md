# Matriz de Roles y Permisos (Phase 018)

## Permisos Introducidos
- `logistics.outbound_documents.read`
- `logistics.outbound_documents.preview`
- `logistics.outbound_documents.download`
- `logistics.outbound_documents.read_sensitive` (gating de costos y contactos)
- `logistics.dispatch_documents.read`
- `logistics.dispatch_documents.preview`
- `logistics.dispatch_documents.download`

## Matriz Rol-Permiso
- **WAREHOUSE_OPERATOR**: Solo previsualiza PICK/PACK. Sin acceso sensible.
- **DISPATCH**: Previsualiza MAN/ADSP/CPR y todos los de salida.
- **LOGISTICS_MANAGER**: Control completo de previsualizaciones y descargas.
