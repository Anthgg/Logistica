"""Source adapters that materialize Phase 042 / 043 events into MOV postings.

Each adapter implements the ``InventoryMovementSourceAdapter`` protocol
declared in :mod:`source_registry`. The adapters are stateless and
deterministic: they take a payload describing a source event and produce
a ``PreparedMovement`` ready for the posting service.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryMovementSourceConflict,
    InventoryMovementSourceNotAuthorized,
    InventoryMovementSourceNotFound,
)
from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
    hash_payload,
)
from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
    PreparedMovement,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    ADAPTER_TO_MOVEMENT_TYPE,
    ADAPTER_VERSION,
    MovementFamily,
    MovementType,
    SourceAdapterName,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _require(payload: Mapping[str, Any], key: str) -> Any:
    if key not in payload or payload[key] in (None, ""):
        raise InventoryMovementSourceNotFound(
            f"Source payload missing required key {key!r}.",
        )
    return payload[key]


# ---------------------------------------------------------------------------
# Phase 042 — Quality adapters
# ---------------------------------------------------------------------------


class _BaseQualityAdapter:
    adapter_version = ADAPTER_VERSION

    def __init__(
        self, adapter_name: str, movement_type: str, movement_family: str, reason_code: str
    ) -> None:
        self.adapter_name = adapter_name
        self._movement_type = movement_type
        self._movement_family = movement_family
        self._reason_code = reason_code

    @property
    def enabled(self) -> bool:
        return True

    def validate_source(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> None:
        if "source_event_id" not in payload or not payload.get("source_event_id"):
            raise InventoryMovementSourceConflict(
                "Source payload missing source_event_id.",
            )
        if "source_hash" not in payload or not payload.get("source_hash"):
            raise InventoryMovementSourceConflict(
                "Source payload missing source_hash.",
            )

    def build(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> PreparedMovement:
        product_id = _require(payload, "product_id")
        product_version_id = payload.get("product_version_id")
        unit_id = _require(payload, "unit_id")
        base_unit_id = payload.get("base_unit_id", unit_id)
        quantity = _decimal(_require(payload, "quantity"))
        base_quantity = _decimal(payload.get("base_quantity", quantity))
        source_position_id = payload.get("source_position_id")
        destination_position_id = payload.get("destination_position_id")
        source_boundary_kind = payload.get("source_external_boundary_kind")
        destination_boundary_kind = payload.get("destination_external_boundary_kind")
        idempotency_key = str(_require(payload, "source_event_id"))

        line = {
            "line_number": 1,
            "product_id": str(product_id),
            "product_version_id": str(product_version_id) if product_version_id else None,
            "product_snapshot": payload.get("product_snapshot") or {},
            "quantity": str(quantity),
            "unit_id": str(unit_id),
            "base_quantity": str(base_quantity),
            "base_unit_id": str(base_unit_id),
            "source_position_id": str(source_position_id) if source_position_id else None,
            "destination_position_id": str(destination_position_id)
            if destination_position_id
            else None,
            "source_external_boundary_kind": source_boundary_kind,
            "destination_external_boundary_kind": destination_boundary_kind,
            "quantity_direction": self._direction(),
            "reason_code": self._reason_code,
            "metadata": payload.get("metadata") or {},
        }
        source_ref = {
            "source_system": "QUALITY",
            "source_module": "phase_042",
            "source_event_type": self.adapter_name,
            "source_event_id": str(payload["source_event_id"]),
            "source_event_version": int(payload.get("source_event_version", 1)),
            "source_document_type": payload.get("source_document_type"),
            "source_document_id": payload.get("source_document_id"),
            "source_document_code": payload.get("source_document_code"),
            "source_entity_type": str(payload.get("source_entity_type", "QualityDispositionEvent")),
            "source_entity_id": str(payload.get("source_entity_id", payload["source_event_id"])),
            "source_hash": str(payload["source_hash"]),
            "source_occurred_at": payload.get("source_occurred_at"),
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
        }
        return PreparedMovement(
            movement_type=self._movement_type,
            movement_family=self._movement_family,
            reason_code=self._reason_code,
            occurred_at=payload.get("occurred_at"),
            lines=[line],
            source_references=[source_ref],
            payload_hash=hash_payload(payload),
            idempotency_key=idempotency_key,
        )

    def _direction(self) -> str:  # pragma: no cover - override
        return "STATE_CHANGE"


@dataclass
class QualityQuarantineAppliedAdapter(_BaseQualityAdapter):
    def __init__(self) -> None:
        super().__init__(
            adapter_name=SourceAdapterName.QUALITY_QUARANTINE_APPLIED.value,
            movement_type=ADAPTER_TO_MOVEMENT_TYPE[SourceAdapterName.QUALITY_QUARANTINE_APPLIED],
            movement_family=MovementFamily.QUALITY_TRANSITION,
            reason_code="QUARANTINE_APPLIED",
        )


@dataclass
class QualityApprovedAdapter(_BaseQualityAdapter):
    def __init__(self) -> None:
        super().__init__(
            adapter_name=SourceAdapterName.QUALITY_APPROVED.value,
            movement_type=ADAPTER_TO_MOVEMENT_TYPE[SourceAdapterName.QUALITY_APPROVED],
            movement_family=MovementFamily.INBOUND,
            reason_code="QUALITY_RELEASE_TO_STAGING",
        )

    def _direction(self) -> str:
        return "STATE_CHANGE"


@dataclass
class QuarantineReleasedAdapter(_BaseQualityAdapter):
    def __init__(self) -> None:
        super().__init__(
            adapter_name=SourceAdapterName.QUARANTINE_RELEASED.value,
            movement_type=ADAPTER_TO_MOVEMENT_TYPE[SourceAdapterName.QUARANTINE_RELEASED],
            movement_family=MovementFamily.QUALITY_TRANSITION,
            reason_code="QUARANTINE_RELEASED",
        )


@dataclass
class QualityRejectedAdapter(_BaseQualityAdapter):
    def __init__(self) -> None:
        super().__init__(
            adapter_name=SourceAdapterName.QUALITY_REJECTED.value,
            movement_type=ADAPTER_TO_MOVEMENT_TYPE[SourceAdapterName.QUALITY_REJECTED],
            movement_family=MovementFamily.QUALITY_TRANSITION,
            reason_code="QUALITY_REJECTED",
        )


@dataclass
class DispositionSplitAdapter(_BaseQualityAdapter):
    def __init__(self) -> None:
        super().__init__(
            adapter_name=SourceAdapterName.DISPOSITION_SPLIT.value,
            movement_type=ADAPTER_TO_MOVEMENT_TYPE[SourceAdapterName.DISPOSITION_SPLIT],
            movement_family=MovementFamily.INBOUND,
            reason_code="DISPOSITION_SPLIT",
        )

    def build(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> PreparedMovement:
        # A split must not add or remove quantity; it only re-states
        # the existing allocation across two dimensions.
        children = payload.get("children") or []
        if not isinstance(children, list) or not children:
            raise InventoryMovementSourceConflict(
                "Disposition split payload requires at least one child.",
            )
        lines = []
        for idx, child in enumerate(children, start=1):
            lines.append(
                {
                    "line_number": idx,
                    "product_id": str(child["product_id"]),
                    "product_version_id": str(child.get("product_version_id"))
                    if child.get("product_version_id")
                    else None,
                    "product_snapshot": child.get("product_snapshot") or {},
                    "quantity": str(_decimal(child["quantity"])),
                    "unit_id": str(child["unit_id"]),
                    "base_quantity": str(_decimal(child.get("base_quantity", child["quantity"]))),
                    "base_unit_id": str(child.get("base_unit_id", child["unit_id"])),
                    "source_position_id": str(child.get("source_position_id"))
                    if child.get("source_position_id")
                    else None,
                    "destination_position_id": str(child.get("destination_position_id"))
                    if child.get("destination_position_id")
                    else None,
                    "source_external_boundary_kind": child.get("source_external_boundary_kind"),
                    "destination_external_boundary_kind": child.get(
                        "destination_external_boundary_kind"
                    ),
                    "quantity_direction": "TRANSFER",
                    "reason_code": "DISPOSITION_SPLIT",
                    "metadata": child.get("metadata") or {},
                }
            )
        source_ref = {
            "source_system": "QUALITY",
            "source_module": "phase_042",
            "source_event_type": self.adapter_name,
            "source_event_id": str(payload["source_event_id"]),
            "source_event_version": int(payload.get("source_event_version", 1)),
            "source_entity_type": "InventoryDispositionSplit",
            "source_entity_id": str(payload.get("source_entity_id", payload["source_event_id"])),
            "source_hash": str(payload["source_hash"]),
            "source_occurred_at": payload.get("source_occurred_at"),
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
        }
        return PreparedMovement(
            movement_type=self._movement_type,
            movement_family=self._movement_family,
            reason_code=self._reason_code,
            occurred_at=payload.get("occurred_at"),
            lines=lines,
            source_references=[source_ref],
            payload_hash=hash_payload(payload),
            idempotency_key=str(payload["source_event_id"]),
        )


# ---------------------------------------------------------------------------
# Phase 043 — Putaway adapter
# ---------------------------------------------------------------------------


@dataclass
class PutawayCompletedAdapter:
    adapter_name: str = SourceAdapterName.PUTAWAY_COMPLETED.value
    adapter_version: str = ADAPTER_VERSION
    enabled: bool = True

    def validate_source(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> None:
        if not payload.get("source_event_id"):
            raise InventoryMovementSourceConflict(
                "Putaway payload missing source_event_id.",
            )
        if not payload.get("source_hash"):
            raise InventoryMovementSourceConflict(
                "Putaway payload missing source_hash.",
            )

    def build(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> PreparedMovement:
        destinations = payload.get("destinations") or []
        if not isinstance(destinations, list) or not destinations:
            raise InventoryMovementSourceConflict(
                "Putaway payload requires a non-empty destinations list.",
            )
        lines = []
        for idx, dest in enumerate(destinations, start=1):
            lines.append(
                {
                    "line_number": idx,
                    "product_id": str(dest["product_id"]),
                    "product_version_id": str(dest.get("product_version_id"))
                    if dest.get("product_version_id")
                    else None,
                    "product_snapshot": dest.get("product_snapshot") or {},
                    "quantity": str(_decimal(dest["quantity"])),
                    "unit_id": str(dest["unit_id"]),
                    "base_quantity": str(_decimal(dest.get("base_quantity", dest["quantity"]))),
                    "base_unit_id": str(dest.get("base_unit_id", dest["unit_id"])),
                    "source_position_id": str(dest.get("source_position_id"))
                    if dest.get("source_position_id")
                    else None,
                    "destination_position_id": str(dest.get("destination_position_id"))
                    if dest.get("destination_position_id")
                    else None,
                    "source_external_boundary_kind": dest.get("source_external_boundary_kind"),
                    "destination_external_boundary_kind": dest.get(
                        "destination_external_boundary_kind"
                    ),
                    "quantity_direction": "TRANSFER",
                    "reason_code": "PUTAWAY_COMPLETED",
                    "metadata": dest.get("metadata") or {},
                }
            )
        source_ref = {
            "source_system": "PUTAWAY",
            "source_module": "phase_043",
            "source_event_type": self.adapter_name,
            "source_event_id": str(payload["source_event_id"]),
            "source_event_version": int(payload.get("source_event_version", 1)),
            "source_entity_type": "PutawayPlacementConfirmation",
            "source_entity_id": str(payload.get("source_entity_id", payload["source_event_id"])),
            "source_hash": str(payload["source_hash"]),
            "source_occurred_at": payload.get("source_occurred_at"),
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
        }
        return PreparedMovement(
            movement_type=MovementType.PUTAWAY_COMPLETED.value,
            movement_family=MovementFamily.INBOUND,
            reason_code="PUTAWAY_COMPLETED",
            occurred_at=payload.get("occurred_at"),
            lines=lines,
            source_references=[source_ref],
            payload_hash=hash_payload(payload),
            idempotency_key=str(payload["source_event_id"]),
        )


# ---------------------------------------------------------------------------
# Explicitly disabled future sources (Phase 045+)
# ---------------------------------------------------------------------------


@dataclass
class _DisabledFutureAdapter:
    adapter_name: str
    adapter_version: str = ADAPTER_VERSION
    enabled: bool = False

    def validate_source(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> None:
        raise InventoryMovementSourceNotAuthorized(
            f"Source adapter {self.adapter_name!r} is reserved for a future phase."
        )

    def build(self, *, organization_id: UUID, payload: Mapping[str, Any]) -> PreparedMovement:
        raise InventoryMovementSourceNotAuthorized(
            f"Source adapter {self.adapter_name!r} is reserved for a future phase."
        )


class FutureAdjustmentMovementAdapter(_DisabledFutureAdapter):
    def __init__(self) -> None:
        super().__init__("FUTURE_ADJUSTMENT")


class FutureCountMovementAdapter(_DisabledFutureAdapter):
    def __init__(self) -> None:
        super().__init__("FUTURE_COUNT")


class FutureTransferMovementAdapter(_DisabledFutureAdapter):
    def __init__(self) -> None:
        super().__init__("FUTURE_TRANSFER")


# ---------------------------------------------------------------------------
# Registry helper
# ---------------------------------------------------------------------------


def build_default_registry() -> dict[str, "InventoryMovementSourceAdapterLike"]:
    return {
        SourceAdapterName.QUALITY_QUARANTINE_APPLIED.value: QualityQuarantineAppliedAdapter(),
        SourceAdapterName.QUALITY_APPROVED.value: QualityApprovedAdapter(),
        SourceAdapterName.QUARANTINE_RELEASED.value: QuarantineReleasedAdapter(),
        SourceAdapterName.QUALITY_REJECTED.value: QualityRejectedAdapter(),
        SourceAdapterName.DISPOSITION_SPLIT.value: DispositionSplitAdapter(),
        SourceAdapterName.PUTAWAY_COMPLETED.value: PutawayCompletedAdapter(),
    }


class InventoryMovementSourceAdapterLike:
    """Lightweight protocol re-export to avoid circular imports."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover
        raise RuntimeError("Protocol stub; use concrete adapter classes.")
