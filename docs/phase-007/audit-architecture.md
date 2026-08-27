# F007 · Arquitectura de Auditoría Unificada

## 1. Visión General
El sistema de auditoría unificada de Logistics proporciona una pista de auditoría inmutable (append-only), criptográficamente verificable mediante hashes SHA-256 por registro, con sanitización estricta de secretos (AUDIT_SECRET_LEAKS=0), aislamiento multi-inquilino (tenant-scoped) y exportación controlada en formato CSV (UTF-8 con BOM).

## 2. Componentes Principales
- **LogisticsAuditEvent (`app.modules.logistics.audit.models_event`)**: Modelo SQLAlchemy canónico que mapea a la tabla `logistics_audit_events` (45 columnas, soporte JSONB, 15 índices, Row Level Security en PostgreSQL/Supabase).
- **AuditService (`app.modules.logistics.audit.service`)**: Servicio singleton centralizado para:
  - Registro de eventos (`write_event`, `record_event`).
  - Cálculo de hash SHA-256 (`_compute_hash`) sobre snapshot determinista de la entidad.
  - Verificación de integridad (`verify_integrity`).
  - Filtrado multidimensional con acotamiento de inquilino (`_build_filters`, `list`).
  - Exportación de auditoría (`export_csv`) con streaming y enmascaramiento de IP (`[REDACTED]`).
- **Audit Sanitizer (`app.modules.logistics.audit.sanitizer`)**: Módulo de seguridad que intercepta y redacta recursivamente tokens, claves, contraseñas y datos biométricos antes de la persistencia.
- **Audit Router (`app.modules.logistics.audit.api.router`)**: Endpoints HTTP protegidos por RBAC (`logistics.audit.read`, `logistics.audit.export`, `logistics.audit.read_sensitive`).

## 3. Garantías de Seguridad
- **Append-Only**: No existen endpoints HTTP ni métodos de servicio para `DELETE`, `UPDATE` o `PURGE` de eventos de auditoría (`AUDIT_UPDATE_API_COUNT=0`, `AUDIT_DELETE_API_COUNT=0`).
- **Aislamiento Multi-Tenant**: Las consultas de auditoría validan rigurosamente el ámbito del `LogisticsPrincipal`. Un usuario asignado a una organización nunca puede leer eventos de otra (`CROSS_TENANT_AUDIT_ACCESS=DENIED`).
- **Registro Inmutable**: Cada evento posee un hash SHA-256 generado con su identificador UUID y fecha `occurred_at`.\n