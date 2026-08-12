from datetime import datetime

from pydantic import BaseModel

from app.schemas.shipment import ShipmentRead


class ActivityItem(BaseModel):
    event_type: str
    event_type_label: str | None = None
    created_at: datetime
    resource_type: str | None
    resource_type_label: str | None = None
    resource_id: str | None


class DashboardSummary(BaseModel):
    total_shipments: int
    pending_shipments: int
    in_transit_shipments: int
    delivered_shipments: int
    delayed_shipments: int
    open_incidents: int
    critical_incidents: int
    low_stock_items: int
    routes_today: int
    deliveries_today: int
    recent_shipments: list[ShipmentRead]
    recent_activity: list[ActivityItem]
    shipments_by_status: dict[str, int]
