from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

MovementType = Literal["entry", "exit", "adjustment"]


class InventoryItemCreate(BaseModel):
    warehouse_id: UUID
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    current_stock: Decimal = Field(default=Decimal("0"), ge=0)
    minimum_stock: Decimal = Field(default=Decimal("0"), ge=0)
    unit: str = Field(min_length=1, max_length=30)


class InventoryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    minimum_stock: Decimal | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    is_active: bool | None = None


class InventoryItemRead(InventoryItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InventoryMovementCreate(BaseModel):
    inventory_item_id: UUID
    movement_type: MovementType
    quantity: Decimal = Field(gt=0)
    reason: str = Field(min_length=2, max_length=1000)
    shipment_id: UUID | None = None
    adjustment_resulting_stock: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_adjustment(self) -> "InventoryMovementCreate":
        if self.movement_type == "adjustment" and self.adjustment_resulting_stock is None:
            raise ValueError("adjustment_resulting_stock es obligatorio para ajustes")
        if self.movement_type != "adjustment" and self.adjustment_resulting_stock is not None:
            raise ValueError("adjustment_resulting_stock solo se admite en ajustes")
        return self


class InventoryMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventory_item_id: UUID
    movement_type: MovementType
    quantity: Decimal
    previous_stock: Decimal
    resulting_stock: Decimal
    reason: str
    shipment_id: UUID | None
    created_by: UUID
    created_at: datetime
