"""Source-backed availability provider.

The source-backed provider validates that the requested quantity exists
in an immutable source of truth (typically an
``InboundInventoryDispositionAllocation`` from Phase 042, an
``OperationalInventoryPlacement`` from Phase 043, a
``QuarantinePlacementConfirmation`` or a ``QuarantineReleaseAuthorization``).

It does NOT compute balances. Until Phase 045 delivers the
``InventoryBalanceAvailabilityProvider`` the project must not permit
generic balance-consuming movements.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryAvailabilityProviderUnavailable,
    InventoryMovementSourceNotFound,
    InventoryMovementQuantityInvalid,
)


@dataclass(frozen=True)
class AvailabilityCheckResult:
    ok: bool
    available_base_quantity: Decimal
    consumed_base_quantity: Decimal
    remaining_base_quantity: Decimal
    source_reference: Mapping[str, object]


class InventoryAvailabilityProvider:
    """Interface contract for availability providers."""

    def get_available_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
    ) -> AvailabilityCheckResult:  # pragma: no cover - interface
        raise NotImplementedError

    def validate_source_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
        requested_base_quantity: Decimal,
    ) -> AvailabilityCheckResult:  # pragma: no cover - interface
        raise NotImplementedError

    def validate_reservation_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
        requested_base_quantity: Decimal,
    ) -> AvailabilityCheckResult:  # pragma: no cover - interface
        raise NotImplementedError

    def validate_transfer_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
        requested_base_quantity: Decimal,
    ) -> AvailabilityCheckResult:  # pragma: no cover - interface
        raise NotImplementedError


class SourceBackedAvailabilityProvider(InventoryAvailabilityProvider):
    """Validates availability against immutable source allocations.

    The current implementation only consults
    ``inbound_inventory_disposition_allocations`` and the operational
    placement projections from Phase 043. Phase 045 will replace it with
    the ledger-derived balance provider.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def _allocation_query(
        self,
        *,
        organization_id: UUID,
        source_entity_id: UUID,
        product_id: UUID,
    ) -> Decimal | None:
        # Lazy import avoids hard-binding the inbound phase 042 models.
        from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import (
            InboundInventoryDispositionAllocationModel,
        )

        stmt = select(InboundInventoryDispositionAllocationModel).where(
            InboundInventoryDispositionAllocationModel.organization_id == organization_id,
            InboundInventoryDispositionAllocationModel.id == source_entity_id,
            InboundInventoryDispositionAllocationModel.product_id == product_id,
        )
        row = self._db.scalars(stmt).first()
        if row is None:
            return None
        return Decimal(row.base_quantity)

    def _placement_query(
        self,
        *,
        organization_id: UUID,
        source_entity_id: UUID,
        product_id: UUID,
    ) -> Decimal | None:
        from app.modules.logistics.inventory.putaway.infrastructure.persistence.models import (
            OperationalInventoryPlacementModel,
        )

        stmt = select(OperationalInventoryPlacementModel).where(
            OperationalInventoryPlacementModel.organization_id == organization_id,
            OperationalInventoryPlacementModel.id == source_entity_id,
            OperationalInventoryPlacementModel.product_id == product_id,
        )
        row = self._db.scalars(stmt).first()
        if row is None:
            return None
        return Decimal(row.base_quantity)

    def get_available_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
    ) -> AvailabilityCheckResult:
        if source_entity_type == "INBOUND_ALLOCATION":
            base = self._allocation_query(
                organization_id=organization_id,
                source_entity_id=source_entity_id,
                product_id=product_id,
            )
        elif source_entity_type == "OPERATIONAL_PLACEMENT":
            base = self._placement_query(
                organization_id=organization_id,
                source_entity_id=source_entity_id,
                product_id=product_id,
            )
        else:
            raise InventoryAvailabilityProviderUnavailable(
                f"Source-backed provider does not support entity type "
                f"{source_entity_type!r} in phase 044.",
            )
        if base is None:
            raise InventoryMovementSourceNotFound(
                "No allocation or placement found for source reference.",
            )
        return AvailabilityCheckResult(
            ok=True,
            available_base_quantity=base,
            consumed_base_quantity=Decimal("0"),
            remaining_base_quantity=base,
            source_reference={"source_entity_type": source_entity_type},
        )

    def validate_source_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
        requested_base_quantity: Decimal,
    ) -> AvailabilityCheckResult:
        result = self.get_available_quantity(
            organization_id=organization_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            product_id=product_id,
        )
        if requested_base_quantity > result.available_base_quantity:
            raise InventoryMovementQuantityInvalid(
                "Requested base quantity exceeds the immutable source allocation.",
            )
        return result

    def validate_reservation_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
        requested_base_quantity: Decimal,
    ) -> AvailabilityCheckResult:
        return self.validate_source_quantity(
            organization_id=organization_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            product_id=product_id,
            requested_base_quantity=requested_base_quantity,
        )

    def validate_transfer_quantity(
        self,
        *,
        organization_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        product_id: UUID,
        requested_base_quantity: Decimal,
    ) -> AvailabilityCheckResult:
        return self.validate_source_quantity(
            organization_id=organization_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            product_id=product_id,
            requested_base_quantity=requested_base_quantity,
        )
