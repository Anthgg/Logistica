# 02. Modelo de Instancia de Documento

El modelo `DocumentInstanceModel` actúa como la entidad raíz que representa un documento físico o digital en el sistema.

## Propiedades Clave
- **id**: Identificador único global (UUID).
- **document_code**: Código físico estructurado final (ej. `PED-LIM-2026-000001`).
- **status**: Estado actual de la máquina de estados (`DRAFT`, `ISSUED`, `CANCELLED`).
- **sensitivity**: Clasificación de privacidad (`PUBLIC`, `INTERNAL`, `RESTRICTED`, `CONFIDENTIAL`).
- **print_request_count**: Contador total de solicitudes físicas de impresión.
- **reprint_count**: Contador total de copias físicas oficiales de reimpresión generadas.
