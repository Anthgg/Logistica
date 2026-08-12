from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.inventory_movement import InventoryMovement
from app.models.warehouse import Warehouse


class WarehouseRepository:
    def get(self, database: Session, warehouse_id: UUID) -> Warehouse | None:
        return database.get(Warehouse, warehouse_id)

    def get_by_code(self, database: Session, code: str) -> Warehouse | None:
        return database.scalar(select(Warehouse).where(Warehouse.code == code))

    def list(
        self,
        database: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        is_active: bool | None = None,
    ) -> Tuple[List[Warehouse], int]:
        filters = []
        if is_active is not None:
            filters.append(Warehouse.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Warehouse.code.ilike(pattern),
                    Warehouse.name.ilike(pattern),
                )
            )

        total = database.scalar(select(func.count()).select_from(Warehouse).where(*filters)) or 0

        sort_col = getattr(Warehouse, sort_by, Warehouse.created_at)
        if sort_order == "desc":
            sort_col = sort_col.desc()
        else:
            sort_col = sort_col.asc()

        items = list(
            database.scalars(
                select(Warehouse)
                .where(*filters)
                .order_by(sort_col)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def has_movements(self, database: Session, warehouse_id: UUID) -> bool:
        stmt = select(InventoryMovement).where(
            InventoryMovement.warehouse_id == warehouse_id
        ).limit(1)
        return database.scalar(stmt) is not None
