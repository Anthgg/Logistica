# Auditoría de Documentos de Inventario (Phase 017)

## Propósito
Garantizar la inmutabilidad y la trazabilidad de cada interacción con los documentos de inventario (EUB, PUT, MOV, AJI, CNT, ADI, TRA, CRT) durante su ciclo de vida de generación y previsualización.

## Eventos Registrados
Todos los eventos se registran de forma centralizada en la base de datos de auditoría usando `AuditService`:
- `logistics.inventory_document.preview_rendered`: Disparado al previsualizar un PDF.
- `logistics.inventory_document.preview_downloaded`: Disparado al descargar el archivo PDF.
- `logistics.inventory_document.package_manifest_created`: Disparado al evaluar las reglas de inclusión del manifiesto.

## Datos de Trazabilidad
Cada registro de auditoría almacena:
- `user_id`: Identificador del usuario que realiza la acción.
- `session_id`: Sesión activa para correlación de seguridad.
- `resource_id`: Código del tipo de documento (ej. `AJI`).
- `event_metadata`: Detalles del render (tamaño del PDF, hash del contenido, estado del conteo ciego, etc.).
