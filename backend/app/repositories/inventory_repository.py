from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.inventory_movement import InventoryMovement


class InventoryRepository:
    ITEM_SORT_FIELDS = {
        "sku": InventoryItem.sku,
        "name": InventoryItem.name,
        "current_stock": InventoryItem.current_stock,
        "created_at": InventoryItem.created_at,
    }
    MOVEMENT_SORT_FIELDS = {
        "created_at": InventoryMovement.created_at,
        "quantity": InventoryMovement.quantity,
        "movement_type": InventoryMovement.movement_type,
    }

    def get_item(
        self, database: Session, item_id: UUID, *, lock: bool = False
    ) -> InventoryItem | None:
        statement = select(InventoryItem).where(InventoryItem.id == item_id)
        if lock:
            statement = statement.with_for_update()
        return database.scalar(statement)

    def get_by_sku(
        self, database: Session, warehouse_id: UUID, sku: str
    ) -> InventoryItem | None:
        return database.scalar(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.sku == sku,
            )
        )

    def list_items(
        self,
        database: Session,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: str,
        warehouse_id: UUID | None,
        is_active: bool | None,
        low_stock: bool | None,
    ) -> tuple[list[InventoryItem], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(InventoryItem.sku.ilike(term), InventoryItem.name.ilike(term)))
        if warehouse_id:
            filters.append(InventoryItem.warehouse_id == warehouse_id)
        if is_active is not None:
            filters.append(InventoryItem.is_active == is_active)
        if low_stock:
            filters.append(InventoryItem.current_stock <= InventoryItem.minimum_stock)
        total = database.scalar(
            select(func.count()).select_from(InventoryItem).where(*filters)
        ) or 0
        column = self.ITEM_SORT_FIELDS[sort_by]
        ordering = column.desc() if sort_order == "desc" else column.asc()
        return (
            list(
                database.scalars(
                    select(InventoryItem)
                    .where(*filters)
                    .order_by(ordering)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ),
            total,
        )

    def list_movements(
        self,
        database: Session,
        *,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
        item_id: UUID | None,
        movement_type: str | None,
    ) -> tuple[list[InventoryMovement], int]:
        filters = []
        if item_id:
            filters.append(InventoryMovement.inventory_item_id == item_id)
        if movement_type:
            filters.append(InventoryMovement.movement_type == movement_type)
        total = database.scalar(
            select(func.count()).select_from(InventoryMovement).where(*filters)
        ) or 0
        column = self.MOVEMENT_SORT_FIELDS[sort_by]
        ordering = column.desc() if sort_order == "desc" else column.asc()
        return (
            list(
                database.scalars(
                    select(InventoryMovement)
                    .where(*filters)
                    .order_by(ordering)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ),
            total,
        )
