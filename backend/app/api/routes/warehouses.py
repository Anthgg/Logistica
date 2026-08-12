from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import LOGISTICS_READ_ROLES, WAREHOUSE_WRITE_ROLES
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.i18n import translate
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])
service = WarehouseService()


@router.get("", response_model=PaginatedResponse[WarehouseRead], summary="Listar almacenes")
def list_warehouses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("code"),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    is_active: bool | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[WarehouseRead]:
    return service.list(
        database,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        is_active=is_active,
    )


@router.post(
    "",
    response_model=WarehouseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear almacén",
    dependencies=[Depends(verify_csrf)],
)
def create_warehouse(
    data: WarehouseCreate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*WAREHOUSE_WRITE_ROLES)),
) -> WarehouseRead:
    return WarehouseRead.model_validate(service.create(database, data))


@router.get("/{warehouse_id}", response_model=WarehouseRead, summary="Consultar almacén")
def get_warehouse(
    warehouse_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> WarehouseRead:
    return WarehouseRead.model_validate(service.get(database, warehouse_id))


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    summary="Actualizar almacén",
    dependencies=[Depends(verify_csrf)],
)
def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*WAREHOUSE_WRITE_ROLES)),
) -> WarehouseRead:
    return WarehouseRead.model_validate(service.update(database, warehouse_id, data))


@router.delete(
    "/{warehouse_id}",
    summary="Eliminar o desactivar almacén",
    dependencies=[Depends(verify_csrf)],
)
def delete_warehouse(
    warehouse_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*WAREHOUSE_WRITE_ROLES)),
) -> dict[str, object]:
    physically_deleted = service.delete(database, warehouse_id)
    return {
        "success": True,
        "message": translate(
            "message.warehouse.deleted"
            if physically_deleted
            else "message.warehouse.deactivated"
        ),
        "physically_deleted": physically_deleted,
    }
