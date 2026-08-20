"""OpenStreetMap Nominatim geocoding provider implementation."""

import logging
from typing import Any

import httpx

from app.modules.logistics.geocoding.base import (
    GeocodeAddress,
    GeocodeLocationResult,
    validate_coordinates,
)
from app.modules.logistics.geocoding.exceptions import (
    GeocodingProviderUnavailableError,
    GeocodingRateLimitError,
)

logger = logging.getLogger(__name__)


class NominatimGeocodingProvider:
    """Geocoding provider integrating with OpenStreetMap Nominatim API.

    Implements GeocodingProvider protocol complying with Nominatim's usage policy.
    """

    def __init__(
        self,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = "LogisticaT1-BranchLocator/1.0 (contact@logisticat1.pe)",
        timeout_seconds: float = 5.0,
        country_codes: str = "pe",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.country_codes = country_codes
        self._external_client = client
        self._internal_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        if self._internal_client is None or self._internal_client.is_closed:
            self._internal_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds),
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                },
            )
        return self._internal_client

    async def close(self) -> None:
        """Close internal HTTP client if created."""
        if self._internal_client is not None and not self._internal_client.is_closed:
            await self._internal_client.aclose()
            self._internal_client = None

    async def __aenter__(self) -> "NominatimGeocodingProvider":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _parse_address(self, raw_addr: dict[str, Any]) -> GeocodeAddress:
        """Extract structured address components from Nominatim response."""
        road = (
            raw_addr.get("road")
            or raw_addr.get("pedestrian")
            or raw_addr.get("street")
            or raw_addr.get("footway")
            or raw_addr.get("path")
        )
        house_number = raw_addr.get("house_number") or raw_addr.get("housenumber")
        neighbourhood = (
            raw_addr.get("neighbourhood")
            or raw_addr.get("neighborhood")
            or raw_addr.get("residential")
        )
        suburb = raw_addr.get("suburb")
        district = (
            raw_addr.get("city_district")
            or raw_addr.get("district")
            or raw_addr.get("municipality")
            or raw_addr.get("suburb")
        )
        city = (
            raw_addr.get("city")
            or raw_addr.get("town")
            or raw_addr.get("village")
            or raw_addr.get("hamlet")
        )
        province = (
            raw_addr.get("county")
            or raw_addr.get("state_district")
            or raw_addr.get("province")
        )
        department = (
            raw_addr.get("state")
            or raw_addr.get("region")
            or raw_addr.get("department")
        )
        postcode = raw_addr.get("postcode")
        country = raw_addr.get("country", "Perú")
        country_code = raw_addr.get("country_code", "pe")

        return GeocodeAddress(
            road=road,
            house_number=house_number,
            neighbourhood=neighbourhood,
            suburb=suburb,
            district=district,
            city=city,
            province=province,
            department=department,
            postcode=postcode,
            country=country,
            country_code=country_code,
        )

    def _parse_item(self, item: dict[str, Any]) -> GeocodeLocationResult:
        """Parse raw Nominatim jsonv2 item into GeocodeLocationResult."""
        lat = float(item["lat"])
        lon = float(item["lon"])
        display_name = item.get("display_name", "")
        place_id = item.get("place_id")
        osm_type = item.get("osm_type")
        osm_id = item.get("osm_id")
        confidence = (
            float(item["importance"])
            if "importance" in item and item["importance"] is not None
            else None
        )
        raw_type = item.get("type") or item.get("category")

        bounding_box = None
        raw_bbox = item.get("boundingbox")
        if raw_bbox and isinstance(raw_bbox, list) and len(raw_bbox) == 4:
            try:
                bounding_box = [float(coord) for coord in raw_bbox]
            except (ValueError, TypeError):
                bounding_box = None

        raw_addr = item.get("address")
        address = self._parse_address(raw_addr) if isinstance(raw_addr, dict) else None

        return GeocodeLocationResult(
            latitude=lat,
            longitude=lon,
            display_name=display_name,
            place_id=place_id,
            osm_type=osm_type,
            osm_id=osm_id,
            bounding_box=bounding_box,
            address=address,
            confidence=confidence,
            raw_type=raw_type,
        )

    async def search(self, query: str, limit: int = 5) -> list[GeocodeLocationResult]:
        """Search forward geocoding results for a given query string."""
        if not query or not query.strip():
            return []

        limit = max(1, min(limit, 20))
        params: dict[str, Any] = {
            "q": query.strip(),
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
        }
        if self.country_codes:
            params["countrycodes"] = self.country_codes

        url = f"{self.base_url}/search"
        client = await self._get_client()

        try:
            response = await client.get(
                url,
                params=params,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            logger.warning("Nominatim forward search timed out: %s", exc)
            raise GeocodingProviderUnavailableError(
                "Timeout al consultar el proveedor de geocodificación Nominatim."
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                logger.warning("Nominatim rate limit exceeded (429): %s", exc)
                raise GeocodingRateLimitError(
                    "Límite de solicitudes de Nominatim alcanzado."
                ) from exc
            logger.warning(
                "Nominatim HTTP status error %s: %s",
                exc.response.status_code,
                exc,
            )
            raise GeocodingProviderUnavailableError(
                f"Error HTTP del proveedor Nominatim: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("Nominatim network request error: %s", exc)
            raise GeocodingProviderUnavailableError(
                "Error de conexión con el proveedor Nominatim."
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error during Nominatim geocoding: %s", exc)
            raise GeocodingProviderUnavailableError(
                "Error inesperado al consultar el proveedor de geocodificación."
            ) from exc

        if not isinstance(data, list):
            return []

        results: list[GeocodeLocationResult] = []
        for item in data:
            try:
                result = self._parse_item(item)
                results.append(result)
            except Exception as exc:
                logger.debug("Skipping unparseable Nominatim search item: %s", exc)
                continue

        return results

    async def reverse(self, latitude: float, longitude: float) -> GeocodeLocationResult | None:
        """Reverse geocode geographic coordinates to a structured location result."""
        lat, lon = validate_coordinates(latitude, longitude)
        params: dict[str, Any] = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "addressdetails": 1,
            "zoom": 18,
        }
        url = f"{self.base_url}/reverse"
        client = await self._get_client()

        try:
            response = await client.get(
                url,
                params=params,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            logger.warning("Nominatim reverse geocoding timed out: %s", exc)
            raise GeocodingProviderUnavailableError(
                "Timeout al consultar el proveedor de geocodificación Nominatim."
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                logger.warning("Nominatim rate limit exceeded (429): %s", exc)
                raise GeocodingRateLimitError(
                    "Límite de solicitudes de Nominatim alcanzado."
                ) from exc
            logger.warning(
                "Nominatim reverse HTTP status error %s: %s",
                exc.response.status_code,
                exc,
            )
            raise GeocodingProviderUnavailableError(
                f"Error HTTP del proveedor Nominatim: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("Nominatim reverse network request error: %s", exc)
            raise GeocodingProviderUnavailableError(
                "Error de conexión con el proveedor Nominatim."
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error during Nominatim reverse geocoding: %s", exc)
            raise GeocodingProviderUnavailableError(
                "Error inesperado al consultar el proveedor de geocodificación."
            ) from exc

        if not isinstance(data, dict):
            return None

        # Check for Nominatim error response (e.g. {"error": "Unable to geocode"})
        if "error" in data:
            return None

        try:
            return self._parse_item(data)
        except Exception as exc:
            logger.warning("Failed to parse Nominatim reverse result: %s", exc)
            return None
