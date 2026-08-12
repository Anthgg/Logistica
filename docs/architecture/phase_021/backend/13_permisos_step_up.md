# 13. Permisos RBAC y Autenticación Step-Up (Fase 021)

## 🔑 Catálogo de Permisos RBAC de la Fase 021

La **Fase 021** registra un conjunto granular de 14 permisos RBAC dentro del subsistema logístico (`logistics.*`). Estos permisos son validados por la dependencia `require_permission` en la capa de routers FastAPI.

| Código del Permiso | Nombre Funcional | Descripción del Acceso |
|---|---|---|
| `logistics.company_profile.read` | Leer Ficha Institucional | Permite consultar la información legal y configuraciones de la empresa. |
| `logistics.company_profile.create` | Inicializar Ficha Institucional | Permite crear el perfil inicial y generar versiones borrador SemVer. |
| `logistics.company_profile.update` | Modificar Ficha Institucional | Permite actualizar datos tributarios, razón social y teléfonos. |
| `logistics.company_profile.activate` | Activar Versión SemVer | Permite activar oficialmente una versión institucional congelada. |
| `logistics.company_profile.read_history` | Consultar Histórico SemVer | Permite examinar versiones `DRAFT` y `DEPRECATED` del perfil. |
| `logistics.company_addresses.read` | Leer Direcciones | Consultar el catálogo de direcciones institucionales. |
| `logistics.company_addresses.manage` | Gestionar Direcciones | Crear, editar y establecer la dirección principal de la empresa. |
| `logistics.company_contacts.read` | Leer Contactos | Consultar el directorio de contactos institucionales. |
| `logistics.company_contacts.manage` | Gestionar Contactos | Crear, editar y marcar contactos principales por área. |
| `logistics.company_assets.read` | Leer Activos Gráficos | Consultar y descargar logotipos y firmas visuales. |
| `logistics.company_assets.upload` | Cargar Activos Gráficos | Subir imágenes PNG/JPEG/WebP para sanitización y storage. |
| `logistics.company_assets.activate` | Activar Activos Gráficos | Aprobar y activar un activo gráfico cargado. |
| `logistics.company_assets.revoke` | Revocar Activos Gráficos | Inhabilitar un logotipo o sello institucional. |
| `logistics.authorized_signers.read` | Leer Firmantes Autorizados | Consultar la lista de apoderados y firmantes registrados. |
| `logistics.authorized_signers.create` | Registrar Firmante | Crear un nuevo firmante autorizado con facultades. |
| `logistics.authorized_signers.update` | Modificar Firmante | Editar montos, facultades o asociar firma visual. |
| `logistics.authorized_signers.activate` | Activar Firmante | Aprobar la habilitación operativa de un firmante. |
| `logistics.authorized_signers.revoke` | Revocar/Suspender Firmante | Suspender o revocar definitivamente a un firmante (exige motivo). |
| `logistics.numbering_policies.read` | Leer Políticas Numeración | Consultar patrones de formato visual de numeración. |
| `logistics.numbering_policies.create` | Crear Políticas Numeración | Registrar o actualizar patrones de presentación estética. |

---

## 🔐 Requerimiento de Step-Up Authentication

La modificación de datos institucionales sensibles y la gestión de apoderados legales representan operaciones de alto riesgo para la seguridad de la empresa. Por ello, la Fase 021 exige **Autenticación Step-Up (Re-autenticación por Contraseña / MFA)** en las siguientes operaciones críticas:

```mermaid
graph TD
    A[Usuario solicita Operación Crítica] --> B{¿Es una Acción Sensible?}
    B -- Sí: Activar Versión SemVer / Revocar Firmante / Cambiar RUC --> C{¿Token JWT posee Step-Up Freshness?}
    C -- No / Expirado > 15 min --> D[Retornar HTTP 403 Step-Up Required]
    D --> E[Usuario Re-ingresa Contraseña / Token TOTP]
    E --> F[Emite Token JWT con Claim 'amr': ['mfa'] / Fresh]
    F --> G[Re-intenta Operación Crítica]
    G --> H[Procesar Transacción & Escribir Auditoría High Severity]
    C -- Sí: Token Válido --> H
```

### Operaciones que Exigen Step-Up:
1. `POST /company-profile/versions/{id}/activate`: La activación de una nueva versión SemVer altera la razón social o RUC oficial para todos los documentos futuros.
2. `POST /company-profile/signers/{id}/revoke`: La revocación legal de poderes de un firmante es irretroversible y registra un evento de auditoría de severidad `CRITICAL`.
3. `PATCH /company-profile` (Cambio de RUC / Razón Social): La alteración de identificadores tributarios principales.
