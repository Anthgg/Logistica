# Catálogo de Eventos Inmutables de Auditoría (`logistics_audit_events`)

## 1. Descripción General

Todas las operaciones ejecutadas en el subsistema de verificaciones vehiculares generan registros inmutables de auditoría en la tabla global `logistics_audit_events`.

Estos eventos capturan el usuario responsable, dirección IP, timestamp UTC, entidad afectada, payload antes/después y firmas SHA-256 de las respuestas o archivos involucrados, garantizando trazabilidad no repudiable.

---

## 2. Catálogo de los 9 Eventos de Auditoría de la Fase 028

| Código del Evento (`event_type`) | Nivel / Severidad | Descripción del Disparador | Payload Principal Registrado |
|---|---|---|---|
| `LOGISTICS_VEHICLE_VERIFICATION_REQUESTED` | `INFO` | Se solicita una nueva verificación para una placa ante una fuente externa | `verification_id`, `plate_number`, `source_code`, `requested_by` |
| `LOGISTICS_VEHICLE_VERIFICATION_COMPLETED` | `INFO` | La fuente devuelve el resultado exitosamente y se firma el payload | `verification_id`, `outcome_status`, `payload_sha256`, `execution_time_ms` |
| `LOGISTICS_VEHICLE_VERIFICATION_FAILED` | `WARNING` | La consulta ante la fuente falla por timeout, red o error HTTP | `verification_id`, `source_code`, `status_code`, `error_message` |
| `LOGISTICS_ASSISTED_VERIFICATION_CREATED` | `INFO` | Se registra una verificación asistida manual con evidencias adjuntas | `assisted_verification_id`, `masked_owner_name`, `evidences_count` |
| `LOGISTICS_ASSISTED_VERIFICATION_APPROVED` | `IMPORTANT` | Un supervisor aprueba la verificación asistida (Segregación de Funciones) | `assisted_verification_id`, `approved_by`, `created_by` |
| `LOGISTICS_ASSISTED_VERIFICATION_REJECTED` | `WARNING` | Un supervisor rechaza la verificación asistida manual | `assisted_verification_id`, `rejected_by`, `rejection_reason` |
| `LOGISTICS_VERIFICATION_CONFLICT_DETECTED` | `WARNING` / `CRITICAL` | El detector identifica una discrepancia de datos entre ERP y fuente | `conflict_id`, `field_name`, `severity`, `erp_value`, `verified_value` |
| `LOGISTICS_VERIFICATION_CONFLICT_RESOLVED` | `IMPORTANT` | Un oficial de compliance resuelve o dispensa un conflicto de verificación | `conflict_id`, `action`, `resolution_comment`, `resolved_by` |
| `LOGISTICS_VERIFICATION_APPLIED_TO_VEHICLE` | `CRITICAL` | Se aplican los datos verificados al vehículo y se genera `VehicleVersionModel` | `verification_id`, `vehicle_id`, `version_number`, `version_hash` |

---

## 3. Ejemplo Estructurado de Evento de Auditoría JSON

```json
{
  "audit_event_id": "e8877665-4433-2211-00aa-bbccddeeff00",
  "event_type": "LOGISTICS_VERIFICATION_APPLIED_TO_VEHICLE",
  "aggregate_type": "VehicleModel",
  "aggregate_id": "c1f7b880-99aa-44bb-88cc-112233445566",
  "actor": {
    "user_id": "user-uuid-3333",
    "username": "compliance.officer",
    "ip_address": "192.168.1.45",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  },
  "timestamp": "2026-07-28T22:15:30.123456Z",
  "payload": {
    "verification_id": "a90184b2-3344-5566-7788-9900aabbccdd",
    "verification_number": "VER-20260728-98124",
    "plate_number": "ABC-123",
    "applied_fields": [
      "vin",
      "engine_number",
      "manufacturing_year"
    ],
    "previous_values": {
      "vin": "1HGCR2F83HA000000",
      "engine_number": "ENG-OLD-111",
      "manufacturing_year": 2021
    },
    "new_values": {
      "vin": "1HGCR2F83HA001234",
      "engine_number": "ENG-982104",
      "manufacturing_year": 2022
    },
    "version_snapshot": {
      "version_number": 4,
      "version_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
    }
  }
}
```
