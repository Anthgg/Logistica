from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.logistics_route import LogisticsRoute
from app.models.route_shipment import RouteShipment


class RouteRepository:
    def get(
        self, database: Session, route_id: UUID, *, lock: bool = False
    ) -> LogisticsRoute | None:
        stmt = select(LogisticsRoute).where(LogisticsRoute.id == route_id)
        if lock:
            stmt = stmt.with_for_update()
        return database.scalar(stmt)

    def get_by_code(self, database: Session, code: str) -> LogisticsRoute | None:
        return database.scalar(
            select(LogisticsRoute).where(LogisticsRoute.route_code == code)
        )

    def list(
        self,
        database: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        status: str | None = None,
    ) -> Tuple[List[LogisticsRoute], int]:
        filters = []
        if status:
            filters.append(LogisticsRoute.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    LogisticsRoute.route_code.ilike(pattern),
                    LogisticsRoute.name.ilike(pattern),
                    LogisticsRoute.origin.ilike(pattern),
                    LogisticsRoute.destination.ilike(pattern),
                )
            )

        total = database.scalar(select(func.count()).select_from(LogisticsRoute).where(*filters)) or 0

        sort_col = getattr(LogisticsRoute, sort_by, LogisticsRoute.created_at)
        if sort_order == "desc":
            sort_col = sort_col.desc()
        else:
            sort_col = sort_col.asc()

        items = list(
            database.scalars(
                select(LogisticsRoute)
                .where(*filters)
                .order_by(sort_col)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def assignment(
        self, database: Session, route_id: UUID, shipment_id: UUID
    ) -> RouteShipment | None:
        stmt = select(RouteShipment).where(
            RouteShipment.route_id == route_id,
            RouteShipment.shipment_id == shipment_id,
        )
        return database.scalar(stmt)
