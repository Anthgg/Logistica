"""Inventory movement source adapter registry.

The registry lists which source adapters are enabled in Phase 044 and
provides a single entry point to obtain a fresh instance of a given
adapter. Each adapter implements the
``InventoryMovementSourceAdapter`` protocol below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol
from uuid import UUID

from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    ADAPTER_VERSION,
    DISABLED_MOVEMENT_TYPES,
    ENABLED_ADAPTERS,
)


@dataclass(frozen=True)
class PreparedMovement:
    """Output produced by an adapter before posting."""

    movement_type: str
    movement_family: str
    reason_code: str
    occurred_at: Any
    lines: list[Mapping[str, Any]]
    source_references: list[Mapping[str, Any]]
    payload_hash: str
    idempotency_key: str


class InventoryMovementSourceAdapter(Protocol):
    adapter_name: str
    adapter_version: str
    enabled: bool

    def validate_source(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> None: ...

    def build(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> PreparedMovement: ...


class InventoryMovementSourceRegistry:
    """Explicit registry that rejects unknown and disabled source adapters."""

    def __init__(self, adapters: Iterable[InventoryMovementSourceAdapter] = ()) -> None:
        self._adapters: dict[str, InventoryMovementSourceAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: InventoryMovementSourceAdapter) -> None:
        if adapter.adapter_name in self._adapters:
            raise ValueError(f"Adapter {adapter.adapter_name!r} is already registered.")
        self._adapters[adapter.adapter_name] = adapter

    def get(self, adapter_name: str) -> InventoryMovementSourceAdapter:
        from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
            InventoryMovementSourceNotAuthorized,
        )

        adapter = self._adapters.get(adapter_name)
        if adapter is None or not adapter.enabled:
            raise InventoryMovementSourceNotAuthorized(
                f"Source adapter {adapter_name!r} is not enabled in Phase 044."
            )
        return adapter

    def prepare(
        self,
        *,
        adapter_name: str,
        organization_id: UUID,
        payload: Mapping[str, Any],
    ) -> PreparedMovement:
        adapter = self.get(adapter_name)
        adapter.validate_source(organization_id=organization_id, payload=payload)
        return adapter.build(organization_id=organization_id, payload=payload)

    def enabled_names(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, adapter in self._adapters.items() if adapter.enabled))


def is_adapter_enabled(adapter_name: str) -> bool:
    return adapter_name in ENABLED_ADAPTERS


def is_movement_type_disabled(movement_type: str) -> bool:
    return movement_type in DISABLED_MOVEMENT_TYPES


def default_adapter_version() -> str:
    return ADAPTER_VERSION


def list_enabled_adapters() -> tuple[str, ...]:
    return tuple(sorted(ENABLED_ADAPTERS))


def list_supported_movement_types() -> tuple[str, ...]:
    return tuple(
        sorted(
            m
            for m in __import__(
                "app.modules.logistics.inventory.ledger.domain.value_objects.enums",
                fromlist=["MovementType"],
            ).MovementType
            if m not in DISABLED_MOVEMENT_TYPES
        )
    )
