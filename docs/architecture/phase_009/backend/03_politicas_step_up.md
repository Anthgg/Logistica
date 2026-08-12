# 03 — Políticas Step-Up por Permiso Sensible

## Mapeo de Permisos Sensibles

| Código de Permiso | Factores Requeridos | Nivel Riesgo Base | TTL Desafío | TTL Proof | One-Time | Fail Closed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `logistics.role_assignments.create` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.role_assignments.revoke` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.role_permissions.update` | `COMBINED_MULTIMODAL` | `CRITICAL` | 120s | 60s | Sí | Sí |
| `logistics.inventory.adjustments.create` | `FACE` | `MEDIUM` | 120s | 60s | Sí | Sí |
| `logistics.inventory.adjustments.approve` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.quarantine.release` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.dispatches.release` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.dispatches.cancel` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.documents.issue` | `FACE` | `MEDIUM` | 120s | 60s | Sí | Sí |
| `logistics.documents.reprint` | `FACE` | `MEDIUM` | 120s | 60s | Sí | Sí |
| `logistics.documents.cancel` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.documents.download_bulk` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.documents.export` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.vehicles.update` | `FACE` | `MEDIUM` | 120s | 60s | Sí | Sí |
| `logistics.trips.assign` | `FACE` | `MEDIUM` | 120s | 60s | Sí | Sí |
| `logistics.routes.override` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.deliveries.manual_close` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |
| `logistics.audit.read_sensitive` | `FACE`, `PAD` | `HIGH` | 120s | 60s | Sí | Sí |

## Fail Closed Policy
Si un servicio de inferencia biométrica no está disponible durante la evaluación de un permiso sensible con política `fail_closed = True`, la solicitud es rechazada inmediatamente con decisión `DENY` o `STEP_UP_REQUIRED` inejecutable sin permitir acceso libre.
