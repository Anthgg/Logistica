from math import ceil
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.warehouse import Warehouse
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.common import PaginatedResponse
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate


class WarehouseService:
    def __init__(self) -> None:
        self.repository = WarehouseRepository()

    def list(self, database: Session, **filters: object) -> PaginatedResponse[WarehouseRead]:
        sort_by = str(filters["sort_by"])
        if sort_by not in self.repository.SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[WarehouseRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get(self, database: Session, warehouse_id: UUID) -> Warehouse:
        warehouse = self.repository.get(database, warehouse_id)
        if not warehouse:
            raise ApplicationError("WAREHOUSE_NOT_FOUND", "El almacén no existe.", 404)
        return warehouse

    def create(self, database: Session, data: WarehouseCreate) -> Warehouse:
        if self.repository.get_by_code(database, data.code):
            raise ApplicationError("WAREHOUSE_CODE_EXISTS", "El código ya existe.", 409)
        warehouse = Warehouse(**data.model_dump())
        database.add(warehouse)
        try:
            database.commit()
        except IntegrityError as exc:
            database.rollback()
            raise ApplicationError("WAREHOUSE_CODE_EXISTS", "El código ya existe.", 409) from exc
        database.refresh(warehouse)
        return warehouse

    def update(
        self, database: Session, warehouse_id: UUID, data: WarehouseUpdate
    ) -> Warehouse:
        warehouse = self.get(database, warehouse_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(warehouse, field, value)
        try:
            database.commit()
        except IntegrityError as exc:
            database.rollback()
            raise ApplicationError("WAREHOUSE_CODE_EXISTS", "El código ya existe.", 409) from exc
        database.refresh(warehouse)
        return warehouse

    def delete(self, database: Session, warehouse_id: UUID) -> bool:
        warehouse = self.get(database, warehouse_id)
        if self.repository.has_movements(database, warehouse_id):
            warehouse.is_active = False
            database.commit()
            return False
        database.delete(warehouse)
        database.commit()
        return True
