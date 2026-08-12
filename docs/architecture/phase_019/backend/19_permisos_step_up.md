# Permisos y Step-Up (Phase 019)

## Matriz de Permisos
- `logistics.transport_documents.read`: Permite previsualizar documentos de transporte.
- `logistics.transport_documents.read_sensitive`: Permite visualizar DNI/Licencias.

## Flujo Step-Up
```mermaid
flowchart TD
    Request[Solicitar Datos Sensibles] --> CheckPerm{¿Tiene sensitive_read?}
    CheckPerm -->|No| PromptStepUp[Solicitar Step-Up Authentication]
    CheckPerm -->|Sí| ShowData[Mostrar Datos Completo]
```
