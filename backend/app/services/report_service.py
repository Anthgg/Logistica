from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.inventory_item import InventoryItem
from app.models.logistics_route import LogisticsRoute
from app.models.route_shipment import RouteShipment
from app.models.shipment import Shipment
from app.schemas.report import CountGroup, DateCount, LowStockRow, RouteSummaryRow


def _date_bounds(
    date_from: date | None, date_to: date | None
) -> tuple[datetime | None, datetime | None]:
    start = (
        datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        if date_from
        else None
    )
    end = (
        datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    )
    return start, end


class ReportService:
    def _shipment_filters(
        self,
        date_from: date | None,
        date_to: date | None,
        route_id: UUID | None,
    ) -> list[object]:
        start, end = _date_bounds(date_from, date_to)
        filters: list[object] = []
        if start:
            filters.append(Shipment.created_at >= start)
        if end:
            filters.append(Shipment.created_at <= end)
        if route_id:
            filters.append(Shipment.assigned_route_id == route_id)
        return filters

    def shipments_by_status(
        self,
        database: Session,
        date_from: date | None,
        date_to: date | None,
        route_id: UUID | None,
    ) -> list[CountGroup]:
        rows = database.execute(
            select(Shipment.status, func.count(Shipment.id))
            .where(*self._shipment_filters(date_from, date_to, route_id))
            .group_by(Shipment.status)
            .order_by(Shipment.status)
        ).all()
        return [CountGroup(key=str(row[0]), count=int(row[1])) for row in rows]

    def shipments_by_priority(
        self,
        database: Session,
        date_from: date | None,
        date_to: date | None,
        route_id: UUID | None,
    ) -> list[CountGroup]:
        rows = database.execute(
            select(Shipment.priority, func.count(Shipment.id))
            .where(*self._shipment_filters(date_from, date_to, route_id))
            .group_by(Shipment.priority)
            .order_by(Shipment.priority)
        ).all()
        return [CountGroup(key=str(row[0]), count=int(row[1])) for row in rows]

    def deliveries_by_date(
        self, database: Session, date_from: date | None, date_to: date | None
    ) -> list[DateCount]:
        filters = [Shipment.delivered_at.is_not(None)]
        start, end = _date_bounds(date_from, date_to)
        if start:
            filters.append(Shipment.delivered_at >= start)
        if end:
            filters.append(Shipment.delivered_at <= end)
        delivery_date = func.date(Shipment.delivered_at)
        rows = database.execute(
            select(delivery_date, func.count(Shipment.id))
            .where(*filters)
            .group_by(delivery_date)
            .order_by(delivery_date)
        ).all()
        return [DateCount(date=row[0], count=int(row[1])) for row in rows]

    def incidents_summary(
        self, database: Session, date_from: date | None, date_to: date | None
    ) -> list[CountGroup]:
        start, end = _date_bounds(date_from, date_to)
        filters = []
        if start:
            filters.append(Incident.created_at >= start)
        if end:
            filters.append(Incident.created_at <= end)
        key = Incident.severity + ":" + Incident.status
        rows = database.execute(
            select(key, func.count(Incident.id))
            .where(*filters)
            .group_by(Incident.severity, Incident.status)
            .order_by(Incident.severity, Incident.status)
        ).all()
        return [CountGroup(key=str(row[0]), count=int(row[1])) for row in rows]

    def low_stock(
        self, database: Session, warehouse_id: UUID | None
    ) -> list[LowStockRow]:
        filters = [
            InventoryItem.is_active.is_(True),
            InventoryItem.current_stock <= InventoryItem.minimum_stock,
        ]
        if warehouse_id:
            filters.append(InventoryItem.warehouse_id == warehouse_id)
        items = database.scalars(
            select(InventoryItem)
            .where(*filters)
            .order_by(InventoryItem.current_stock.asc())
        )
        return [
            LowStockRow(
                id=item.id,
                warehouse_id=item.warehouse_id,
                sku=item.sku,
                name=item.name,
                current_stock=item.current_stock,
                minimum_stock=item.minimum_stock,
            )
            for item in items
        ]

    def routes_summary(
        self,
        database: Session,
        date_from: date | None,
        date_to: date | None,
        route_id: UUID | None,
    ) -> list[RouteSummaryRow]:
        filters = []
        if date_from:
            filters.append(LogisticsRoute.scheduled_date >= date_from)
        if date_to:
            filters.append(LogisticsRoute.scheduled_date <= date_to)
        if route_id:
            filters.append(LogisticsRoute.id == route_id)
        rows = database.execute(
            select(
                LogisticsRoute.id,
                LogisticsRoute.route_code,
                LogisticsRoute.status,
                func.count(RouteShipment.id),
            )
            .outerjoin(RouteShipment, RouteShipment.route_id == LogisticsRoute.id)
            .where(*filters)
            .group_by(
                LogisticsRoute.id,
                LogisticsRoute.route_code,
                LogisticsRoute.status,
            )
            .order_by(LogisticsRoute.scheduled_date.desc())
        ).all()
        return [
            RouteSummaryRow(
                route_id=row[0],
                route_code=str(row[1]),
                status=str(row[2]),
                shipment_count=int(row[3]),
            )
            for row in rows
        ]
