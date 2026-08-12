# 11. Exportaciones ZIP

El backend ofrece endpoints asíncronos para empaquetar grandes selecciones de documentos en archivos comprimidos ZIP seguros.

## Estructura del ZIP
- `manifest.json`: Listado de metadatos de los documentos exportados, incluyendo hashes originales.
- `manifest.csv`: Formato legible para importación directa en hojas de cálculo.
- `checksums.sha256`: Firmas electrónicas de verificación para cada PDF contenido en el ZIP.
- `*.pdf`: Los archivos individuales correspondientes.

## Límites y Seguridad
- Máximo 100 elementos por exportación.
- Tamaño total máximo de 100 MB.
- Prevención de **Zip Slip**: Los nombres de archivo se sanitizan descartando secuencias de escape de ruta (ej. `../`).
