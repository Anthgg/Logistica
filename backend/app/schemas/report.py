from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CountGroup(BaseModel):
    key: str
    count: int


class DateCount(BaseModel):
    date: date
    count: int


class LowStockRow(BaseModel):
    id: UUID
    warehouse_id: UUID
    sku: str
    name: str
    current_stock: Decimal
    minimum_stock: Decimal


class RouteSummaryRow(BaseModel):
    route_id: UUID
    route_code: str
    status: str
    shipment_count: int
