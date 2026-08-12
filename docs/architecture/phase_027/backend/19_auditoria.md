# Catálogo de Eventos de Auditoría Inmutable

## 1. Integración con `logistics_audit_events`

Todas las mutaciones críticas dentro de la Fase 027 se registran de forma asíncrona pero transaccionalmente consistente en la tabla central de auditoría inmutable (`logistics_audit_events`) establecida en la **Fase 001/002**.

Cada registro almacena el `organization_id`, `user_id`, dirección IP, agente de usuario, evento específico, ID de la entidad afectada y un snapshot con los datos anteriores y posteriores a la mutación (`before_state`, `after_state`).

---

## 2. Catálogo de los 13 Eventos Inmutables de la Fase 027

| # | Código del Evento | Desencadenante | Payload Clave |
|---|---|---|---|
| 01 | `VEHICLE_CREATED` | Creación de un nuevo vehículo en borrador o activo. | `vehicle_code`, `display_plate`, `vin` |
| 02 | `VEHICLE_UPDATED` | Modificación de atributos generales o tipología. | `changed_fields`, `before_state`, `after_state` |
| 03 | `VEHICLE_PLATE_CHANGED` | Reasignación formal de placa de rodaje. | `previous_plate`, `new_plate`, `reason` |
| 04 | `VEHICLE_CAPACITY_UPDATED` | Alta o cambio en tara, carga útil o volumen. | `tare_weight`, `max_payload_weight`, `max_volume` |
| 05 | `VEHICLE_DIMENSIONS_UPDATED`| Alta o cambio en cotas exteriores o compartimento. | `overall_length`, `cargo_length`, `calculated_volume` |
| 06 | `VEHICLE_OWNERSHIP_ASSIGNED` | Asignación de tipo de propiedad o leasing. | `ownership_type`, `owner_partner_id` |
| 07 | `VEHICLE_CARRIER_ASSIGNED` | Asignación de transportista autorizado (Fase 025).| `carrier_partner_id`, `assignment_start_date` |
| 08 | `VEHICLE_DOCUMENT_ATTACHED` | Carga de nuevo documento (SOAT, CITV). | `document_type`, `document_number`, `expiration_date` |
| 09 | `VEHICLE_DOCUMENT_EXPIRED` | Detección automática de caducidad por cron/resolver. | `document_type`, `expired_date` |
| 10 | `VEHICLE_RESTRICTION_APPLIED`| Imposición manual de bloqueo o maintenance. | `restriction_type`, `reason`, `severity` |
| 11 | `VEHICLE_RESTRICTION_RESOLVED`| Levantamiento y des-bloqueo auditado. | `restriction_id`, `resolution_notes` |
| 12 | `VEHICLE_STATUS_CHANGED` | Transición en `operational_status` o `compliance`. | `previous_status`, `new_status` |
| 13 | `VEHICLE_VERSION_SNAPSHOT_CREATED`| Generación del snapshot inmutable SHA-256. | `version_number`, `content_hash` |

---

## 3. Ejemplo de Payload de Auditoría en `logistics_audit_events`

```json
{
  "event_id": "c7112233-4455-6677-8899-aabbccddeeff",
  "event_type": "VEHICLE_PLATE_CHANGED",
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "11223344-5566-7788-9900-aabbccddeeff",
  "entity_name": "logistics_vehicles",
  "entity_id": "e4a3b2c1-0011-2233-4455-66778899aabb",
  "created_at": "2026-07-28T21:55:00.123456Z",
  "ip_address": "190.235.12.44",
  "metadata": {
    "previous_plate": "ABC-123",
    "new_plate": "F3X-992",
    "reason": "Re-matriculación SUNARP",
    "step_up_authenticated": true,
    "sha256_snapshot_version": 2
  }
}
```
