# Matriz de Permisos RBAC y Autenticación Elevada (Step-Up Auth)

## 1. Descripción General

El acceso a las funcionalidades del subsistema de verificaciones vehiculares está restringido mediante el modelo **RBAC (Role-Based Access Control)** del ERP.

Adicionalmente, aquellas operaciones que alteran el estado operativo de los vehículos, aprueban verificaciones asistidas manuales o resuelven conflictos de severidad crítica requieren obligatoriamente **Autenticación Elevada (Step-Up Authentication)** mediante la re-ingreso de credenciales o token MFA (TOTP / Hardware Key) para prevenir acciones fraudulentas o no autorizadas.

---

## 2. Catálogo de Permisos RBAC de la Fase 028

| Código del Permiso RBAC | Nombre del Permiso | Operaciones Autorizadas | Exige Step-Up Auth |
|---|---|---|---|
| `logistics.vehicle_verifications.read` | Consultar Verificaciones | Visualizar historial de verificaciones, provenance de campos y estado de conflictos | No |
| `logistics.vehicle_verifications.create` | Solicitar Verificación | Iniciar una verificación automatizada contra fuentes oficiales o proveedor | No |
| `logistics.vehicle_verifications.apply` | Aplicar Datos Verificados | Sobreescribir atributos en `VehicleModel` y congelar versión `VehicleVersionModel` | **SÍ** |
| `logistics.vehicle_verifications.resolve_conflict` | Resolver Conflictos | Dispensar, anular o resolver discrepancias en `VehicleVerificationConflictModel` | **SÍ** |
| `logistics.assisted_verifications.create` | Registrar Verificación Asistida | Ingresar datos manuales y cargar evidencias PDF/JPG de soporte | No |
| `logistics.assisted_verifications.approve` | Aprobar Verificación Asistida | Dar conformidad a la verificación manual (exige Creador != Aprobador) | **SÍ** |
| `logistics.verification_sources.manage` | Gestionar Fuentes | Crear, editar o deshabilitar fuentes y credenciales API en `ProviderConfigs` | **SÍ** |

---

## 3. Matriz de Asignación por Roles del Sistema

| Permiso RBAC | Administrador Logística | Oficial de Compliance | Operador de Registro | Auditor / Consulta |
|---|:---:|:---:|:---:|:---:|
| `logistics.vehicle_verifications.read` | ✓ | ✓ | ✓ | ✓ |
| `logistics.vehicle_verifications.create` | ✓ | ✓ | ✓ | ✗ |
| `logistics.vehicle_verifications.apply` | ✓ | ✓ | ✗ | ✗ |
| `logistics.vehicle_verifications.resolve_conflict` | ✓ | ✓ | ✗ | ✗ |
| `logistics.assisted_verifications.create` | ✓ | ✗ | ✓ | ✗ |
| `logistics.assisted_verifications.approve` | ✓ | ✓ | ✗ | ✗ |
| `logistics.verification_sources.manage` | ✓ | ✗ | ✗ | ✗ |

---

## 4. Requerimientos de Autenticación Elevada (Step-Up Auth)

### Endpoints Protegidos por Step-Up Auth
1. `POST /api/v1/logistics/vehicle-verifications/{id}/apply`
2. `POST /api/v1/logistics/assisted-verifications/{id}/approve`
3. `POST /api/v1/logistics/vehicle-verification-conflicts/{id}/resolve`
4. `PUT /api/v1/logistics/vehicle-verification-sources/{id}/provider-config`

### Flujo de Verificación Step-Up
Cuando el cliente realiza una petición a un endpoint protegido por Step-Up Auth sin el encabezado `X-StepUp-Token` válido o con un token cuya vigencia sea mayor a **5 minutos**, el backend responde con un error `401 Unauthorized` exigiendo el desafío de re-autenticación:

```json
{
  "error_code": "STEP_UP_REQUIRED",
  "message": "La operación solicitada involucra cambios críticos en el Maestro de Vehículos. Se requiere re-autenticación MFA.",
  "step_up_challenge": {
    "auth_method": "TOTP_OR_PASSWORD",
    "challenge_session_id": "stepup-sess-998877665544"
  }
}
```
