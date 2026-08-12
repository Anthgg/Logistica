from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    address: str = Field(min_length=3, max_length=255)
    district: str = Field(min_length=2, max_length=100)
    province: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)
    capacity: Decimal | None = Field(default=None, gt=0)


class WarehouseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=30)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    province: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=100)
    capacity: Decimal | None = Field(default=None, gt=0)
    is_active: bool | None = None


class WarehouseRead(WarehouseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
