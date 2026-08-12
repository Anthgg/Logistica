"""InventoryPositionService — dimension management for the ledger.

InventoryPosition defines a *dimension*, never a quantity. It is computed
deterministically from the components that fully describe a dimension:

* organization
* branch
* warehouse (optional for external boundaries)
* warehouse_location (optional for staging / transit)
* product
* product_version (optional, when known)
* availability_state
* quality_state
* transit_state
* damage_state
* expiration_state
* ownership_type / owner_business_partner_id
* tracking_reference_type / tracking_reference_hash
* handling_unit_reference_hash

The dimension_key is a SHA-256 hex over the canonical JSON of the
dimension components. Equal positions reuse the same row.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    AvailabilityState,
    BoundaryType,
    DamageState,
    ExpirationState,
    QualityState,
    TransitState,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryPositionModel,
)


@dataclass(frozen=True)
class PositionDimension:
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID | None
    warehouse_location_id: UUID | None
    boundary_type: BoundaryType
    product_id: UUID
    product_version_id: UUID | None
    ownership_type: str
    owner_business_partner_id: UUID | None
    availability_state: AvailabilityState
    quality_state: QualityState
    transit_state: TransitState
    damage_state: DamageState
    expiration_state: ExpirationState
    tracking_reference_type: str | None = None
    tracking_reference_hash: str | None = None
    handling_unit_reference_hash: str | None = None


def compute_dimension_key(dim: PositionDimension) -> str:
    payload = {
        "organization_id": str(dim.organization_id),
        "branch_id": str(dim.branch_id),
        "warehouse_id": str(dim.warehouse_id) if dim.warehouse_id else None,
        "warehouse_location_id": (
            str(dim.warehouse_location_id) if dim.warehouse_location_id else None
        ),
        "boundary_type": dim.boundary_type.value,
        "product_id": str(dim.product_id),
        "product_version_id": (
            str(dim.product_version_id) if dim.product_version_id else None
        ),
        "ownership_type": dim.ownership_type,
        "owner_business_partner_id": (
            str(dim.owner_business_partner_id) if dim.owner_business_partner_id else None
        ),
        "availability_state": dim.availability_state.value,
        "quality_state": dim.quality_state.value,
        "transit_state": dim.transit_state.value,
        "damage_state": dim.damage_state.value,
        "expiration_state": dim.expiration_state.value,
        "tracking_reference_type": dim.tracking_reference_type,
        "tracking_reference_hash": dim.tracking_reference_hash,
        "handling_unit_reference_hash": dim.handling_unit_reference_hash,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class InventoryPositionService:
    """Get-or-create position rows by deterministic dimension key."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def resolve(self, dim: PositionDimension) -> InventoryPositionModel:
        dimension_key = compute_dimension_key(dim)
        stmt = select(InventoryPositionModel).where(
            InventoryPositionModel.organization_id == dim.organization_id,
            InventoryPositionModel.dimension_key == dimension_key,
        )
        position = self._db.scalars(stmt).first()
        if position is not None:
            return position
        position = InventoryPositionModel(
            organization_id=dim.organization_id,
            branch_id=dim.branch_id,
            warehouse_id=dim.warehouse_id,
            warehouse_location_id=dim.warehouse_location_id,
            boundary_type=dim.boundary_type.value,
            product_id=dim.product_id,
            product_version_id=dim.product_version_id,
            ownership_type=dim.ownership_type,
            owner_business_partner_id=dim.owner_business_partner_id,
            availability_state=dim.availability_state.value,
            quality_state=dim.quality_state.value,
            transit_state=dim.transit_state.value,
            damage_state=dim.damage_state.value,
            expiration_state=dim.expiration_state.value,
            tracking_reference_type=dim.tracking_reference_type,
            tracking_reference_hash=dim.tracking_reference_hash,
            handling_unit_reference_hash=dim.handling_unit_reference_hash,
            dimension_key=dimension_key,
        )
        self._db.add(position)
        self._db.flush()
        return position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INTERNAL_BOUNDARIES: frozenset[str] = frozenset(
    {
        BoundaryType.INTERNAL_LOCATION.value,
        BoundaryType.INTERNAL_STAGING.value,
        BoundaryType.INTERNAL_QUARANTINE.value,
        BoundaryType.INTERNAL_TRANSIT.value,
    }
)


def is_internal_boundary(boundary_type: str) -> bool:
    return boundary_type in INTERNAL_BOUNDARIES
