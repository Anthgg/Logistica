from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import ApplicationError


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        now = monotonic()
        threshold = now - settings.RATE_LIMIT_WINDOW_SECONDS
        with self._lock:
            entries = self._requests[key]
            while entries and entries[0] < threshold:
                entries.popleft()
            if len(entries) >= settings.RATE_LIMIT_REQUESTS:
                raise ApplicationError(
                    "RATE_LIMIT_EXCEEDED",
                    "Demasiadas solicitudes. Inténtelo nuevamente más tarde.",
                    429,
                )
            entries.append(now)


rate_limiter = InMemoryRateLimiter()


class ResearchRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(
        self, request: Request, *, category: str, maximum: int, window_seconds: int
    ) -> None:
        client = request.client.host if request.client else "unknown"
        user_id = getattr(getattr(request.state, "current_user", None), "id", "anonymous")
        key = f"{category}:{user_id}:{client}"
        now = monotonic()
        threshold = now - window_seconds
        with self._lock:
            entries = self._requests[key]
            while entries and entries[0] < threshold:
                entries.popleft()
            if len(entries) >= maximum:
                raise ApplicationError(
                    "RATE_LIMIT_EXCEEDED",
                    "Demasiadas solicitudes para el recolector. Espere e intente nuevamente.",
                    429,
                )
            entries.append(now)


research_rate_limiter = ResearchRateLimiter()


def enforce_auth_rate_limit(request: Request) -> None:
    rate_limiter.check(request)


def enforce_research_start_rate_limit(request: Request) -> None:
    research_rate_limiter.check(
        request, category="research_start", maximum=5, window_seconds=60
    )


def enforce_capture_rate_limit(request: Request) -> None:
    research_rate_limiter.check(
        request, category="facial_capture", maximum=20, window_seconds=60
    )


def enforce_behavior_rate_limit(request: Request) -> None:
    research_rate_limiter.check(
        request, category="behavior_batch", maximum=40, window_seconds=60
    )


def enforce_research_finish_rate_limit(request: Request) -> None:
    research_rate_limiter.check(
        request, category="research_finish", maximum=10, window_seconds=60
    )
