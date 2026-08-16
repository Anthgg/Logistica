"""Pydantic schemas for the organization module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    country_code: str = Field(min_length=2, max_length=2)
    timezone: str = Field(default="America/Lima", max_length=50)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        return v.strip().upper()


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = Field(default=None, max_length=50)

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else v


class OrganizationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    status: str
    country_code: str
    timezone: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

class BranchCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    timezone: str = Field(default="America/Lima", max_length=50)
    address_text: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = Field(default=None, max_length=50)
    address_text: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class BranchStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    name: str
    status: str
    timezone: str
    address_text: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Warehouse (logistics extension)
# ---------------------------------------------------------------------------

class LogisticsWarehouseCreate(BaseModel):
    branch_id: UUID
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    warehouse_type: str = Field(default="general", max_length=30)
    address: str = Field(min_length=3, max_length=255)
    district: str = Field(min_length=2, max_length=100)
    province: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)
    capacity: float | None = Field(default=None, gt=0)
    is_default: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("warehouse_type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        allowed = {"general", "receiving", "dispatch", "quarantine", "returns", "transit"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"warehouse_type must be one of {allowed}")
        return v


class LogisticsWarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    warehouse_type: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    province: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=100)
    capacity: float | None = Field(default=None, gt=0)


class LogisticsWarehouseStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class LogisticsWarehouseSetDefault(BaseModel):
    is_default: bool = True


class LogisticsWarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    # Se emite para que el invariante "organization_id se deriva de la sede" sea
    # verificable por HTTP y no solo mirando la tabla.
    organization_id: UUID | None
    branch_id: UUID | None
    code: str
    name: str
    warehouse_type: str
    address: str | None
    district: str | None
    province: str | None
    department: str | None
    capacity: float | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime