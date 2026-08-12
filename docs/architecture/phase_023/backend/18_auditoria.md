# 18 — Auditoría de Eventos Inmutables (`logistics_audit_events`)

## 1. Mecanismo General de Auditoría Logística

Toda modificación, creación, cambio de estado, renombre de SKU o evaluación de compatibilidad en la **Fase 023** genera un evento inmutable registrado de forma síncrona/asíncrona en la tabla global de auditoría **`logistics_audit_events`** (desarrollada en la arquitectura base).

---

## 2. Catálogo Oficial de Eventos de la Fase 023

| Código del Evento (`event_type`) | Nivel de Severidad | Descripción del Disparador | Payload JSON Registrado |
| :--- | :--- | :--- | :--- |
| `PRODUCT_CREATED` | INFO | Se crea un producto nuevo en estado `DRAFT` o `ACTIVE`. | SKU, Nombre, CategoriaID, Creador. |
| `PRODUCT_UPDATED` | INFO | Se actualizan datos generales o perfil físico. | Atributos modificados (Before/After). |
| `PRODUCT_STATUS_CHANGED` | WARNING | Se cambia el estado operativo (`ACTIVE` -> `SUSPENDED`). | Estado anterior, estado nuevo, motivo. |
| `PRODUCT_SKU_RENAMED` | WARNING | Se renombra un SKU activo y se genera un alias. | `old_sku`, `new_sku`, `reason`, `alias_id`. |
| `PRODUCT_VERSION_SNAPSHOT_CREATED` | INFO | Se genera un snapshot inmutable SHA-256. | `version_number`, `content_hash`. |
| `PRODUCT_IDENTIFIER_ADDED` | INFO | Se asigna un nuevo código EAN/UPC o interno. | `identifier_type`, `normalized_value`. |
| `PRODUCT_IDENTIFIER_REMOVED` | WARNING | Se elimina un código de barras del producto. | `identifier_type`, `normalized_value`. |
| `PRODUCT_CATEGORY_CREATED` | INFO | Se crea una nueva categoría en la jerarquía. | `code`, `hierarchy_path`, `depth`. |
| `PRODUCT_BRAND_CREATED` | INFO | Se registra una nueva marca comercial. | `name`, `normalized_name`. |
| `PRODUCT_LOCATION_COMPATIBILITY_CHECKED` | INFO | Se evalúa compatibilidad cualitativa con ubicación. | `location_id`, `is_compatible`, `reasons`. |
| `PRODUCT_ARCHIVED` | CRITICAL | El producto pasa al estado `ARCHIVED`. | `product_id`, `user_id`, motivo. |

---

## 3. Estructura del Registro en `logistics_audit_events`

```json
{
  "id": "f1e2d3c4-b5a6-9788-1122-334455667788",
  "organization_id": "e8c7b6a5-4321-9876-bcda-123456789012",
  "event_type": "PRODUCT_SKU_RENAMED",
  "aggregate_type": "PRODUCT",
  "aggregate_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "actor_user_id": "99001122-3344-5566-7788-99aabbccddeeff",
  "client_ip": "192.168.1.45",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "payload": {
    "product_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "old_sku": "SKU-MONITOR-V1",
    "new_sku": "SKU-MONITOR-PRO-V2",
    "alias_created": "SKU-MONITOR-V1",
    "reason": "Rebranding comercial por actualización de hardware",
    "step_up_authenticated": true
  },
  "created_at": "2026-07-28T12:10:00.123456Z"
}
```

---

## 4. Servicio de Emisión de Auditoría (`LogisticsAuditLogger`)

```python
import json
from datetime import datetime
from app.db.base_class import Base

class LogisticsAuditLogger:

    @classmethod
    def log_event(
        cls,
        db_session,
        org_id: uuid.UUID,
        event_type: str,
        aggregate_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        payload: dict,
        client_ip: str | None = None
    ):
        """
        Persiste un evento de auditoría de manera inmutable en logistics_audit_events.
        """
        audit_entry = LogisticsAuditEventModel(
            organization_id=org_id,
            event_type=event_type,
            aggregate_type="PRODUCT",
            aggregate_id=aggregate_id,
            actor_user_id=actor_user_id,
            client_ip=client_ip,
            payload=payload,
            created_at=datetime.utcnow()
        )
        db_session.add(audit_entry)
        # Se garantiza que el log forma parte de la misma transacción atómica que la entidad modicada
```

---

## 5. Garantía de Inmutabilidad de Logs

1. **Sin Endpoints de Edición o Eliminación:** No existe ninguna ruta en la API para modificar (`PUT`/`PATCH`) o borrar (`DELETE`) registros de `logistics_audit_events`.
2. **Restricción de Permisos DB:** El usuario SQL asignado a la aplicación en producción posee únicamente privilegios de `INSERT` y `SELECT` sobre la tabla de auditoría, impidiendo cualquier operación de `UPDATE` o `TRUNCATE`.
