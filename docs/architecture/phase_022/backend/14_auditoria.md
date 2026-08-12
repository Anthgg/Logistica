# 14. Catálogo de Eventos de Auditoría Logística Inmutable

## Sistema de Auditoría Logística (`logistics_audit_events`)

Todas las acciones de creación, modificación, movimiento, rotación de seguridad y eliminación en el módulo de almacenes y ubicaciones registran eventos inmutables en la tabla `logistics_audit_events`. Estos eventos garantizan trazabilidad forense completa y cumplimiento normativo.

---

## Estructura de la Tabla `logistics_audit_events`

```sql
CREATE TABLE logistics_audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    warehouse_id UUID NULL REFERENCES warehouses(id),
    actor_user_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id UUID NOT NULL,
    payload_before JSONB NULL,
    payload_after JSONB NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logistics_org_event ON logistics_audit_events (organization_id, event_type, created_at);
```

---

## Catálogo de los 17 Eventos de Auditoría Inmutables

| # | Identificador del Evento (`event_type`) | Severidad | Descripción del Disparador Operativo |
| :---: | :--- | :---: | :--- |
| **01** | `LOGISTICS_WAREHOUSE_CREATED` | INFO | Creación de una nueva entidad Almacén. |
| **02** | `LOGISTICS_WAREHOUSE_UPDATED` | INFO | Modificación de propiedades o geolocalización de un almacén. |
| **03** | `LOGISTICS_WAREHOUSE_STATUS_CHANGED` | WARNING | Cambio de estado de almacén (`ACTIVE` $\rightarrow$ `MAINTENANCE` / `FULL`). |
| **04** | `LOGISTICS_LOCATION_CREATED` | INFO | Registro manual de una ubicación individual. |
| **05** | `LOGISTICS_LOCATION_UPDATED` | INFO | Actualización de nombre, banderas o atributos de ubicación. |
| **06** | `LOGISTICS_LOCATION_STATUS_CHANGED` | WARNING | Bloqueo o cambio a cuarentena (`ACTIVE` $\rightarrow$ `BLOCKED`). |
| **07** | `LOGISTICS_LOCATION_DELETED` | CRITICAL | Eliminación física de un nodo de ubicación sin stock. |
| **08** | `LOGISTICS_LOCATION_BULK_GENERATED` | INFO | Ejecución combinatoria masiva de ubicaciones. |
| **09** | `LOGISTICS_LOCATION_SUBTREE_MOVED` | CRITICAL | Reubicación topológica de un subárbol con recálculo de rutas. |
| **10** | `LOGISTICS_LOCATION_CAPACITY_SET` | INFO | Configuración o edición de capacidades físicas en una ubicación. |
| **11** | `LOGISTICS_LOCATION_RESTRICTION_ADDED` | WARNING | Registro de restricción ambiental (COLD_CHAIN, HAZMAT). |
| **12** | `LOGISTICS_LOCATION_RESTRICTION_REMOVED` | WARNING | Eliminación de una restricción normativa de ubicación. |
| **13** | `LOGISTICS_LAYOUT_VERSION_CREATED` | INFO | Guardado de un nuevo borrador de plano 2D. |
| **14** | `LOGISTICS_LAYOUT_VERSION_ACTIVATED` | CRITICAL | Activación formal de plano 2D para visualización en producción. |
| **15** | `LOGISTICS_LOCATION_QR_RESOLVED` | INFO | Decodificación y resolución exitosa de un payload QR opaco. |
| **16** | `LOGISTICS_LOCATION_QR_ROTATED` | CRITICAL | Rotación de `public_ref` por invalidez o seguridad de etiqueta. |
| **17** | `LOGISTICS_LOCATION_LABELS_EXPORTED` | INFO | Generación y exportación de archivo de etiquetas PDF para impresión. |

---

## Formato del Payload Registrado (Ejemplo: Movimiento)

```json
{
  "event_id": "7a8b9c0d-1111-2222-3333-444455556666",
  "event_type": "LOGISTICS_LOCATION_SUBTREE_MOVED",
  "actor_user_id": "f1e2d3c4-5555-6666-7777-888899990000",
  "resource_id": "c3a9d2e1-4567-89ab-cdef-0123456789ab",
  "payload_before": {
    "parent_id": "parent-old-uuid",
    "full_code": "ALM01-Z01-A01-R01",
    "hierarchy_path": "/root/old_parent/c3a9d2e1"
  },
  "payload_after": {
    "parent_id": "parent-new-uuid",
    "full_code": "ALM01-Z02-A01-R01",
    "hierarchy_path": "/root/new_parent/c3a9d2e1",
    "descendants_affected_count": 48
  },
  "created_at": "2026-07-28T12:05:00Z"
}
```
