# 18. Registro de Eventos de Auditoría Inmutable (`logistics_audit_events`)

## 1. Integración con el Sistema Global de Auditoría

Toda modificación estructural sobre el catálogo de unidades, reglas de conversión o empaques de producto genera un registro inmutable append-only en la tabla central de auditoría del sistema: `logistics_audit_events`.

---

## 2. Catálogo de Eventos de Auditoría de la Fase 024

| Nombre del Evento | Desencadenante Operativo | Payload de Auditoría (`payload_json`) |
| :--- | :--- | :--- |
| `LOGISTICS_UOM_UNIT_CREATED` | Alta de nueva UOM personalizada. | `unit_id`, `code`, `scope`, `dimension_code`, `kind` |
| `LOGISTICS_UOM_UNIT_DEACTIVATED` | Desactivación lógica de una UOM. | `unit_id`, `code`, `reason`, `deactivated_by` |
| `LOGISTICS_UOM_CONVERSION_RULE_CREATED` | Alta de regla de conversión física. | `rule_id`, `from_unit`, `to_unit`, `conversion_factor` |
| `LOGISTICS_UOM_CONVERSION_RULE_DEPRECATED` | Invalidación o cierre de regla. | `rule_id`, `from_unit`, `to_unit`, `effective_to` |
| `LOGISTICS_UOM_PRODUCT_CONFIG_UPDATED` | Reconfiguración de 5 unidades de producto. | `product_id`, `old_storage_unit`, `new_storage_unit` |
| `LOGISTICS_UOM_PACKAGING_DEFINED` | Alta o modificación de nivel de empaque. | `product_id`, `packaging_unit`, `contained_qty` |

---

## 3. Ejemplo de Payload Registrado

### Evento: `LOGISTICS_UOM_PACKAGING_DEFINED`

```json
{
  "event_id": "c71a3d90-0000-4000-8000-000000000099",
  "event_type": "LOGISTICS_UOM_PACKAGING_DEFINED",
  "organization_id": "11111111-1111-1111-1111-111111111111",
  "actor_user_id": "a855f700-0000-4000-8000-000000000005",
  "actor_ip_address": "192.168.1.45",
  "timestamp": "2026-07-28T12:30:00.123456Z",
  "resource_type": "product_packaging_definitions",
  "resource_id": "8f3b2a11-0000-4000-8000-000000000001",
  "step_up_authenticated": true,
  "payload_json": {
    "product_id": "8f3b2a11-0000-4000-8000-000000000001",
    "packaging_unit_code": "PALLET",
    "contained_quantity": "40.000000000000000000",
    "contained_unit_code": "CAJA",
    "hierarchy_level": 3,
    "barcode_identifier": "17791234567890"
  }
}
```
