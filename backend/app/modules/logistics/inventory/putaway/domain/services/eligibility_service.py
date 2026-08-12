"""Phase 043 — Source eligibility evaluation service."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from ..errors import PutawaySourceNotEligible


@dataclass
class SourceEligibility:
    eligible: bool
    source_allocation_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    quality_status: str
    disposition: str
    reasons: list[str]


class EligibilityService:
    """Evaluates whether a source allocation is eligible for putaway."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def evaluate(
        self,
        source_allocation_id: UUID,
        *,
        required_quality_status: str | None = None,
        required_disposition: str | None = None,
    ) -> SourceEligibility:
        from ...inbound.quality_quarantine.infrastructure.persistence.models import (
            InboundInventoryDispositionAllocationModel,
        )

        allocation = self._db.get(
            InboundInventoryDispositionAllocationModel, source_allocation_id
        )
        if allocation is None:
            raise PutawaySourceNotEligible(
                f"Source allocation {source_allocation_id} not found"
            )

        reasons = []

        if allocation.allocation_status == "SUPERSEDED":
            reasons.append("Allocation has been superseded")

        if allocation.allocation_status == "CANCELLED":
            reasons.append("Allocation has been cancelled")

        if allocation.availability_class == "BLOCKED":
            reasons.append("Product is blocked")

        if allocation.quality_status == "QUARANTINED":
            reasons.append("Product is in quarantine")

        if allocation.quality_status == "REJECTED":
            reasons.append("Product has been rejected")

        if required_quality_status and allocation.quality_status != required_quality_status:
            reasons.append(
                f"Quality status {allocation.quality_status} does not match "
                f"required {required_quality_status}"
            )

        if required_disposition and allocation.disposition != required_disposition:
            reasons.append(
                f"Disposition {allocation.disposition} does not match "
                f"required {required_disposition}"
            )

        eligible = len(reasons) == 0

        return SourceEligibility(
            eligible=eligible,
            source_allocation_id=allocation.id,
            product_id=allocation.product_id,
            quantity=allocation.quantity,
            unit_id=allocation.unit_id,
            base_quantity=allocation.base_quantity,
            quality_status=allocation.quality_status,
            disposition=allocation.disposition,
            reasons=reasons,
        )

    def require_eligible(
        self,
        source_allocation_id: UUID,
        *,
        required_quality_status: str | None = None,
        required_disposition: str | None = None,
    ) -> SourceEligibility:
        result = self.evaluate(
            source_allocation_id,
            required_quality_status=required_quality_status,
            required_disposition=required_disposition,
        )
        if not result.eligible:
            raise PutawaySourceNotEligible(
                f"Source allocation {source_allocation_id} not eligible: "
                + "; ".join(result.reasons)
            )
        return result
