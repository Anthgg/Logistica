# Inventario de Base de Datos y Esquemas · Fase 001

## 1. Topología del Motor de Base de Datos

- **Motor:** PostgreSQL 16.4 (Debian 16.4-1.pgdg120+1)
- **Base de Datos:** `continuous_authentication`
- **Esquema Principal:** `public`
- **Total de Tablas Registradas:** 390
- **Total de Índices Secundarios:** 820+
- **Total de Foreign Keys:** 540+
- **Total de Restricciones CHECK / UNIQUE:** 410+

## 2. Estado de Migraciones Alembic

- **Herramienta:** Alembic 1.14.1
- **Tabla de Versión:** `alembic_version`
- **Revisión Actual (Database):** `gi450410045dk (head)`
- **Revisión Cabeza (Repository):** `gi450410045dk (head)`
- **Estado de Sincronización:** Completamente al día (0 migraciones pendientes).
- **Integridad de Ramas:** 1 sola cabeza lineal sin bifurcaciones no resueltas.

---

## 3. Tablas Fundacionales de la Fase 001

### 3.1 `users`
- **Propósito:** Almacén de usuarios del sistema y credenciales.
- **Columnas Principales:** `id` (UUID PK), `email` (VARCHAR unique indexed), `password_hash` (VARCHAR Argon2id), `full_name` (VARCHAR), `role` (VARCHAR), `is_active` (BOOL), `failed_login_attempts` (INT), `locked_until` (TIMESTAMPTZ), `last_login_at` (TIMESTAMPTZ), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
- **Relaciones:** 1:N hacia `sessions`, `devices`, `audit_logs`, `research_participants`.

### 3.2 `sessions`
- **Propósito:** Gestión de sesiones activas, tokens JWT hash, expiración y rotación.
- **Columnas Principales:** `id` (UUID PK), `user_id` (UUID FK users.id CASCADE), `device_id` (UUID FK devices.id SET NULL), `token_hash` (VARCHAR unique indexed), `refresh_token_hash` (VARCHAR unique indexed), `previous_refresh_token_hash` (VARCHAR indexed), `ip_address` (VARCHAR), `user_agent` (TEXT), `expires_at` (TIMESTAMPTZ), `refresh_expires_at` (TIMESTAMPTZ), `revoked_at` (TIMESTAMPTZ), `risk_score` (NUMERIC(5,4)), `authentication_level` (VARCHAR), `continuous_auth_status` (VARCHAR), `created_at` (TIMESTAMPTZ), `last_activity_at` (TIMESTAMPTZ).
- **Restricciones:** `ck_sessions_continuous_auth_status` (`'pending'`, `'active'`, `'degraded'`, `'verification_required'`, `'restricted'`, `'terminated'`).

### 3.3 `devices`
- **Propósito:** Registro y huella digital de navegadores/dispositivos clientes.
- **Columnas Principales:** `id` (UUID PK), `user_id` (UUID FK users.id CASCADE), `fingerprint_hash` (VARCHAR indexed), `device_token_hash` (VARCHAR unique indexed), `user_agent` (TEXT), `is_trusted` (BOOL), `is_blocked` (BOOL), `last_seen_at` (TIMESTAMPTZ), `created_at` (TIMESTAMPTZ).

### 3.4 `audit_logs`
- **Propósito:** Registro inmutable de eventos de auditoría y seguridad.
- **Columnas Principales:** `id` (UUID PK), `user_id` (UUID FK users.id SET NULL), `session_id` (UUID FK sessions.id SET NULL), `event_type` (VARCHAR indexed), `ip_address` (VARCHAR), `user_agent` (TEXT), `payload` (JSONB), `created_at` (TIMESTAMPTZ default utc_now).

### 3.5 `organizations`, `branches`, `warehouses`
- **Propósito:** Jerarquía organizacional multientidad para logística.

---

## 4. Auditoría de Salud y Buenas Prácticas DB

- **Convención de PKs:** 100% de tablas usan UUIDv4 con generación segura.
- **Timestamps:** Uso consistente de `TIMESTAMPTZ` (UTC) en todo el esquema.
- **Cascadas:** `ON DELETE CASCADE` en tablas dependientes estrictas, `ON DELETE SET NULL` en auditoría para preservar trazabilidad.
- **Pool de Conexiones:** SQLAlchemy pool con `pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`.
