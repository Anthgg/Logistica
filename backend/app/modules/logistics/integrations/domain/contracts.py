"""Integrations domain — contracts for external service adapters.

Defines common patterns for timeout, retries, circuit breaking and
error normalisation that all external integrations should follow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class IntegrationProvider(StrEnum):
    SUNAT = "sunat"
    SUNARP = "sunarp"
    MTC = "mtc"
    SBS = "sbs"
    GEOCODING = "geocoding"
    SMS = "sms"
    OTP = "otp"
    EMAIL = "email"
    STORAGE = "storage"
    NOTIFICATIONS = "notifications"


@dataclass(frozen=True)
class IntegrationRequest:
    """Base request for any external integration."""
    provider: IntegrationProvider
    operation: str
    payload: dict[str, object]
    timeout_seconds: int = 30
    max_retries: int = 3


@dataclass(frozen=True)
class IntegrationResponse:
    """Normalised response from an external integration."""
    provider: IntegrationProvider
    operation: str
    success: bool
    queried_at: datetime
    data: dict[str, object] | None = None
    error: str | None = None
    source: str | None = None
    correlation_id: str | None = None


class IntegrationAdapter(Protocol):
    """Base protocol for all external integration adapters."""

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse: ...


class IntegrationRegistry(Protocol):
    """Looks up the correct adapter for a given provider."""

    def get_adapter(self, provider: IntegrationProvider) -> IntegrationAdapter | None: ...


class IntegrationCache(Protocol):
    """Optional cache for integration responses."""

    async def get(self, key: str) -> dict[str, object] | None: ...

    async def set(self, key: str, value: dict[str, object], ttl_seconds: int) -> None: ...