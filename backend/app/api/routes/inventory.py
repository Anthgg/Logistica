from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import INVENTORY_WRITE_ROLES, LOGISTICS_READ_ROLES
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    InventoryMovementCreate,
    InventoryMovementRead,
    MovementType,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])
service = InventoryService()


@router.get("", response_model=PaginatedResponse[InventoryItemRead], summary="Listar inventario")
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("name"),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    warehouse_id: UUID | None = None,
    is_active: bool | None = None,
    low_stock: bool | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[InventoryItemRead]:
    return service.list_items(
        database,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        warehouse_id=warehouse_id,
        is_active=is_active,
        low_stock=low_stock,
    )


@router.get(
    "/movements",
    response_model=PaginatedResponse[InventoryMovementRead],
    summary="Listar movimientos de inventario",
)
def list_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    item_id: UUID | None = None,
    movement_type: MovementType | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[InventoryMovementRead]:
    return service.list_movements(
        database,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        item_id=item_id,
        movement_type=movement_type,
    )


@router.get("/{item_id}", response_model=InventoryItemRead, summary="Consultar artículo")
def get_inventory_item(
    item_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> InventoryItemRead:
    return InventoryItemRead.model_validate(service.get_item(database, item_id))


@router.post(
    "",
    response_model=InventoryItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear artículo de inventario",
    dependencies=[Depends(verify_csrf)],
)
def create_inventory_item(
    data: InventoryItemCreate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*INVENTORY_WRITE_ROLES)),
) -> InventoryItemRead:
    return InventoryItemRead.model_validate(service.create_item(database, data))


@router.patch(
    "/{item_id}",
    response_model=InventoryItemRead,
    summary="Actualizar artículo de inventario",
    dependencies=[Depends(verify_csrf)],
)
def update_inventory_item(
    item_id: UUID,
    data: InventoryItemUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*INVENTORY_WRITE_ROLES)),
) -> InventoryItemRead:
    return InventoryItemRead.model_validate(service.update_item(database, item_id, data))


@router.post(
    "/movements",
    response_model=InventoryMovementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar movimiento atómico de inventario",
    dependencies=[Depends(verify_csrf)],
)
def create_inventory_movement(
    data: InventoryMovementCreate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*INVENTORY_WRITE_ROLES)),
) -> InventoryMovementRead:
    return InventoryMovementRead.model_validate(
        service.create_movement(database, data, user)
    )
