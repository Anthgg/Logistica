# 22 — Matriz RBAC y Requisitos de Step-Up Authentication

## 1. Matriz de Permisos RBAC

| Rol de Usuario | `ruc_lookup.read` | `ruc_imports.execute` | `ruc_datasets.activate` | `ruc_assisted.create` | `ruc_conflicts.resolve` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Purchasing Agent** (Agente Compras) |  Sí | ❌ No | ❌ No |  Sí | ❌ No |
| **Logistics Manager** (Jefe Logística) |  Sí | ❌ No | ❌ No |  Sí |  Sí |
| **Compliance / Legal Officer** |  Sí | ❌ No | ❌ No |  Sí |  Sí |
| **Logistics Admin** (Admin Sistema) |  Sí |  Sí |  Sí (Step-Up) |  Sí |  Sí |
| **System Cron** (Servicio Cloud) | ❌ No |  Sí |  Sí | ❌ No | ❌ No |

---

## 2. Requisito de Step-Up Authentication

Las operaciones críticas de cambio de estado de infraestructura (**`ruc_datasets.activate`** y **`ruc_datasets.rollback`**) requieren la re-verificación de credenciales del usuario mediante **Step-Up Authentication** (código TOTP / OTP de un solo uso o re-autenticación de contraseña).

### Encabezado Requerido:
```http
X-Step-Up-Token: <MFA_VERIFIED_TOKEN>
```

Si el token Step-Up no está presente o expiró, el endpoint retorna `HTTP 403 Forbidden` con el código de error `STEP_UP_REQUIRED`.
