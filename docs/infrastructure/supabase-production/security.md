# Seguridad, RBAC y Gestión de Secretos

## 1. Gestión de Secretos

- **Regla Estricta:** Ninguna credencial de base de datos (`DATABASE_URL`, passwords, tokens) se almacena en el control de versiones Git, Dockerfiles ni código fuente.
- **Producción:** Las credenciales son inyectadas en tiempo de ejecución en Cloud Run mediante variables de entorno seguras / Secret Manager.
- **Frontend:** El frontend React nunca recibe `DATABASE_URL`, claves de rol ni contraseñas de PostgreSQL. El frontend se comunica exclusivamente con la API REST FastAPI.

---

## 2. RBAC vs Row Level Security (RLS)

- **Control de Acceso a Nivel de Aplicación (RBAC):**
  El sistema implementa un modelo completo de Control de Acceso Basado en Roles (RBAC) gestionado por la aplicación FastAPI:
  - Tablas: `logistics_permissions`, `logistics_roles`, `logistics_role_permissions`, `logistics_role_assignments`.
  - Validación en cada endpoint mediante dependencias de seguridad FastAPI (`get_current_user`, `require_permissions`).
  - Alcances granulares por organización, sucursal y almacén.

- **Políticas RLS en PostgreSQL:**
  Las tablas creadas en Supabase cuentan con la bandera de RLS habilitada a nivel de tabla por defecto de la plataforma. Debido a que el backend se conecta con un rol autorizado a nivel de base de datos y aplica la lógica de seguridad y multi-tenancy en la capa de servicio FastAPI, no se requiere duplicar cientos de políticas RLS manuales en la base de datos durante esta fase.

---

## 3. Cifrado y Red

- **Cifrado en Tránsito:** Todas las comunicaciones entre Cloud Run y Supabase se ejecutan bajo TLS/SSL forzado (`sslmode=require`).
- **Cifrado en Reposo:** Supabase aplica cifrado AES-256 en reposo sobre los volúmenes de almacenamiento subyacentes.
