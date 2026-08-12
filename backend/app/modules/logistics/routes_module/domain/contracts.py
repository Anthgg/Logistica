"""Routes domain — contracts for route calculation and geocoding.

Defines protocols for directions, geocoding and map-matching providers
so the application layer can switch providers without changing business
logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class GeoCoordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class RouteRequest:
    """Input for route calculation."""
    origin: GeoCoordinate
    destination: GeoCoordinate
    waypoints: list[GeoCoordinate] | None = None


@dataclass(frozen=True)
class RouteResult:
    """Output of a route calculation."""
    distance_meters: float
    duration_seconds: float
    geometry_geojson: str
    provider: str


@dataclass(frozen=True)
class GeocodeRequest:
    """Input for geocoding."""
    address: str


@dataclass(frozen=True)
class GeocodeResult:
    """Output of geocoding."""
    coordinate: GeoCoordinate
    formatted_address: str
    provider: str


@dataclass(frozen=True)
class MapMatchRequest:
    """Input for map matching."""
    coordinates: list[GeoCoordinate]


@dataclass(frozen=True)
class MapMatchResult:
    """Output of map matching."""
    geometry_geojson: str
    confidence: float
    provider: str


# ---------------------------------------------------------------------------
# Provider protocols
# ---------------------------------------------------------------------------

class DirectionsProvider(Protocol):
    """Calculates routes between coordinates."""

    async def calculate(self, request: RouteRequest) -> RouteResult: ...


class GeocodingProvider(Protocol):
    """Geocodes an address to coordinates."""

    async def geocode(self, request: GeocodeRequest) -> GeocodeResult: ...


class MapMatchingProvider(Protocol):
    """Snaps GPS traces to road network."""

    async def match(self, request: MapMatchRequest) -> MapMatchResult: ...


class RouteRepository(Protocol):
    """Persists and retrieves calculated routes."""

    async def save(self, result: RouteResult, source_id: UUID) -> UUID: ...

    async def get_by_id(self, route_id: UUID) -> RouteResult | None: ...


class RouteCalculationService(Protocol):
    """Application service that orchestrates route calculation."""

    async def calculate_route(self, request: RouteRequest) -> RouteResult: ...

    async def recalculate_route(self, route_id: UUID, request: RouteRequest) -> RouteResult: ...