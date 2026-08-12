from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.incident import Incident
from app.models.inventory_item import InventoryItem
from app.models.logistics_route import LogisticsRoute
from app.models.shipment import Shipment
from app.schemas.dashboard import ActivityItem, DashboardSummary
from app.schemas.shipment import ShipmentRead


class DashboardService:
    def summary(self, database: Session) -> DashboardSummary:
        status_rows = database.execute(
            select(Shipment.status, func.count(Shipment.id)).group_by(Shipment.status)
        ).all()
        by_status = {str(row[0]): int(row[1]) for row in status_rows}
        today = date.today()
        open_incidents = database.scalar(
            select(func.count())
            .select_from(Incident)
            .where(Incident.status.in_(("open", "investigating")))
        ) or 0
        critical_incidents = database.scalar(
            select(func.count())
            .select_from(Incident)
            .where(
                Incident.severity == "critical",
                Incident.status.in_(("open", "investigating")),
            )
        ) or 0
        low_stock = database.scalar(
            select(func.count())
            .select_from(InventoryItem)
            .where(
                InventoryItem.is_active.is_(True),
                InventoryItem.current_stock <= InventoryItem.minimum_stock,
            )
        ) or 0
        routes_today = database.scalar(
            select(func.count())
            .select_from(LogisticsRoute)
            .where(LogisticsRoute.scheduled_date == today)
        ) or 0
        deliveries_today = database.scalar(
            select(func.count())
            .select_from(Shipment)
            .where(func.date(Shipment.delivered_at) == today)
        ) or 0
        recent_shipments = list(
            database.scalars(
                select(Shipment).order_by(Shipment.created_at.desc()).limit(10)
            )
        )
        recent_audits = list(
            database.scalars(
                select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
            )
        )
        return DashboardSummary(
            total_shipments=sum(by_status.values()),
            pending_shipments=sum(
                by_status.get(state, 0)
                for state in (
                    "registered",
                    "pending_pickup",
                    "picked_up",
                    "warehouse_received",
                )
            ),
            in_transit_shipments=by_status.get("in_transit", 0)
            + by_status.get("out_for_delivery", 0),
            delivered_shipments=by_status.get("delivered", 0),
            delayed_shipments=by_status.get("delayed", 0),
            open_incidents=open_incidents,
            critical_incidents=critical_incidents,
            low_stock_items=low_stock,
            routes_today=routes_today,
            deliveries_today=deliveries_today,
            recent_shipments=[
                ShipmentRead.model_validate(item) for item in recent_shipments
            ],
            recent_activity=[
                ActivityItem(
                    event_type=item.event_type,
                    created_at=item.created_at,
                    resource_type=item.resource_type,
                    resource_id=item.resource_id,
                )
                for item in recent_audits
            ],
            shipments_by_status=by_status,
        )
