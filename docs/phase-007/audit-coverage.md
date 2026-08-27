# F007 · Cobertura de Eventos Catalogados

## 1. Catálogo Centralizado (`EVENT_CATALOG`)
El módulo `app.modules.logistics.audit.catalog` cataloga más de 120 códigos de eventos estándar agrupados por categorías:

- **Organización & Estructura**:
  - `logistics.organization.created`, `logistics.organization.updated`, `logistics.organization.status_changed`
  - `logistics.branch.created`, `logistics.branch.updated`, `logistics.branch.geolocation_updated`
  - `logistics.warehouse.created`, `logistics.warehouse.updated`, `logistics.warehouse.geolocation_updated`
- **Seguridad & RBAC**:
  - `logistics.role.created`, `logistics.role.updated`, `logistics.role.assignment_created`, `logistics.role.assignment_revoked`
  - `logistics.security.session_created`, `logistics.security.step_up_requested`, `logistics.security.step_up_completed`
- **Documentos & Numeración**:
  - `logistics.document.created`, `logistics.document.printed`, `logistics.document.cancelled`
  - `logistics.series.created`, `logistics.series.updated`
- **Operaciones de Auditoría**:
  - `logistics.audit.queried`, `logistics.audit.exported`, `logistics.audit.integrity_verified`

## 2. Validación de Códigos
Todo evento emitido mediante `audit_service.write_event` es validado con `is_valid_event_code()`. La emisión de códigos arbitrarios o fuera de catálogo es rechazada preventivamente.\n