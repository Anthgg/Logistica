from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WarehouseCreate(BaseModel):
    # Obligatorio desde F004: sin sede el almacen nace sin organizacion y queda
    # invisible para cualquier listado acotado por tenant. La organizacion se deriva
    # de la sede dentro del servicio; nunca se acepta desde el cliente.
    branch_id: UUID
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    address: str = Field(min_length=3, max_length=255)
    uses_branch_location: bool = True
    latitude: Decimal | None = Field(
        default=None, ge=Decimal(-90), le=Decimal(90), allow_inf_nan=False
    )
    longitude: Decimal | None = Field(
        default=None, ge=Decimal(-180), le=Decimal(180), allow_inf_nan=False
    )
    district: str = Field(min_length=2, max_length=100)
    province: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)
    capacity: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_location_mode(self) -> "WarehouseCreate":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitud y longitud deben enviarse juntas.")
        if self.uses_branch_location and self.latitude is not None:
            raise ValueError("La ubicación heredada no acepta coordenadas propias.")
        if not self.uses_branch_location and self.latitude is None:
            raise ValueError("La ubicación propia requiere latitud y longitud confirmadas.")
        return self


class WarehouseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=30)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    uses_branch_location: bool | None = None
    latitude: Decimal | None = Field(
        default=None, ge=Decimal(-90), le=Decimal(90), allow_inf_nan=False
    )
    longitude: Decimal | None = Field(
        default=None, ge=Decimal(-180), le=Decimal(180), allow_inf_nan=False
    )
    district: str | None = Field(default=None, min_length=2, max_length=100)
    province: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=100)
    capacity: Decimal | None = Field(default=None, gt=0)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_location_mode(self) -> "WarehouseUpdate":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitud y longitud deben enviarse juntas.")
        if self.uses_branch_location is True and self.latitude is not None:
            raise ValueError("La ubicación heredada no acepta coordenadas propias.")
        if self.uses_branch_location is False and self.latitude is None:
            raise ValueError("La ubicación propia requiere latitud y longitud confirmadas.")
        return self


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
    effective_latitude: Decimal | None = None
    effective_longitude: Decimal | None = None
    location_source: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
