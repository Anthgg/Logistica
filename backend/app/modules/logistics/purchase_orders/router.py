"""FastAPI routes for purchase orders."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.purchase_orders.schemas import (
    PurchaseOrderCancel,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from app.modules.logistics.purchase_orders.service import PurchaseOrderService


router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get("", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    order_status: str | None = Query(default=None, alias="status"),
    supplier_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.read")
    ),
):
    return PurchaseOrderService(db).list(
        resolve_organization_id(principal),
        order_status=order_status,
        supplier_id=supplier_id,
    )


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.create")
    ),
):
    return PurchaseOrderService(db).create(
        resolve_organization_id(principal),
        payload,
        principal.user_id,
    )


@router.get("/{purchase_order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    purchase_order_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.read")
    ),
):
    return PurchaseOrderService(db).get(
        purchase_order_id,
        resolve_organization_id(principal),
    )


@router.patch("/{purchase_order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    purchase_order_id: UUID,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.update")
    ),
):
    return PurchaseOrderService(db).update(
        purchase_order_id,
        resolve_organization_id(principal),
        payload,
        principal.user_id,
    )


@router.post("/{purchase_order_id}/approve", response_model=PurchaseOrderResponse)
def approve_purchase_order(
    purchase_order_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.approve")
    ),
):
    return PurchaseOrderService(db).approve(
        purchase_order_id,
        resolve_organization_id(principal),
        principal.user_id,
    )


@router.post("/{purchase_order_id}/issue", response_model=PurchaseOrderResponse)
def issue_purchase_order(
    purchase_order_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.issue")
    ),
):
    return PurchaseOrderService(db).issue(
        purchase_order_id,
        resolve_organization_id(principal),
        principal.user_id,
    )


@router.post("/{purchase_order_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_purchase_order(
    purchase_order_id: UUID,
    payload: PurchaseOrderCancel,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.purchase_orders.cancel")
    ),
):
    return PurchaseOrderService(db).cancel(
        purchase_order_id,
        resolve_organization_id(principal),
        payload.reason,
        principal.user_id,
    )
