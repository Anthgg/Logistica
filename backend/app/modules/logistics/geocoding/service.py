"""High-level geocoding service orchestrating provider, caching, rate limiting, and UBIGEO enrichment."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.modules.logistics.geocoding.base import (
    GeocodeLocationResult,
    GeocodingProvider,
    validate_coordinates,
)
from app.modules.logistics.geocoding.cache import GeocodingLRUCache
from app.modules.logistics.geocoding.rate_limiter import AsyncRateLimiter
from app.modules.logistics.geography.service import GeographyService

logger = logging.getLogger(__name__)


class GeocodingService:
    """Application domain service for geocoding address queries and reverse coordinates."""

    def __init__(
        self,
        provider: GeocodingProvider,
        cache: GeocodingLRUCache | None = None,
        rate_limiter: AsyncRateLimiter | None = None,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.rate_limiter = rate_limiter

    def enrich_query_with_ubigeo(
        self,
        address: str,
        district_name: str | None = None,
        province_name: str | None = None,
        department_name: str | None = None,
    ) -> str:
        """Enrich a street address with administrative hierarchy names for high-precision geocoding.

        Format: `<address>, <district>, <province>, <department>, Perú`
        """
        clean_addr = (address or "").strip()
        parts: list[str] = [clean_addr] if clean_addr else []

        if district_name and district_name.strip():
            d = district_name.strip()
            if d not in parts:
                parts.append(d)

        if province_name and province_name.strip():
            p = province_name.strip()
            if p not in parts:
                parts.append(p)

        if department_name and department_name.strip():
            dept = department_name.strip()
            if dept not in parts:
                parts.append(dept)

        parts.append("Perú")
        return ", ".join(parts)

    async def search_address(
        self,
        address: str,
        ubigeo_code: str | None = None,
        db: Session | None = None,
        limit: int = 5,
    ) -> list[GeocodeLocationResult]:
        """Search forward geocoding with optional UBIGEO enrichment, caching, and rate limiting."""
        if not address or not address.strip():
            return []

        clean_address = address.strip()
        query = clean_address

        if ubigeo_code and db is not None:
            try:
                hierarchy = GeographyService.resolve_ubigeo(db, ubigeo_code.strip())
                if hierarchy:
                    query = self.enrich_query_with_ubigeo(
                        clean_address,
                        district_name=hierarchy.district_name,
                        province_name=hierarchy.province_name,
                        department_name=hierarchy.department_name,
                    )
                else:
                    query = self.enrich_query_with_ubigeo(clean_address)
            except Exception as exc:
                logger.warning("Failed to resolve UBIGEO %s: %s", ubigeo_code, exc)
                query = self.enrich_query_with_ubigeo(clean_address)
        else:
            query = self.enrich_query_with_ubigeo(clean_address)

        # Check Cache
        cache_key = None
        if self.cache is not None:
            cache_key = self.cache.make_search_key(query, limit=limit)
            cached_results = self.cache.get(cache_key)
            if cached_results is not None:
                logger.debug("Geocoding cache hit for query: %s", query)
                return cached_results

        # Rate limiter
        if self.rate_limiter is not None:
            await self.rate_limiter.acquire()

        # Call Provider
        results = await self.provider.search(query, limit=limit)

        # Store in Cache
        if self.cache is not None and cache_key is not None:
            self.cache.set(cache_key, results)

        return results

    async def reverse_coords(
        self,
        latitude: float,
        longitude: float,
    ) -> GeocodeLocationResult | None:
        """Reverse geocode coordinates with caching and rate limiting."""
        lat, lon = validate_coordinates(latitude, longitude)

        # Check Cache
        cache_key = None
        if self.cache is not None:
            cache_key = self.cache.make_reverse_key(lat, lon)
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Geocoding reverse cache hit for (%s, %s)", lat, lon)
                return cached_result

        # Rate limiter
        if self.rate_limiter is not None:
            await self.rate_limiter.acquire()

        # Call Provider
        result = await self.provider.reverse(lat, lon)

        # Store in Cache
        if self.cache is not None and cache_key is not None and result is not None:
            self.cache.set(cache_key, result)

        return result
