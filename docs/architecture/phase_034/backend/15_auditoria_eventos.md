# 15 — Catálogo de Eventos de Auditoría Inmutable (`logistics_audit_events`)

---

## 1. Estrategia de Auditoría Forense Append-Only

Cada cambio de estado o mutación relevante en el Agregado de Órdenes de Compra emite de forma sincrónica un evento de auditoría inmutable en el repositorio de auditoría centralizado `logistics_audit_events` (así como en el log local `po_purchase_order_audit_logs`).

Estos registros son estrictamente **append-only** (sólo inserción), garantizando que no se puedan modificar o eliminar del historial de auditoría ni siquiera por administradores de sistema.

---

## 2. Catálogo de los 6 Eventos de Auditoría de la Fase 034

| Nombre del Evento | Desencadenante Operativo | Datos Clave Registrados en Payload JSON |
| :--- | :--- | :--- |
| **`logistics.purchase_order.created_from_decision`** | Creación inicial de borrador de OC a partir de adjudicación CCO o borrador directo. | `purchase_order_id`, `code`, `cco_decision_id`, `supplier_id`, `created_by_user_id`, `grand_total` |
| **`logistics.purchase_order.submitted_for_approval`** | Solicitud formal de aprobación (`submit_for_approval`). | `purchase_order_id`, `code`, `revision_number`, `submitted_by_user_id`, `content_hash` |
| **`logistics.purchase_order.approved`** | Aprobación exitosa por parte del manager responsable. | `purchase_order_id`, `code`, `approver_user_id`, `step_up_factor` (`COMBINED_FACE_PAD`), `approval_notes` |
| **`logistics.purchase_order.rejected`** | Rechazo definitivo de la Orden de Compra. | `purchase_order_id`, `code`, `rejector_user_id`, `rejection_reason` |
| **`logistics.purchase_order.returned_for_changes`** | Devolución al solicitante para ajustes o corrección. | `purchase_order_id`, `code`, `actor_user_id`, `return_reason`, `requested_adjustments` |
| **`logistics.purchase_order.cancelled`** | Anulación / Cancelación inmutable de la OC. | `purchase_order_id`, `code`, `cancelled_by_user_id`, `cancellation_reason` |

---

## 3. Estructura Estándar del Payload de Evento

```json
{
  "event_id": "8a9b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
  "event_type": "logistics.purchase_order.approved",
  "aggregate_type": "PurchaseOrder",
  "aggregate_id": "e4f5a6b7-8c9d-0e1f-2a3b-4c5d6e7f8a9b",
  "occurred_at": "2026-07-31T00:45:00.123456Z",
  "actor": {
    "user_id": "8f7e6d5c-4b3a-2f1e-0d9c-8b7a6f5e4d3c",
    "email": "manager.logistica@empresa.com",
    "ip_address": "192.168.1.105",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
  },
  "security_context": {
    "step_up_verified": true,
    "step_up_factor": "COMBINED_FACE_PAD",
    "step_up_token_id": "tk_stepup_9988776655"
  },
  "data": {
    "purchase_order_code": "OC-LIM-2026-000042",
    "previous_status": "PENDING_APPROVAL",
    "new_status": "APPROVED",
    "revision_number": 1,
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "notes": "Aprobación conforme."
  }
}
```
