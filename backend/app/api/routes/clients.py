from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import CLIENT_WRITE_ROLES, LOGISTICS_READ_ROLES
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.i18n import translate
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.common import PaginatedResponse
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])
service = ClientService()


@router.get("", response_model=PaginatedResponse[ClientRead], summary="Listar clientes")
def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("business_name"),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    is_active: bool | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> PaginatedResponse[ClientRead]:
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
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cliente",
    dependencies=[Depends(verify_csrf)],
)
def create_client(
    data: ClientCreate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*CLIENT_WRITE_ROLES)),
) -> ClientRead:
    return ClientRead.model_validate(service.create(database, data, user))


@router.get("/{client_id}", response_model=ClientRead, summary="Consultar cliente")
def get_client(
    client_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> ClientRead:
    return ClientRead.model_validate(service.get(database, client_id))


@router.patch(
    "/{client_id}",
    response_model=ClientRead,
    summary="Actualizar cliente",
    dependencies=[Depends(verify_csrf)],
)
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*CLIENT_WRITE_ROLES)),
) -> ClientRead:
    return ClientRead.model_validate(service.update(database, client_id, data))


@router.delete(
    "/{client_id}",
    summary="Eliminar o desactivar cliente",
    dependencies=[Depends(verify_csrf)],
)
def delete_client(
    client_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*CLIENT_WRITE_ROLES)),
) -> dict[str, object]:
    physically_deleted = service.delete(database, client_id)
    return {
        "success": True,
        "message": translate(
            "message.client.deleted"
            if physically_deleted
            else "message.client.deactivated"
        ),
        "physically_deleted": physically_deleted,
    }
