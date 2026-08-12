"""Phase 043 — Capacity profile and projection service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from ..enums import CapacityType, DataQualityStatus
from ...infrastructure.persistence.repositories import (
    WarehouseLocationCapacityProfileRepository,
    PutawayLocationCapacityProjectionRepository,
)


@dataclass
class CapacityEvaluation:
    location_id: UUID
    capacity_profile_id: UUID
    capacity_type: str
    maximum_value: Decimal
    safety_margin_value: Decimal
    operational_occupied: Decimal
    active_reserved: Decimal
    projected_free: Decimal
    has_enough: bool
    data_quality_status: str
    unit_id: UUID


class CapacityService:
    """Manages capacity profiles and projections for putaway locations."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._profile_repo = WarehouseLocationCapacityProfileRepository(db)
        self._projection_repo = PutawayLocationCapacityProjectionRepository(db)

    def evaluate(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        location_id: UUID,
        required_base_quantity: Decimal,
    ) -> CapacityEvaluation | None:
        profiles = self._profile_repo.list_by_location(location_id)

        for profile in profiles:
            projection = self._projection_repo.get_or_none(
                organization_id, warehouse_id, location_id, profile.id
            )

            if projection is None:
                projected_free = profile.maximum_value - profile.safety_margin_value
                data_quality = DataQualityStatus.MISSING_BASELINE.value
                occupied = Decimal("0")
                reserved = Decimal("0")
            else:
                occupied = projection.operational_occupied_value
                reserved = projection.active_reserved_value
                projected_free = projection.projected_free_value
                data_quality = projection.data_quality_status

            has_enough = projected_free >= required_base_quantity

            return CapacityEvaluation(
                location_id=location_id,
                capacity_profile_id=profile.id,
                capacity_type=profile.capacity_type,
                maximum_value=profile.maximum_value,
                safety_margin_value=profile.safety_margin_value,
                operational_occupied=occupied,
                active_reserved=reserved,
                projected_free=projected_free,
                has_enough=has_enough,
                data_quality_status=data_quality,
                unit_id=profile.unit_id,
            )

        return None

    def get_available_capacity(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        location_id: UUID,
    ) -> list[CapacityEvaluation]:
        results = []
        profiles = self._profile_repo.list_by_location(location_id)

        for profile in profiles:
            projection = self._projection_repo.get_or_none(
                organization_id, warehouse_id, location_id, profile.id
            )

            if projection is None:
                projected_free = profile.maximum_value - profile.safety_margin_value
                data_quality = DataQualityStatus.MISSING_BASELINE.value
                occupied = Decimal("0")
                reserved = Decimal("0")
            else:
                occupied = projection.operational_occupied_value
                reserved = projection.active_reserved_value
                projected_free = projection.projected_free_value
                data_quality = projection.data_quality_status

            results.append(CapacityEvaluation(
                location_id=location_id,
                capacity_profile_id=profile.id,
                capacity_type=profile.capacity_type,
                maximum_value=profile.maximum_value,
                safety_margin_value=profile.safety_margin_value,
                operational_occupied=occupied,
                active_reserved=reserved,
                projected_free=projected_free,
                has_enough=projected_free > Decimal("0"),
                data_quality_status=data_quality,
                unit_id=profile.unit_id,
            ))

        return results

    def update_projection(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        location_id: UUID,
        capacity_profile_id: UUID,
        *,
        operational_occupied_delta: Decimal = Decimal("0"),
        active_reserved_delta: Decimal = Decimal("0"),
    ) -> None:
        profile = self._profile_repo.get(capacity_profile_id)
        if not profile:
            return

        projection = self._projection_repo.get_or_none(
            organization_id, warehouse_id, location_id, capacity_profile_id
        )

        now = datetime.now(timezone.utc)

        if projection is None:
            from ...infrastructure.persistence.models import PutawayLocationCapacityProjectionModel
            projection = PutawayLocationCapacityProjectionModel(
                organization_id=organization_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                capacity_profile_id=capacity_profile_id,
                capacity_type=profile.capacity_type,
                maximum_value=profile.maximum_value,
                safety_margin_value=profile.safety_margin_value,
                operational_occupied_value=max(Decimal("0"), operational_occupied_delta),
                active_reserved_value=max(Decimal("0"), active_reserved_delta),
                projected_free_value=profile.maximum_value - profile.safety_margin_value,
                unit_id=profile.unit_id,
                data_quality_status=DataQualityStatus.VALIDATED.value,
                calculated_at=now,
            )
        else:
            projection.operational_occupied_value = max(
                Decimal("0"), projection.operational_occupied_value + operational_occupied_delta
            )
            projection.active_reserved_value = max(
                Decimal("0"), projection.active_reserved_value + active_reserved_delta
            )
            projection.projected_free_value = (
                projection.maximum_value
                - projection.safety_margin_value
                - projection.operational_occupied_value
                - projection.active_reserved_value
            )
            projection.calculated_at = now
            projection.projection_version += 1

        self._projection_repo.upsert(projection)

    def create_profile(
        self,
        *,
        warehouse_location_id: UUID,
        capacity_type: str,
        maximum_value: Decimal,
        unit_id: UUID,
        safety_margin_value: Decimal = Decimal("0"),
    ):
        from ...infrastructure.persistence.models import WarehouseLocationCapacityProfileModel
        profile = WarehouseLocationCapacityProfileModel(
            warehouse_location_id=warehouse_location_id,
            capacity_type=capacity_type,
            maximum_value=maximum_value,
            unit_id=unit_id,
            safety_margin_value=safety_margin_value,
        )
        return self._profile_repo.create(profile)

    def list_locations_with_available_capacity(
        self,
        organization_id: UUID,
        warehouse_id: UUID,
        required_base_quantity: Decimal,
    ) -> list[UUID]:
        projections = self._projection_repo.list_available_for_product(
            organization_id, warehouse_id, required_base_quantity
        )
        return [p.location_id for p in projections]
