# Modelo de Verificaciones, Resultados y Trazabilidad Granular

## 1. Descripción General

El núcleo del subsistema de verificaciones se compone de tres entidades relacionales jerárquicas:
1. `VehicleVerificationModel`: Registra la intención, ejecución, estado global y metadata del proceso de verificación para un vehículo específico.
2. `VehicleVerificationResultModel`: Almacena el resultado consolidado entregado por la fuente, conservando el payload crudo (`raw_payload`) y la firma criptográfica **SHA-256** del payload original.
3. `VehicleVerificationFieldProvenanceModel`: Brinda trazabilidad a nivel de campo individual (`field_name`), registrando el valor original extraído de la fuente, su equivalente normalizado, el score de confianza y el estado de coincidencia contra el registro base del ERP.

---

## 2. Diagrama Entidad-Relación de Resultados y Trazabilidad

```mermaid
erDiagram
    logistics_vehicles ||--o{ logistics_vehicle_verifications : "se verifica"
    logistics_vehicle_verification_sources ||--o{ logistics_vehicle_verifications : "provee datos"
    logistics_vehicle_verifications ||--o1 logistics_vehicle_verification_results : "obtiene"
    logistics_vehicle_verification_results ||--o{ logistics_vehicle_verification_field_provenance : "desglosa campos"

    logistics_vehicle_verifications {
        uuid id PK
        uuid vehicle_id FK
        uuid source_id FK
        string verification_number UK
        string plate_number
        string status
        datetime verification_date
        datetime expiration_date
        uuid requested_by FK
        datetime created_at
    }

    logistics_vehicle_verification_results {
        uuid id PK
        uuid verification_id FK
        string outcome_status
        jsonb raw_payload
        string payload_sha256
        decimal overall_confidence_score
        integer execution_time_ms
        datetime created_at
    }

    logistics_vehicle_verification_field_provenance {
        uuid id PK
        uuid result_id FK
        string field_name
        string raw_source_value
        string normalized_value
        string erp_current_value
        boolean is_matching
        decimal field_confidence_score
        datetime created_at
    }
```

---

## 3. Especificación de Tablas ORM

### 3.1. `VehicleVerificationModel` (`logistics_vehicle_verifications`)

| Campo | Tipo | Nulo | Descripción / Reglas |
|---|---|---|---|
| `id` | `UUID` | No | Clave Primaria (UUIDv4) |
| `vehicle_id` | `UUID` | No | FK a `logistics_vehicles.id` de Fase 027 (ON DELETE RESTRICT) |
| `source_id` | `UUID` | No | FK a `logistics_vehicle_verification_sources.id` (ON DELETE RESTRICT) |
| `verification_number` | `VARCHAR(60)` | No | Código único de verificación (ej. `VER-20260728-98124`) |
| `plate_number` | `VARCHAR(15)` | No | Placa consultada en formato normalizado (ej. `ABC-123` o `A1B-890`) |
| `status` | `VARCHAR(30)` | No | Estado del proceso: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `verification_date` | `TIMESTAMPTZ` | No | Fecha y hora en que se ejecutó la consulta ante la fuente |
| `expiration_date` | `TIMESTAMPTZ` | Sí | Fecha de expiración de los datos verificados calculada según la política de frescura |
| `requested_by` | `UUID` | No | FK al usuario del ERP que inició el requerimiento |
| `created_at` | `TIMESTAMPTZ` | No | Timestamp de auditoría de creación |

#### Claves Únicas e Índices B-Tree
* `uq_vehicle_verifications_number`: UNIQUE(`verification_number`)
* `idx_vv_vehicle_status`: INDEX(`vehicle_id`, `status`)
* `idx_vv_plate_search`: INDEX(`plate_number`, `verification_date`)

---

### 3.2. `VehicleVerificationResultModel` (`logistics_vehicle_verification_results`)

| Campo | Tipo | Nulo | Descripción / Reglas |
|---|---|---|---|
| `id` | `UUID` | No | Clave Primaria (UUIDv4) |
| `verification_id` | `UUID` | No | FK a `logistics_vehicle_verifications.id` (ON DELETE CASCADE) — Relación 1 a 1 |
| `outcome_status` | `VARCHAR(30)` | No | Resultado de la validación: `VERIFIED_MATCH`, `VERIFIED_WITH_DISCREPANCIES`, `NOT_FOUND`, `REJECTED`, `ERROR` |
| `raw_payload` | `JSONB` | No | Respuesta cruda en formato JSON obtenida desde el proveedor o formulario asistido |
| `payload_sha256` | `CHAR(64)` | No | Hash SHA-256 hex del `raw_payload` canonicalizado para garantizar inmutabilidad |
| `overall_confidence_score` | `NUMERIC(3,2)` | No | Score de confianza global ponderado del resultado (`0.00` a `1.00`) |
| `execution_time_ms` | `INTEGER` | No | Tiempo de latencia de la consulta en milisegundos |
| `created_at` | `TIMESTAMPTZ` | No | Fecha de registro |

#### Claves Únicas e Índices
* `uq_vv_results_verification_id`: UNIQUE(`verification_id`)
* `idx_vv_results_sha256`: INDEX(`payload_sha256`)

---

### 3.3. `VehicleVerificationFieldProvenanceModel` (`logistics_vehicle_verification_field_provenance`)

| Campo | Tipo | Nulo | Descripción / Reglas |
|---|---|---|---|
| `id` | `UUID` | No | Clave Primaria (UUIDv4) |
| `result_id` | `UUID` | No | FK a `logistics_vehicle_verification_results.id` (ON DELETE CASCADE) |
| `field_name` | `VARCHAR(60)` | No | Nombre estándar del campo verificado (ej. `vin`, `engine_number`, `owner_document`, `manufacturing_year`, `soat_status`) |
| `raw_source_value` | `TEXT` | Sí | Valor textual tal como fue devuelto por la fuente externa |
| `normalized_value` | `TEXT` | Sí | Valor limpio y estandarizado por el servicio `VehicleVerificationNormalizer` |
| `erp_current_value` | `TEXT` | Sí | Valor actual almacenado en el Maestro de Vehículos (Fase 027) al momento de la verificación |
| `is_matching` | `BOOLEAN` | No | `True` si `normalized_value == erp_current_value` |
| `field_confidence_score` | `NUMERIC(3,2)` | No | Confianza atribuida al campo en particular |
| `created_at` | `TIMESTAMPTZ` | No | Fecha de registro |

#### Claves e Índices
* `fk_vv_field_provenance_result_id`: Foreign Key a `logistics_vehicle_verification_results(id)`
* `idx_vv_field_provenance_matching`: INDEX(`result_id`, `field_name`, `is_matching`)

---

## 4. Algoritmo de Firmado y Canonicalización de Raw Payload (SHA-256)

Para evitar la alteración retroactiva de los payloads almacenados en la base de datos, el sistema genera la firma SHA-256 aplicando el siguiente procedimiento:

```python
import json
import hashlib

def calculate_payload_sha256(raw_payload: dict) -> str:
    """
    Serializa el diccionario JSON ordenando sus llaves para asegurar 
    determinismo de representación y calcula el hash SHA-256.
    """
    canonical_json = json.dumps(raw_payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
```
