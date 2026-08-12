# Registro de Auditoría de Inventario (Phase 017)

## Trazabilidad de Operaciones
Se registran logs inmutables en la base de datos de auditoría para cada operación de renderizado:
- **Preview de Documento**: Registra el tamaño en bytes, el hash del archivo y si se ejecutó en modo conteo ciego.
- **Descarga de PDF**: Registra la descarga del archivo de previsualización protegido.
- **Generación de Manifiesto**: Registra el modo de paquete y la cantidad de documentos incluidos.

## Estructura de Metadatos
Los metadatos se guardan en formato JSON, facilitando búsquedas complejas y análisis forense sobre el uso de documentos internos.
