"""Pydantic schemas and DTOs for geocoding requests and responses (Phase 005.4 / F005.4)."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.logistics.geocoding.base import GeocodeAddress, GeocodeLocationResult


class GeocodeAddressDTO(BaseModel):
    """Structured postal address components returned in geocoding responses."""

    road: str | None = Field(default=None, description="Street or road name")
    house_number: str | None = Field(default=None, description="Building or street number")
    neighbourhood: str | None = Field(default=None, description="Neighbourhood / Urbanización")
    suburb: str | None = Field(default=None, description="Suburb / Sector")
    district: str | None = Field(default=None, description="District / Distrito")
    city: str | None = Field(default=None, description="City / Ciudad")
    province: str | None = Field(default=None, description="Province / Provincia")
    department: str | None = Field(default=None, description="Department / Departamento")
    postcode: str | None = Field(default=None, description="Postal code")
    country: str | None = Field(default="Perú", description="Country name")
    country_code: str | None = Field(default="pe", description="ISO two-letter country code")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, addr: GeocodeAddress | None) -> "GeocodeAddressDTO | None":
        """Convert a domain GeocodeAddress dataclass instance to a GeocodeAddressDTO."""
        if addr is None:
            return None
        return cls(
            road=addr.road,
            house_number=addr.house_number,
            neighbourhood=addr.neighbourhood,
            suburb=addr.suburb,
            district=addr.district,
            city=addr.city,
            province=addr.province,
            department=addr.department,
            postcode=addr.postcode,
            country=addr.country,
            country_code=addr.country_code,
        )


class GeocodeLocationResultDTO(BaseModel):
    """Normalized geocoding candidate location result item."""

    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude [-90.0, 90.0]")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude [-180.0, 180.0]")
    display_name: str = Field(..., min_length=1, description="Complete formatted display address")
    place_id: str | None = Field(default=None, description="Upstream place identifier")
    osm_type: str | None = Field(default=None, description="OpenStreetMap element type (node, way, relation)")
    osm_id: str | None = Field(default=None, description="OpenStreetMap identifier")
    bounding_box: list[float] | None = Field(
        default=None,
        description="Bounding box [south_lat, north_lat, west_lon, east_lon]",
    )
    address: GeocodeAddressDTO | None = Field(default=None, description="Structured postal address")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Match confidence score [0.0, 1.0]")
    raw_type: str | None = Field(default=None, description="Raw feature type from provider")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, result: GeocodeLocationResult | None) -> "GeocodeLocationResultDTO | None":
        """Convert a domain GeocodeLocationResult dataclass instance to a GeocodeLocationResultDTO."""
        if result is None:
            return None
        return cls(
            latitude=result.latitude,
            longitude=result.longitude,
            display_name=result.display_name,
            place_id=str(result.place_id) if result.place_id is not None else None,
            osm_type=result.osm_type,
            osm_id=str(result.osm_id) if result.osm_id is not None else None,
            bounding_box=result.bounding_box,
            address=GeocodeAddressDTO.from_domain(result.address),
            confidence=result.confidence,
            raw_type=result.raw_type,
        )


class GeocodeSearchRequest(BaseModel):
    """Request payload for forward address geocoding search."""

    address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Street address or location query string",
        json_schema_extra={"example": "Av. Larco 1234"},
    )
    ubigeo_code: str | None = Field(
        default=None,
        min_length=6,
        max_length=6,
        pattern=r"^[0-9]{6}$",
        description="Optional 6-digit canonical Peruvian UBIGEO code for geographic enrichment",
        json_schema_extra={"example": "150122"},
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of candidate results to return (1-20)",
    )

    @field_validator("address")
    @classmethod
    def validate_address_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("El campo address no puede estar vacío.")
        return cleaned

    @field_validator("ubigeo_code")
    @classmethod
    def normalize_ubigeo_code(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class GeocodeSearchData(BaseModel):
    """Data payload for forward geocoding search response."""

    results: list[GeocodeLocationResultDTO] = Field(default_factory=list, description="List of candidate matches")
    count: int = Field(default=0, description="Total number of returned candidate matches")


# Alias for compatibility with varying naming conventions
GeocodeSearchResultsData = GeocodeSearchData


class GeocodeSearchResponse(BaseModel):
    """Standard response envelope for forward geocoding search."""

    success: bool = True
    data: GeocodeSearchData


class GeocodeReverseRequest(BaseModel):
    """Request payload for reverse geocoding geographic coordinates."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="WGS84 latitude coordinate [-90.0, 90.0]",
        json_schema_extra={"example": -12.1215},
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="WGS84 longitude coordinate [-180.0, 180.0]",
        json_schema_extra={"example": -77.0298},
    )
    zoom: int | None = Field(
        default=18,
        ge=0,
        le=18,
        description="OSM detail zoom level (0-18)",
    )


class GeocodeReverseResponse(BaseModel):
    """Standard response envelope for reverse geocoding."""

    success: bool = True
    data: GeocodeLocationResultDTO | None = Field(
        default=None,
        description="Matched address result, or null if no address could be resolved",
    )
