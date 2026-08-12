# 06 — Regla de Seguridad: Prohibición Absoluta de Auto-Aprobación

---

## 1. Justificación de Control Interno (Segregación de Funciones - SoD)

En la gestión de compras corporativas, la **Segregación de Funciones (Segregation of Duties - SoD)** es un control interno crítico exigido por estándares de auditoría financiera (Sarbanes-Oxley / ISO 27001).

Permitir que un mismo individuo cree una Orden de Compra y posteriormente la apruebe genera un riesgo inaceptable de fraude, compras fantasma o desvío de fondos.

Por este motivo, la Fase 034 enforza la regla estricta:

$$\text{creator\_user\_id} \neq \text{approver\_user\_id}$$

---

## 2. Excepción de Dominio (`PurchaseOrderSelfApprovalDenied`)

Cuando se intenta aprobar una Orden de Compra donde el ID del usuario aprobador coincide con el ID del usuario creador de la orden, el sistema interrumpe inmediatamente la transacción lanzando la excepción de dominio:

```python
class PurchaseOrderSelfApprovalDenied(DomainException):
    def __init__(self, message: str = "Un usuario no puede aprobar su propia Orden de Compra"):
        super().__init__(
            code="PURCHASE_ORDER_SELF_APPROVAL_DENIED",
            message=message,
            status_code=403
        )
```

---

## 3. Lógica de Enforzamiento en Caso de Uso

```python
def validate_approval_eligibility(purchase_order: PurchaseOrder, current_user_id: UUID) -> None:
    # 1. Verificar prohibición de auto-aprobación
    if purchase_order.created_by_user_id == current_user_id:
        # Verificar si hay una excepción activa para entornos de prueba aislados
        allow_test_override = os.getenv("ALLOW_SELF_APPROVAL_IN_TEST", "false").lower() == "true"
        if not allow_test_override:
            raise PurchaseOrderSelfApprovalDenied(
                f"El usuario {current_user_id} creó la OC {purchase_order.code} y no puede aprobarla."
            )
```

---

## 4. Matriz de Permisos y Validación de Identidades

| Usuario Creador (`created_by_user_id`) | Usuario Aprobador (`approver_user_id`) | Entorno | Resultado de Operación |
| :--- | :--- | :--- | :--- |
| `usr_buyer_01` | `usr_buyer_01` | Producción / QA | ❌ **RECHAZADO** (`403 Forbidden` - `PurchaseOrderSelfApprovalDenied`) |
| `usr_buyer_01` | `usr_manager_02` | Producción / QA | ✅ **PERMITIDO** (Pasa validación SoD) |
| `usr_test_admin` | `usr_test_admin` | Test (con `ALLOW_SELF_APPROVAL_IN_TEST=true`) | ⚠️ **PERMITIDO EXCEPCIONALMENTE** (Únicamente en ejecuciones unitarias aisladas) |
