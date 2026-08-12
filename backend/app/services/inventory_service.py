from decimal import Decimal
from math import ceil
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.inventory_item import InventoryItem
from app.models.inventory_movement import InventoryMovement
from app.models.shipment import Shipment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    InventoryMovementCreate,
    InventoryMovementRead,
)
from app.services.audit_service import AuditService


class InventoryService:
    def __init__(self) -> None:
        self.repository = InventoryRepository()
        self.audit = AuditService()

    def list_items(
        self, database: Session, **filters: object
    ) -> PaginatedResponse[InventoryItemRead]:
        sort_by = str(filters["sort_by"])
        if sort_by not in self.repository.ITEM_SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list_items(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[InventoryItemRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get_item(self, database: Session, item_id: UUID) -> InventoryItem:
        item = self.repository.get_item(database, item_id)
        if not item:
            raise ApplicationError("INVENTORY_ITEM_NOT_FOUND", "El artículo no existe.", 404)
        return item

    def create_item(
        self, database: Session, data: InventoryItemCreate
    ) -> InventoryItem:
        warehouse = database.get(Warehouse, data.warehouse_id)
        if not warehouse or not warehouse.is_active:
            raise ApplicationError(
                "WAREHOUSE_NOT_AVAILABLE", "El almacén no existe o está inactivo.", 422
            )
        if self.repository.get_by_sku(database, data.warehouse_id, data.sku):
            raise ApplicationError(
                "INVENTORY_SKU_EXISTS",
                "El SKU ya existe en este almacén.",
                409,
            )
        item = InventoryItem(**data.model_dump())
        database.add(item)
        try:
            database.commit()
        except IntegrityError as exc:
            database.rollback()
            raise ApplicationError(
                "INVENTORY_SKU_EXISTS",
                "El SKU ya existe en este almacén.",
                409,
            ) from exc
        database.refresh(item)
        return item

    def update_item(
        self, database: Session, item_id: UUID, data: InventoryItemUpdate
    ) -> InventoryItem:
        item = self.get_item(database, item_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        database.commit()
        database.refresh(item)
        return item

    def create_movement(
        self, database: Session, data: InventoryMovementCreate, user: User
    ) -> InventoryMovement:
        item = self.repository.get_item(database, data.inventory_item_id, lock=True)
        if not item or not item.is_active:
            raise ApplicationError(
                "INVENTORY_ITEM_NOT_AVAILABLE",
                "El artículo no existe o está inactivo.",
                422,
            )
        if data.shipment_id and not database.get(Shipment, data.shipment_id):
            raise ApplicationError("SHIPMENT_NOT_FOUND", "El envío no existe.", 422)
        previous = Decimal(item.current_stock)
        if data.movement_type == "entry":
            resulting = previous + data.quantity
        elif data.movement_type == "exit":
            resulting = previous - data.quantity
        else:
            resulting = data.adjustment_resulting_stock
            if resulting is None:
                raise ApplicationError(
                    "ADJUSTMENT_STOCK_REQUIRED",
                    "Debe indicar el stock resultante del ajuste.",
                    422,
                )
        if resulting < 0:
            raise ApplicationError(
                "INSUFFICIENT_STOCK", "El movimiento dejaría stock negativo.", 409
            )
        item.current_stock = resulting
        movement = InventoryMovement(
            inventory_item_id=item.id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            previous_stock=previous,
            resulting_stock=resulting,
            reason=data.reason,
            shipment_id=data.shipment_id,
            created_by=user.id,
        )
        database.add(movement)
        database.flush()
        self.audit.record(
            database,
            "INVENTORY_MOVEMENT_CREATED",
            user_id=user.id,
            resource_type="inventory_item",
            resource_id=str(item.id),
            event_metadata={
                "movement_type": data.movement_type,
                "quantity": str(data.quantity),
            },
        )
        database.commit()
        database.refresh(movement)
        return movement

    def list_movements(
        self, database: Session, **filters: object
    ) -> PaginatedResponse[InventoryMovementRead]:
        sort_by = str(filters["sort_by"])
        if sort_by not in self.repository.MOVEMENT_SORT_FIELDS:
            raise ApplicationError("INVALID_SORT_FIELD", "Campo de orden no permitido.", 422)
        items, total = self.repository.list_movements(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[InventoryMovementRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )
