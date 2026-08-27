# F007 · Esquema Canónico de Eventos de Auditoría

## 1. Modelo de Datos (`logistics_audit_events`)
El modelo `LogisticsAuditEvent` implementa los siguientes campos clave:

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Identificador único del evento |
| `event_code` | VARCHAR(100) | Código estructurado en formato `logistics.<dominio>.<accion>` |
| `event_category` | VARCHAR(50) | Categoría del evento (`organization`, `branch`, `warehouse`, `security`, etc.) |
| `event_version` | VARCHAR(20) | Versión del catálogo de eventos (default `1.0.0`) |
| `occurred_at` | TIMESTAMPTZ | Fecha y hora exacta UTC del suceso |
| `actor_user_id` | UUID | Identificador del usuario autenticado (extraído del Principal) |
| `actor_display_name_snapshot` | VARCHAR(200) | Nombre o snapshot del actor |
| `actor_role_codes_snapshot` | TEXT | Roles del actor al momento de la operación |
| `session_id` | UUID | ID de la sesión activa |
| `device_id` | UUID | ID del dispositivo |
| `ip_address` | VARCHAR(45) | Dirección IP del cliente (enmascarada para usuarios no privilegiados) |
| `action` | VARCHAR(50) | Acción ejecutada (`create`, `update`, `delete`, `export`, etc.) |
| `result` | VARCHAR(20) | Resultado de la operación (`success`, `failure`, `denied`, `error`) |
| `severity` | VARCHAR(20) | Nivel de criticidad (`info`, `low`, `medium`, `high`, `critical`) |
| `resource_type` | VARCHAR(50) | Tipo del recurso afectado (`organization`, `branch`, `warehouse`, etc.) |
| `resource_id` | VARCHAR(100) | Identificador del recurso afectado |
| `organization_id` | UUID | Ámbito de organización |
| `branch_id` | UUID | Ámbito de sede |
| `warehouse_id` | UUID | Ámbito de almacén |
| `previous_data` | JSONB | Estado anterior sanitizado |
| `new_data` | JSONB | Estado posterior sanitizado |
| `changed_fields` | JSONB / ARRAY | Lista de propiedades modificadas calculadas automáticamente |
| `event_hash` | VARCHAR(64) | Hash SHA-256 para validación de integridad |\n