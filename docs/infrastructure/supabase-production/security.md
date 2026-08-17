# Seguridad, RBAC, RLS y Exposición de Data API

## 1. Gestión de Secretos

- **Regla Estricta:** Ninguna credencial de base de datos (`DATABASE_URL`, passwords, tokens, API keys) se almacena en el control de versiones Git, Dockerfiles ni código fuente.
- **Producción:** Las credenciales son inyectadas en tiempo de ejecución en Cloud Run mediante variables de entorno seguras / Google Cloud Secret Manager.
- **Frontend:** El frontend React nunca recibe `DATABASE_URL`, claves de conexión ni `service_role` de Supabase. El frontend se comunica exclusivamente con la API REST FastAPI.

---

## 2. Auditoría de Seguridad PostgreSQL & RLS Post-Reconciliación

Auditoría ejecutada en vivo contra Supabase PostgreSQL 17.6 (`public` schema):

- **TOTAL_APPLICATION_TABLES:** 380
- **RLS_ENABLED_COUNT:** 380 (100% de las tablas tienen `relrowsecurity = true`)
- **RLS_DISABLED_COUNT:** 0
- **RLS_FORCED_COUNT:** 0

### Exposición de Data API (PostgREST)
- **DATA_API_USED_BY_APP:** `NO` (El sistema utiliza conexión directa PostgreSQL desde FastAPI en Cloud Run).
- **Estado de Seguridad:** `DATA_API_EXPOSED_BUT_SECURED`
- **Grants para roles Supabase (`anon`, `authenticated`, `service_role`):**
  - Los roles heredan privilegios estándar a través de `pg_default_acl` en el esquema `public`.
  - **Mecanismo de Protección:** Al estar RLS habilitado en el 100% de las tablas (380/380) sin políticas permisivas para clientes anónimos o autenticados de Supabase, cualquier intento de acceso directo vía Data API/PostgREST devuelve 0 registros o acceso denegado.
  - **Rol de Aplicación Cloud Run:** El backend se conecta mediante el rol directo de base de datos (`postgres`), el cual opera como propietario sobre las tablas gestionadas y no es bloqueado por RLS.

---

## 3. Cobertura de Enforcement RBAC

- **Infraestructura RBAC en FastAPI:**
  FastAPI implementa la infraestructura RBAC y tenant scope mediante tablas relacionales:
  - `logistics_permissions` (509 permisos registrados)
  - `logistics_roles`
  - `logistics_role_permissions` (1390 asignaciones)
  - `logistics_role_assignments`
- **Alcance y Gaps Conocidos:**
  La cobertura de enforcement se valida fase por fase en el ciclo de vida del proyecto.
  > **Nota de Auditoría F004:** La Fase 004 cuenta con gaps conocidos en los routers de `Organization`, `Branch` y `Warehouse` que actualmente emplean `get_current_user` / `require_active_user` y cuya remediación de granularidad RBAC está asignada a la Fase 004. NO se asume cobertura total en cada endpoint sin validación de fase.

---

## 4. Cifrado y Red

- **Cifrado en Tránsito:** Todas las comunicaciones entre Cloud Run y Supabase se ejecutan bajo TLS/SSL forzado (`sslmode=require`).
- **Cifrado en Reposo:** Supabase aplica cifrado AES-256 en reposo sobre los volúmenes de almacenamiento subyacentes.
