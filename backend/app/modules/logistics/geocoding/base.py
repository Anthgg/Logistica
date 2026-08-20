"""Base interfaces, protocols, and data models for geocoding."""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.modules.logistics.geocoding.exceptions import GeocodingInvalidCoordinatesError


def validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """Validate latitude and longitude against WGS84 standards.

    Latitude must be in [-90.0, 90.0].
    Longitude must be in [-180.0, 180.0].
    Returns (lat, lon) as normalized floats or raises GeocodingInvalidCoordinatesError.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError) as exc:
        raise GeocodingInvalidCoordinatesError(
            f"Coordenadas inválidas: lat={latitude}, lon={longitude}"
        ) from exc

    if not (-90.0 <= lat <= 90.0):
        raise GeocodingInvalidCoordinatesError(
            f"Latitud fuera de rango [-90.0, 90.0]: {lat}"
        )
    if not (-180.0 <= lon <= 180.0):
        raise GeocodingInvalidCoordinatesError(
            f"Longitud fuera de rango [-180.0, 180.0]: {lon}"
        )

    return lat, lon


@dataclass
class GeocodeAddress:
    """Structured postal address components returned by a geocoding provider."""

    road: str | None = None
    house_number: str | None = None
    neighbourhood: str | None = None
    suburb: str | None = None
    district: str | None = None
    city: str | None = None
    province: str | None = None
    department: str | None = None
    postcode: str | None = None
    country: str = "Perú"
    country_code: str = "pe"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "road": self.road,
            "house_number": self.house_number,
            "neighbourhood": self.neighbourhood,
            "suburb": self.suburb,
            "district": self.district,
            "city": self.city,
            "province": self.province,
            "department": self.department,
            "postcode": self.postcode,
            "country": self.country,
            "country_code": self.country_code,
        }


@dataclass
class GeocodeLocationResult:
    """Normalized geocoding location item for search and reverse operations."""

    latitude: float
    longitude: float
    display_name: str
    place_id: str | int | None = None
    osm_type: str | None = None
    osm_id: int | str | None = None
    bounding_box: list[float] | None = None
    address: GeocodeAddress | None = None
    confidence: float | None = None
    raw_type: str | None = None

    def __post_init__(self) -> None:
        self.latitude, self.longitude = validate_coordinates(self.latitude, self.longitude)

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "display_name": self.display_name,
            "place_id": str(self.place_id) if self.place_id is not None else None,
            "osm_type": self.osm_type,
            "osm_id": str(self.osm_id) if self.osm_id is not None else None,
            "bounding_box": self.bounding_box,
            "address": self.address.to_dict() if self.address else None,
            "confidence": self.confidence,
            "raw_type": self.raw_type,
        }


@runtime_checkable
class GeocodingProvider(Protocol):
    """Protocol interface defining operations for any geocoding provider."""

    async def search(self, query: str, limit: int = 5) -> list[GeocodeLocationResult]:
        """Search forward geocoding results for a given query string.

        Args:
            query: Address or location search query string.
            limit: Maximum number of candidate results to return.

        Returns:
            List of GeocodeLocationResult items ordered by relevance.
        """
        ...

    async def reverse(self, latitude: float, longitude: float) -> GeocodeLocationResult | None:
        """Reverse geocode geographic coordinates to a structured location result.

        Args:
            latitude: WGS84 latitude (-90 to 90).
            longitude: WGS84 longitude (-180 to 180).

        Returns:
            GeocodeLocationResult if found, or None.
        """
        ...
