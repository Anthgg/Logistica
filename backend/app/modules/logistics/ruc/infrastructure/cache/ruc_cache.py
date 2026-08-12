"""Versioned RUC lookup cache (Phase 026).

Namespace format: `ruc:{dataset_version_id}:{normalized_RUC}`
Supports L1 memory cache and negative caching with configurable TTL.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class RucLookupCache:
    """In-memory L1 cache with namespace versioning and negative caching support."""

    POSITIVE_TTL_SECONDS = 3600  # 1 hour
    NEGATIVE_TTL_SECONDS = 300   # 5 minutes
    MAX_LOCAL_ITEMS = 5000

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._negative_hits = 0

    def _build_key(self, dataset_version_id: str, normalized_ruc: str) -> str:
        return f"ruc:{dataset_version_id}:{normalized_ruc}"

    def get(self, dataset_version_id: str, normalized_ruc: str) -> tuple[Optional[Dict[str, Any]], str]:
        """Returns (payload, cache_status). cache_status: HIT_L1, MISS, NEGATIVE_HIT."""
        key = self._build_key(dataset_version_id, normalized_ruc)
        entry = self._store.get(key)

        if not entry:
            self._misses += 1
            return None, "MISS"

        now = datetime.now(timezone.utc).timestamp()
        if now > entry["expires_at"]:
            del self._store[key]
            self._misses += 1
            return None, "MISS"

        if entry.get("is_negative"):
            self._negative_hits += 1
            return None, "NEGATIVE_HIT"

        self._hits += 1
        return entry["payload"], "HIT_L1"

    def set(self, dataset_version_id: str, normalized_ruc: str, payload: Dict[str, Any], ttl_seconds: int = POSITIVE_TTL_SECONDS):
        if len(self._store) >= self.MAX_LOCAL_ITEMS:
            # Evict oldest entry
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k]["created_at"])
            del self._store[oldest_key]

        key = self._build_key(dataset_version_id, normalized_ruc)
        now = datetime.now(timezone.utc).timestamp()
        self._store[key] = {
            "payload": payload,
            "is_negative": False,
            "created_at": now,
            "expires_at": now + ttl_seconds,
        }

    def set_negative(self, dataset_version_id: str, normalized_ruc: str, ttl_seconds: int = NEGATIVE_TTL_SECONDS):
        key = self._build_key(dataset_version_id, normalized_ruc)
        now = datetime.now(timezone.utc).timestamp()
        self._store[key] = {
            "payload": None,
            "is_negative": True,
            "created_at": now,
            "expires_at": now + ttl_seconds,
        }

    def invalidate_dataset(self, dataset_version_id: str):
        prefix = f"ruc:{dataset_version_id}:"
        keys_to_del = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_del:
            del self._store[k]

    def clear(self):
        self._store.clear()

    def get_metrics(self) -> Dict[str, int]:
        return {
            "total_cached": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "negative_hits": self._negative_hits,
        }


# Global L1 instance
ruc_cache = RucLookupCache()
