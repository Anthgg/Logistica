"""Asynchronous rate limiter for enforcing upstream API rate limits."""

import asyncio
import time


class AsyncRateLimiter:
    """Async interval limiter ensuring minimum elapsed time between consecutive upstream calls.

    Complies with OpenStreetMap Nominatim usage policy (strictly <= 1 request per second).
    """

    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        self._min_interval = max(0.0, float(min_interval_seconds))
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def min_interval_seconds(self) -> float:
        return self._min_interval

    async def acquire(self) -> None:
        """Wait if necessary to ensure minimum interval has elapsed since the previous request."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                delay = self._min_interval - elapsed
                await asyncio.sleep(delay)
            self._last_request_time = time.monotonic()

    def reset(self) -> None:
        """Reset internal timestamp tracker."""
        self._last_request_time = 0.0
