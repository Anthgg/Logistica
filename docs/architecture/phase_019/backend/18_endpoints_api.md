# Endpoints de la API (Phase 019)

## Endpoints de Transporte y Entrega
- `/api/logistics/transport/documents/{document_type_code}/preview`
- `/api/logistics/transport/documents/{document_type_code}/pdf`
- `/api/logistics/transport/document-package/manifest`
- `/api/logistics/transport/document-package/preview`
- `/api/logistics/delivery/documents/{document_type_code}/preview`
- `/api/logistics/delivery/documents/{document_type_code}/pdf`

## Secuencia de Endpoints
```mermaid
sequenceDiagram
    Client->>API: POST /preview con Payload Contexto
    API->>Service: Validar con Pydantic y enmascarar
    Service->>Engine: Renderizar HTML/PDF
    Engine->>API: PDF en base64 / Bytes
    API->>Client: Retornar PDF Inline/Attachment
```
