# 13 — Especificación de Endpoints del Catálogo Documental

## Catálogo de Endpoints REST (`/api/logistics/document-catalog`)

| Método | Endpoint | Permiso Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/document-catalog` | `logistics.documents.read` | Resumen y versión activa del catálogo global |
| `GET` | `/document-catalog/version` | `logistics.documents.read` | Metadatos de versión SemVer del catálogo |
| `GET` | `/document-catalog/families` | `logistics.documents.read` | Listar familias documentales |
| `GET` | `/document-catalog/families/{family_code}` | `logistics.documents.read` | Detalle de una familia documental |
| `GET` | `/document-catalog/retention-policies` | `logistics.documents.read` | Listar políticas de retención |
| `GET` | `/document-catalog/types` | `logistics.documents.read` | Listar tipos documentales con filtros |
| `GET` | `/document-catalog/types/{code}` | `logistics.documents.read` | Detalle completo de un tipo documental |
| `GET` | `/document-catalog/types/{code}/versions` | `logistics.documents.read` | Historial de versiones del tipo documental |
| `GET` | `/document-catalog/types/{code}/active-version` | `logistics.documents.read` | Versión activa del contrato |
| `POST` | `/document-catalog/validate` | `logistics.integrations.configure` | Validación administrativa en modo Dry-run |
