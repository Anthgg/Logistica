# 23 — Permisos RBAC y Autenticación Step-Up Security

## Matriz de Permisos RBAC (`logistics.drivers.*`)

El acceso a las funcionalidades y datos del Maestro de Conductores se controla granularmente mediante el sistema de **Role-Based Access Control (RBAC)** de la plataforma.

---

## Catálogo de Permisos

| Permiso | Descripción | Roles Típicos Asignados |
|---|---|---|
| **`logistics.drivers.read`** | Permite listar y consultar detalles de conductores con campos enmascarados (`*****153`). | Dispatcher, Logistics Clerk, Auditor, Safety Inspector |
| **`logistics.drivers.create`** | Registrar nuevos conductores en estado `DRAFT` o `PENDING_VERIFICATION`. | Fleet Manager, Logistics Admin |
| **`logistics.drivers.update`** | Editar datos de conductores, licencias y certificados. | Fleet Manager, Logistics Admin |
| **`logistics.drivers.delete`** | Archivar o desactivar registros de conductores. | System Admin, Logistics Manager |
| **`logistics.drivers.sensitive.read`** | Requerido para solicitar la unmasking/revelación de DNI y Licencia mediante Step-Up. | Compliance Officer, Security Chief |
| **`logistics.drivers.restrictions.manage`** | Aplicar bloqueos administrativos, sanciones y inhabilitaciones operativas. | Safety Chief, HR Manager |
| **`logistics.drivers.restrictions.revoke`** | Levantar / revocar sanciones operativas registradas. | Safety Chief, Logistics Director |

---

## Autenticación Step-Up Security para Datos Sensibles

La lectura de datos de identificación sin enmascarar (DNI y Licencia completos) exige un mecanismo de **Step-Up Authentication** para prevenir la exfiltración masiva de datos personales.

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuario / Guardilla
    participant API as Backend API (/sensitive-reveal)
    participant Auth as StepUpAuthService
    participant Audit as AuditLogger

    User->>API: POST /drivers/{id}/sensitive-reveal (Token JWT Estándar)
    API->>Auth: Verify RBAC Permission (logistics.drivers.sensitive.read)
    Auth-->>API: OK Permiso Confirmado
    API->>Auth: Validate Step-Up Token (¿Re-auth en últimos 5 min?)
    alt Token Step-Up Inválido o Ausente
        Auth-->>API: Error 401 Step-Up Required
        API-->>User: HTTP 401 ("Se requiere re-autenticación con contraseña o TOTP")
    else Token Step-Up Válido
        Auth-->>API: OK Step-Up Verificado
        API->>Audit: Log Sensitive Read Event (DRV_SENSITIVE_DATA_REVEALED)
        Audit-->>API: Event Saved
        API-->>User: Retorna DNI / Licencia Des-enmascarados
    end
```

### Requisitos del Token Step-Up:
1. El usuario debe re-ingresar su contraseña o un código **MFA/TOTP (One-Time Password)** dentro de un endpoint de re-autenticación (`POST /api/auth/step-up`).
2. El servidor emite un token efímero firmado por clave privada con expiración de **300 segundos (5 minutos)**.
3. El token efímero debe ser enviado en el cuerpo o cabecera `X-Step-Up-Token` al consumir la revelación sensible.
