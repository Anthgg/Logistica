"""Typed exceptions for Purchase Requisitions domain (Phase 031)."""

from __future__ import annotations

from fastapi import HTTPException, status


class PurchaseRequisitionNotFound(HTTPException):
    def __init__(self, requisition_id: object) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PURCHASE_REQUISITION_NOT_FOUND", "requisition_id": str(requisition_id)},
        )


class PurchaseRequisitionNotEditable(HTTPException):
    def __init__(self, current_status: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_NOT_EDITABLE", "current_status": current_status},
        )


class PurchaseRequisitionAlreadySubmitted(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_ALREADY_SUBMITTED"},
        )


class PurchaseRequisitionAlreadyDecided(HTTPException):
    def __init__(self, decision_type: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_ALREADY_DECIDED", "decision_type": decision_type},
        )


class PurchaseRequisitionStatusInvalid(HTTPException):
    def __init__(self, current_status: str, required_status: str | list) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PURCHASE_REQUISITION_STATUS_INVALID",
                "current_status": current_status,
                "required_status": required_status if isinstance(required_status, list) else [required_status],
            },
        )


class PurchaseRequisitionCannotBeApproved(HTTPException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_CANNOT_BE_APPROVED", "reason": reason},
        )


class PurchaseRequisitionCannotBeRejected(HTTPException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_CANNOT_BE_REJECTED", "reason": reason},
        )


class PurchaseRequisitionCannotBeWithdrawn(HTTPException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_CANNOT_BE_WITHDRAWN", "reason": reason},
        )


class PurchaseRequisitionCannotBeCancelled(HTTPException):
    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_CANNOT_BE_CANCELLED", "reason": reason},
        )


class PurchaseRequisitionSelfApprovalDenied(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PURCHASE_REQUISITION_SELF_APPROVAL_DENIED",
                "message": "El creador de la solicitud no puede aprobarla (política SINGLE_STEP_BASIC).",
            },
        )


class PurchaseRequisitionRevisionConflict(HTTPException):
    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PURCHASE_REQUISITION_REVISION_CONFLICT",
                "expected_row_version": expected,
                "actual_row_version": actual,
            },
        )


class PurchaseRequisitionValidationFailed(HTTPException):
    def __init__(self, errors: list, blocking_issues: list | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PURCHASE_REQUISITION_VALIDATION_FAILED",
                "errors": errors,
                "blocking_issues": blocking_issues or errors,
            },
        )


class PurchaseRequisitionDuplicateSuspected(HTTPException):
    def __init__(self, candidates: list) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PURCHASE_REQUISITION_DUPLICATE_SUSPECTED",
                "candidates": candidates,
                "message": "Se detectaron posibles solicitudes duplicadas. Incluya justificación para continuar.",
            },
        )


class PurchaseRequisitionCodeConflict(HTTPException):
    def __init__(self, code: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_CODE_CONFLICT", "requisition_code": code},
        )


class PurchaseRequisitionLineNotFound(HTTPException):
    def __init__(self, line_id: object) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PURCHASE_REQUISITION_LINE_NOT_FOUND", "line_id": str(line_id)},
        )


class PurchaseRequisitionLineInvalid(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PURCHASE_REQUISITION_LINE_INVALID", "message": message},
        )


class PurchaseRequisitionQuantityInvalid(HTTPException):
    def __init__(self, value: str, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PURCHASE_REQUISITION_QUANTITY_INVALID", "value": value, "reason": reason},
        )


class PurchaseRequisitionUnitInvalid(HTTPException):
    def __init__(self, unit_id: object) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PURCHASE_REQUISITION_UNIT_INVALID", "unit_id": str(unit_id)},
        )


class PurchaseRequisitionConversionMissing(HTTPException):
    def __init__(self, from_unit: str, to_unit: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PURCHASE_REQUISITION_CONVERSION_MISSING",
                "from_unit": from_unit,
                "to_unit": to_unit,
                "message": f"No existe regla de conversión activa de '{from_unit}' a '{to_unit}'.",
            },
        )


class PurchaseRequisitionProductInactive(HTTPException):
    def __init__(self, product_id: object) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PURCHASE_REQUISITION_PRODUCT_INACTIVE", "product_id": str(product_id)},
        )


class CostCenterNotFound(HTTPException):
    def __init__(self, cost_center_id: object) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COST_CENTER_NOT_FOUND", "cost_center_id": str(cost_center_id)},
        )


class CostCenterInactive(HTTPException):
    def __init__(self, cost_center_id: object, current_status: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "COST_CENTER_INACTIVE",
                "cost_center_id": str(cost_center_id),
                "current_status": current_status,
            },
        )


class DestinationWarehouseInvalid(HTTPException):
    def __init__(self, warehouse_id: object, reason: str = "not found or inactive") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "DESTINATION_WAREHOUSE_INVALID",
                "warehouse_id": str(warehouse_id),
                "reason": reason,
            },
        )
