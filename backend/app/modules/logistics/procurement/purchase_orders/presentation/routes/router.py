"""Phase 034 — Purchase Orders FastAPI Router.

Defines REST endpoints under `/api/logistics/procurement/purchase-orders`.
Integrates with RBAC, Step-Up Security Policy, and Audit Event logging.
"""

from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.procurement.purchase_orders.application.dto.schemas import (
    PurchaseOrderApproveRequest,
    PurchaseOrderCancelRequest,
    PurchaseOrderDetailResponse,
    PurchaseOrderGenerateFromDecisionRequest,
    PurchaseOrderGenerationPlanRequest,
    PurchaseOrderGenerationPlanResponse,
    PurchaseOrderRejectRequest,
    PurchaseOrderReturnRequest,
    PurchaseOrderSubmitRequest,
    PurchaseOrderSummaryResponse,
)
from app.modules.logistics.procurement.purchase_orders.application.services.purchase_order_service import (
    PurchaseOrderService,
)
from app.modules.logistics.procurement.purchase_orders.domain.errors.exceptions import (
    PurchaseOrderDomainError,
)

router = APIRouter(
    prefix="/procurement/purchase-orders",
    tags=["Purchase Orders (Phase 034)"],
)


# Helper dependency to mock / get active user context
def get_current_user_context(request: Request) -> dict[str, Any]:
    """Extract user context from request state (set by authentication middleware)."""
    user = getattr(request.state, "user", None)
    if not user:
        # Fallback for dev / unauthenticated requests in test mode
        return {
            "id": UUID("00000000-0000-0000-0000-000000000001"),
            "organization_id": UUID("00000000-0000-0000-0000-000000000001"),
            "branch_id": UUID("00000000-0000-0000-0000-000000000001"),
        }
    return {
        "id": getattr(user, "id", UUID("00000000-0000-0000-0000-000000000001")),
        "organization_id": getattr(user, "organization_id", UUID("00000000-0000-0000-0000-000000000001")),
        "branch_id": getattr(user, "branch_id", UUID("00000000-0000-0000-0000-000000000001")),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/plan-generation",
    dependencies=[Depends(require_permission("logistics.purchase_orders.create"))],
    response_model=PurchaseOrderGenerationPlanResponse,
    summary="Preview PO creation plan from CCO decision",
)
def plan_po_generation(
    payload: PurchaseOrderGenerationPlanRequest,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Preview the purchase orders that will be created from a RECORDED decision."""
    service = PurchaseOrderService(db)
    # Fetch decision and candidates data from database or evaluations module
    # In presentation tier, data is loaded via decision_id
    # Note: decision_data mock/loader handled by service/evaluations integration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Plan generation endpoint requires live decision loader integration.",
    )


@router.get(
    "",
    dependencies=[Depends(require_permission("logistics.purchase_orders.read"))],
    response_model=List[PurchaseOrderSummaryResponse],
    summary="List purchase orders",
)
def list_purchase_orders(
    branch_id: Optional[UUID] = Query(None),
    supplier_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """List purchase orders for the active organization with filters and pagination."""
    service = PurchaseOrderService(db)
    orders, total = service.list_orders(
        organization_id=user_ctx["organization_id"],
        branch_id=branch_id,
        supplier_id=supplier_id,
        status=status,
        approval_status=approval_status,
        limit=limit,
        offset=offset,
    )
    return orders


@router.get(
    "/{po_id}",
    dependencies=[Depends(require_permission("logistics.purchase_orders.read"))],
    response_model=PurchaseOrderDetailResponse,
    summary="Get purchase order details",
)
def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Fetch full purchase order details including revisions and lines."""
    service = PurchaseOrderService(db)
    try:
        return service.get_order(po_id, user_ctx["organization_id"])
    except PurchaseOrderDomainError as err:
        raise HTTPException(status_code=err.http_status, detail=err.message)


@router.post(
    "/{po_id}/submit",
    dependencies=[Depends(require_permission("logistics.purchase_orders.update"))],
    response_model=PurchaseOrderDetailResponse,
    summary="Submit purchase order for approval",
)
def submit_purchase_order(
    po_id: UUID,
    payload: Optional[PurchaseOrderSubmitRequest] = None,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Submit a DRAFT purchase order for approval."""
    service = PurchaseOrderService(db)
    try:
        order = service.submit_for_approval(
            po_id=po_id,
            organization_id=user_ctx["organization_id"],
            submitter_user_id=user_ctx["id"],
        )
        db.commit()
        return order
    except PurchaseOrderDomainError as err:
        db.rollback()
        raise HTTPException(status_code=err.http_status, detail=err.message)


@router.post(
    "/{po_id}/approve",
    dependencies=[Depends(require_permission("logistics.purchase_orders.approve"))],
    response_model=PurchaseOrderDetailResponse,
    summary="Approve purchase order (Step-Up required)",
)
def approve_purchase_order(
    po_id: UUID,
    payload: Optional[PurchaseOrderApproveRequest] = None,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Approve a PENDING_APPROVAL purchase order.

    Requires Step-Up COMBINED_FACE_PAD. Creator cannot approve own PO.
    """
    service = PurchaseOrderService(db)
    allow_override = payload.allow_self_approval_override if payload else False
    reason = payload.reason if payload else None

    try:
        order = service.approve_order(
            po_id=po_id,
            organization_id=user_ctx["organization_id"],
            approver_user_id=user_ctx["id"],
            reason=reason,
            allow_self_approval_override=allow_override,
        )
        db.commit()
        return order
    except PurchaseOrderDomainError as err:
        db.rollback()
        raise HTTPException(status_code=err.http_status, detail=err.message)


@router.post(
    "/{po_id}/reject",
    dependencies=[Depends(require_permission("logistics.purchase_orders.approve"))],
    response_model=PurchaseOrderDetailResponse,
    summary="Reject purchase order",
)
def reject_purchase_order(
    po_id: UUID,
    payload: PurchaseOrderRejectRequest,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Reject a PENDING_APPROVAL purchase order. Reason at least 20 chars required."""
    service = PurchaseOrderService(db)
    try:
        order = service.reject_order(
            po_id=po_id,
            organization_id=user_ctx["organization_id"],
            approver_user_id=user_ctx["id"],
            reason=payload.reason,
        )
        db.commit()
        return order
    except PurchaseOrderDomainError as err:
        db.rollback()
        raise HTTPException(status_code=err.http_status, detail=err.message)


@router.post(
    "/{po_id}/return-for-changes",
    dependencies=[Depends(require_permission("logistics.purchase_orders.approve"))],
    response_model=PurchaseOrderDetailResponse,
    summary="Return purchase order for changes",
)
def return_purchase_order_for_changes(
    po_id: UUID,
    payload: PurchaseOrderReturnRequest,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Return a PENDING_APPROVAL purchase order for changes. Reason at least 20 chars required."""
    service = PurchaseOrderService(db)
    try:
        order = service.return_for_changes(
            po_id=po_id,
            organization_id=user_ctx["organization_id"],
            approver_user_id=user_ctx["id"],
            reason=payload.reason,
        )
        db.commit()
        return order
    except PurchaseOrderDomainError as err:
        db.rollback()
        raise HTTPException(status_code=err.http_status, detail=err.message)


@router.post(
    "/{po_id}/cancel",
    dependencies=[Depends(require_permission("logistics.purchase_orders.cancel"))],
    response_model=PurchaseOrderDetailResponse,
    summary="Cancel purchase order",
)
def cancel_purchase_order(
    po_id: UUID,
    payload: PurchaseOrderCancelRequest,
    db: Session = Depends(get_db),
    user_ctx: dict[str, Any] = Depends(get_current_user_context),
) -> Any:
    """Cancel an unissued purchase order."""
    service = PurchaseOrderService(db)
    try:
        order = service.cancel_order(
            po_id=po_id,
            organization_id=user_ctx["organization_id"],
            user_id=user_ctx["id"],
            cancellation_reason=payload.cancellation_reason,
        )
        db.commit()
        return order
    except PurchaseOrderDomainError as err:
        db.rollback()
        raise HTTPException(status_code=err.http_status, detail=err.message)
