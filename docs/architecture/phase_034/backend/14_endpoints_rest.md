# 14 — Especificación de Endpoints REST OpenAPI v3

---

## 1. Catálogo Resumido de Endpoints REST

Todos los endpoints están expuestos bajo la ruta base:
`/api/logistics/procurement/purchase-orders`

| Método HTTP | Ruta del Endpoint | Permiso RBAC | Descripción de la Operación |
| :-: | :--- | :--- | :--- |
| `POST` | `/plan-from-cco` | `logistics.purchase_orders.create` | Genera la vista previa del plan de agrupamiento de OCs desde una decisión CCO (`RECORDED`). |
| `POST` | `/generate` | `logistics.purchase_orders.create` | Crea formalmente una o más OCs en estado `DRAFT` basadas en el plan CCO o borrador directo. |
| `GET` | `/` | `logistics.purchase_orders.read` | Consulta paginada con filtros (estado, proveedor, rango de fechas, código). |
| `GET` | `/{id}` | `logistics.purchase_orders.read` | Obtiene el detalle completo de una OC, su revisión activa y snapshots inmutables. |
| `POST` | `/{id}/submit-for-approval` | `logistics.purchase_orders.submit` | Transicion el estado de `DRAFT` o `RETURNED_FOR_CHANGES` a `PENDING_APPROVAL`. |
| `POST` | `/{id}/approve` | `logistics.purchase_orders.approve` | **Aprueba la OC.** Requiere Step-Up Auth (`COMBINED_FACE_PAD`) y aplica anti-autoaprobación. |
| `POST` | `/{id}/reject` | `logistics.purchase_orders.reject` | Rechaza formalmente la solicitud de OC pasando a estado `REJECTED`. |
| `POST` | `/{id}/return-for-changes` | `logistics.purchase_orders.return` | Devuelve la OC al solicitante en estado `RETURNED_FOR_CHANGES` para ajustes. |
| `POST` | `/{id}/cancel` | `logistics.purchase_orders.cancel` | Anula una OC en estado borrador o devuelta pasando a `CANCELLED`. |

---

## 2. Especificación Detallada de Payload y Respuestas

### 2.1. `POST /api/logistics/procurement/purchase-orders/plan-from-cco`
**Payload de Entrada:**
```json
{
  "cco_decision_id": "c39a28b4-4b5c-4d89-8a1e-123456789abc"
}
```

**Respuesta Exitosa (`200 OK`):**
```json
{
  "status": "success",
  "data": {
    "cco_decision_id": "c39a28b4-4b5c-4d89-8a1e-123456789abc",
    "plans_count": 2,
    "plans": [
      {
        "supplier_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "supplier_name": "DISTRIBUIDORA INDUSTRIAL S.A.C.",
        "currency_code": "PEN",
        "lines_count": 3,
        "estimated_total": "12500.00"
      },
      {
        "supplier_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
        "supplier_name": "TECH SOLUTIONS CORP",
        "currency_code": "USD",
        "lines_count": 1,
        "estimated_total": "4500.00"
      }
    ],
    "blocking_issues": [],
    "is_valid": true
  }
}
```

---

### 2.2. `POST /api/logistics/procurement/purchase-orders/{id}/approve`
**Headers Requeridos:**
* `Authorization: Bearer <JWT_SESSION_TOKEN>`
* `X-Step-Up-Token: <JWT_STEP_UP_COMBINED_FACE_PAD>`

**Payload de Entrada:**
```json
{
  "approval_notes": "Aprobado tras verificar especificaciones técnicas y presupuesto asignado."
}
```

**Respuesta Exitosa (`200 OK`):**
```json
{
  "status": "success",
  "message": "Purchase Order approved successfully.",
  "data": {
    "id": "e4f5a6b7-8c9d-0e1f-2a3b-4c5d6e7f8a9b",
    "code": "OC-LIM-2026-000042",
    "status": "APPROVED",
    "approved_at": "2026-07-31T00:45:00Z",
    "approver_user_id": "8f7e6d5c-4b3a-2f1e-0d9c-8b7a6f5e4d3c",
    "step_up_factor_verified": "COMBINED_FACE_PAD"
  }
}
```

**Respuesta de Error de Auto-Aprobación (`403 Forbidden`):**
```json
{
  "code": "PURCHASE_ORDER_SELF_APPROVAL_DENIED",
  "message": "El usuario creador no puede aprobar su propia Orden de Compra.",
  "status_code": 403
}
```

**Respuesta de Error de Step-Up Faltante (`401 Unauthorized`):**
```json
{
  "code": "STEP_UP_AUTHENTICATION_REQUIRED",
  "message": "La aprobación de Órdenes de Compra requiere verificación facial biométrica activa.",
  "required_factor": "COMBINED_FACE_PAD",
  "status_code": 401
}
```
