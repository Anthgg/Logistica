"""Thread-safe bounded LRU memory cache with TTL for geocoding results."""

from collections import OrderedDict
import threading
import time
from typing import Any


class GeocodingLRUCache:
    """Thread-safe in-memory LRU cache with time-to-live (TTL) expiration."""

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 1000) -> None:
        self._ttl_seconds = max(1, int(ttl_seconds))
        self._max_entries = max(1, int(max_entries))
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0

    @property
    def ttl_seconds(self) -> int:
        return self._ttl_seconds

    @property
    def max_entries(self) -> int:
        return self._max_entries

    def get(self, key: str) -> Any | None:
        """Retrieve an item from the cache if present and unexpired.

        Updates LRU access order on cache hit.
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            created_at, value = self._cache[key]
            if (time.monotonic() - created_at) > self._ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None

            # Mark as recently used
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """Store an item in the cache, evicting the least recently used item if at capacity."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                while len(self._cache) >= self._max_entries:
                    self._cache.popitem(last=False)

            self._cache[key] = (time.monotonic(), value)

    def clear(self) -> None:
        """Clear all entries and reset cache statistics."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def size(self) -> int:
        """Return the current number of items in the cache."""
        with self._lock:
            return len(self._cache)

    def stats(self) -> dict[str, int]:
        """Return operational cache metrics."""
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "max_entries": self._max_entries,
                "ttl_seconds": self._ttl_seconds,
            }

    @staticmethod
    def make_search_key(query: str, limit: int = 5) -> str:
        """Generate canonical cache key for forward geocoding search queries."""
        normalized_query = " ".join((query or "").strip().lower().split())
        return f"search:{normalized_query}:{limit}"

    @staticmethod
    def make_reverse_key(latitude: float, longitude: float) -> str:
        """Generate canonical cache key for reverse geocoding coordinates.

        Coordinates are rounded to 5 decimal places (~1.1m precision at the equator).
        """
        lat_rounded = f"{round(float(latitude), 5):.5f}"
        lon_rounded = f"{round(float(longitude), 5):.5f}"
        return f"reverse:{lat_rounded}:{lon_rounded}"
