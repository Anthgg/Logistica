from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.shipment import Shipment


class ClientRepository:
    def get(self, database: Session, client_id: UUID) -> Client | None:
        return database.get(Client, client_id)

    def get_by_document(self, database: Session, number: str) -> Client | None:
        return database.scalar(select(Client).where(Client.document_number == number))

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
    ) -> Tuple[List[Client], int]:
        filters = []
        if is_active is not None:
            filters.append(Client.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Client.business_name.ilike(pattern),
                    Client.document_number.ilike(pattern),
                )
            )

        total = database.scalar(select(func.count()).select_from(Client).where(*filters)) or 0

        sort_col = getattr(Client, sort_by, Client.created_at)
        if sort_order == "desc":
            sort_col = sort_col.desc()
        else:
            sort_col = sort_col.asc()

        items = list(
            database.scalars(
                select(Client)
                .where(*filters)
                .order_by(sort_col)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def has_shipments(self, database: Session, client_id: UUID) -> bool:
        stmt = select(Shipment).where(Shipment.client_id == client_id).limit(1)
        return database.scalar(stmt) is not None
