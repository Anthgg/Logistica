# F007 · Matriz de Permisos RBAC de Auditoría

## 1. Permisos Definidos
1. **`logistics.audit.read`**: Permite consultar la lista paginada de eventos, ver el detalle completo con diffs Before/After, y ejecutar la verificación de integridad criptográfica SHA-256.
2. **`logistics.audit.export`**: Permite exportar y descargar eventos de auditoría en formato CSV. Cada exportación genera automáticamente un evento `logistics.audit.exported`.
3. **`logistics.audit.read_sensitive`**: Permite visualizar direcciones IP reales del cliente sin máscara `[REDACTED]`.

## 2. Asignación en Matriz de Roles (`ROLE_PERMISSION_MATRIX`)
- **`LOGISTICS_ADMIN`**: `read`, `export`, `read_sensitive`.
- **`LOGISTICS_AUDITOR`**: `read`, `export`, `read_sensitive`.
- **`LOGISTICS_MANAGER`**: `read`, `export`.
- **`LOGISTICS_OPERATOR`**: Sin acceso a auditoría (403 Forbidden).\n