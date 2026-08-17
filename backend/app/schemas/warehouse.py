from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    # Obligatorio desde F004: sin sede el almacen nace sin organizacion y queda
    # invisible para cualquier listado acotado por tenant. La organizacion se deriva
    # de la sede dentro del servicio; nunca se acepta desde el cliente.
    branch_id: UUID
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
    # Las filas heredadas (semilla demo) tienen estas columnas en NULL. Declararlas
    # obligatorias aqui convertiria un listado legitimo en un 500 de serializacion.
    branch_id: UUID | None = None
    organization_id: UUID | None = None
    address: str | None = None
    district: str | None = None
    province: str | None = None
    department: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
