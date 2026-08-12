from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.i18n import translate

ShipmentStatus = Literal[
    "registered",
    "pending_pickup",
    "picked_up",
    "warehouse_received",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "delayed",
    "cancelled",
    "returned",
]
ShipmentPriority = Literal["low", "normal", "high", "urgent"]


class ShipmentCreate(BaseModel):
    client_id: UUID
    origin_address: str = Field(min_length=3, max_length=255)
    destination_address: str = Field(min_length=3, max_length=255)
    origin_district: str = Field(min_length=2, max_length=100)
    destination_district: str = Field(min_length=2, max_length=100)
    package_description: str = Field(min_length=2, max_length=2000)
    package_count: int = Field(gt=0, le=10000)
    total_weight: Decimal = Field(gt=0)
    declared_value: Decimal | None = Field(default=None, ge=0)
    priority: ShipmentPriority = "normal"
    expected_delivery_at: datetime | None = None


class ShipmentUpdate(BaseModel):
    origin_address: str | None = Field(default=None, min_length=3, max_length=255)
    destination_address: str | None = Field(default=None, min_length=3, max_length=255)
    origin_district: str | None = Field(default=None, min_length=2, max_length=100)
    destination_district: str | None = Field(default=None, min_length=2, max_length=100)
    package_description: str | None = Field(default=None, min_length=2, max_length=2000)
    package_count: int | None = Field(default=None, gt=0, le=10000)
    total_weight: Decimal | None = Field(default=None, gt=0)
    declared_value: Decimal | None = Field(default=None, ge=0)
    priority: ShipmentPriority | None = None
    expected_delivery_at: datetime | None = None


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
    description: str | None = Field(default=None, max_length=1000)
    location: str | None = Field(default=None, max_length=200)


class ShipmentRead(ShipmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tracking_code: str
    status: ShipmentStatus
    status_label: str = ""
    priority_label: str = ""
    assigned_route_id: UUID | None
    delivered_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def add_localized_labels(self) -> "ShipmentRead":
        self.status_label = translate(
            f"status.{self.status}",
            default=self.status.replace("_", " ").title(),
        )
        self.priority_label = translate(
            f"priority.{self.priority}",
            default=self.priority.replace("_", " ").title(),
        )
        return self


class ShipmentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    previous_status: str | None
    previous_status_label: str | None = None
    new_status: str
    new_status_label: str = ""
    description: str | None
    location: str | None
    created_by: UUID
    created_at: datetime

    @model_validator(mode="after")
    def add_localized_labels(self) -> "ShipmentEventRead":
        if self.previous_status:
            self.previous_status_label = translate(
                f"status.{self.previous_status}",
                default=self.previous_status.replace("_", " ").title(),
            )
        self.new_status_label = translate(
            f"status.{self.new_status}",
            default=self.new_status.replace("_", " ").title(),
        )
        return self
