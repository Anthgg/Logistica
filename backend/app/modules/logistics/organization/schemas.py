"""Pydantic schemas for the organization module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.logistics.organization.reference_catalogs import (
    COUNTRY_CODES,
    TIMEZONE_CODES,
    WAREHOUSE_TYPE_CODES,
)

# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    # Opcional desde F005.1: si no llega, lo genera el backend. Se mantiene
    # aceptado para no romper a los clientes que ya lo envían.
    code: str | None = Field(default=None, min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    country_code: str = Field(min_length=2, max_length=2)
    timezone: str = Field(default="America/Lima", max_length=50)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else None

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        code = v.strip().upper()
        if code not in COUNTRY_CODES:
            raise ValueError(f"País '{code}' no pertenece al catálogo ISO soportado.")
        return code

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        tz = v.strip()
        if tz not in TIMEZONE_CODES:
            raise ValueError(f"Zona horaria '{tz}' no pertenece al catálogo soportado.")
        return tz


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


from app.modules.logistics.geography.schemas import UbigeoHierarchyResponse

# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

class BranchCreate(BaseModel):
    # Opcional desde F005.1: lo genera el backend cuando no llega.
    code: str | None = Field(default=None, min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    timezone: str = Field(default="America/Lima", max_length=50)
    ubigeo_code: str | None = Field(default=None, min_length=6, max_length=6, pattern="^[0-9]{6}$")
    address_text: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        tz = v.strip()
        if tz not in TIMEZONE_CODES:
            raise ValueError(f"Zona horaria '{tz}' no pertenece al catálogo soportado.")
        return tz


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = Field(default=None, max_length=50)
    ubigeo_code: str | None = Field(default=None, min_length=6, max_length=6, pattern="^[0-9]{6}$")
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
    ubigeo_code: str | None = None
    ubigeo: UbigeoHierarchyResponse | None = None
    address_text: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Warehouse (logistics extension)
# ---------------------------------------------------------------------------

class LogisticsWarehouseCreate(BaseModel):
    # La sede llega por la ruta (`/branches/{branch_id}/warehouses`) y es la unica
    # autoridad: el servicio deriva de ella la organizacion. Exigirla tambien en el
    # cuerpo obligaba al cliente a repetir un UUID que el backend ya ignora, y
    # devolvia 422 a cualquier formulario que hiciera lo correcto.
    # Opcional desde F005.1: lo genera el backend cuando no llega.
    code: str | None = Field(default=None, min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    warehouse_type: str = Field(default="general", max_length=30)
    #: Dirección propia del almacén dentro de la sede («Nave B — Puerta 4»), no la
    #: de la sede. Es lo único geográfico que sigue escribiendo el usuario.
    address: str | None = Field(default=None, max_length=255)
    #: Distrito, provincia y departamento pasan a derivarse del UBIGEO de la sede.
    #: Se siguen aceptando por compatibilidad, pero el backend los IGNORA cuando la
    #: sede tiene ubicación normalizada: así es imposible registrar un almacén en
    #: una sede de Lima declarando Arequipa.
    district: str | None = Field(default=None, max_length=100)
    province: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    capacity: float | None = Field(default=None, gt=0)
    is_default: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else None

    @field_validator("warehouse_type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        # La lista vive en `reference_catalogs`, que es lo que sirve el endpoint del
        # catálogo. Antes estaba escrita aquí y repetida en el frontend.
        value = v.strip().lower()
        if value not in WAREHOUSE_TYPE_CODES:
            raise ValueError(
                f"Tipo de almacén '{value}' no pertenece al catálogo soportado."
            )
        return value


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

# ---------------------------------------------------------------------------
# Catálogos de referencia (F005.1)
# ---------------------------------------------------------------------------

class CountryResponse(BaseModel):
    code: str
    name: str


class TimezoneResponse(BaseModel):
    code: str
    name: str
    country_code: str


class WarehouseTypeResponse(BaseModel):
    code: str
    name: str
