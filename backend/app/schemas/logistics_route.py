from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RouteStatus = Literal["planned", "active", "completed", "cancelled"]


class RouteCreate(BaseModel):
    route_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    origin: str = Field(min_length=2, max_length=200)
    destination: str = Field(min_length=2, max_length=200)
    driver_name: str | None = Field(default=None, max_length=150)
    vehicle_plate: str | None = Field(default=None, max_length=20)
    scheduled_date: date
    status: RouteStatus = "planned"


class RouteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    origin: str | None = Field(default=None, min_length=2, max_length=200)
    destination: str | None = Field(default=None, min_length=2, max_length=200)
    driver_name: str | None = Field(default=None, max_length=150)
    vehicle_plate: str | None = Field(default=None, max_length=20)
    scheduled_date: date | None = None
    status: RouteStatus | None = None


class RouteRead(RouteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class RouteShipmentAssignment(BaseModel):
    shipment_ids: list[UUID] = Field(min_length=1, max_length=200)
