"""Phase 043 — Proximity and travel cost calculation service."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from ..enums import MetricType, MetricSourceType
from ...infrastructure.persistence.repositories import WarehouseLocationProximityProfileRepository


@dataclass
class ProximityResult:
    source_location_id: UUID
    target_location_id: UUID | None
    target_zone_id: UUID | None
    metric_type: str
    metric_value: Decimal
    metric_unit: str
    source_type: str


@dataclass
class TravelCostScore:
    walking_distance: Decimal | None
    travel_time: Decimal | None
    normalized_distance: Decimal
    score: Decimal


class ProximityService:
    """Calculates proximity metrics and travel costs for putaway candidates."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._proximity_repo = WarehouseLocationProximityProfileRepository(db)

    def get_distance(
        self,
        warehouse_id: UUID,
        source_id: UUID,
        target_id: UUID,
    ) -> ProximityResult | None:
        profile = self._proximity_repo.get_distance(
            warehouse_id, source_id, target_id,
            metric_type=MetricType.WALKING_DISTANCE_M.value,
        )
        if profile is None:
            return None

        return ProximityResult(
            source_location_id=profile.source_location_id,
            target_location_id=profile.target_location_id,
            target_zone_id=profile.target_zone_id,
            metric_type=profile.metric_type,
            metric_value=profile.metric_value,
            metric_unit=profile.metric_unit,
            source_type=profile.source_type,
        )

    def get_travel_time(
        self,
        warehouse_id: UUID,
        source_id: UUID,
        target_id: UUID,
    ) -> ProximityResult | None:
        profile = self._proximity_repo.get_distance(
            warehouse_id, source_id, target_id,
            metric_type=MetricType.TRAVEL_TIME_S.value,
        )
        if profile is None:
            return None

        return ProximityResult(
            source_location_id=profile.source_location_id,
            target_location_id=profile.target_location_id,
            target_zone_id=profile.target_zone_id,
            metric_type=profile.metric_type,
            metric_value=profile.metric_value,
            metric_unit=profile.metric_unit,
            source_type=profile.source_type,
        )

    def calculate_travel_cost_score(
        self,
        warehouse_id: UUID,
        source_id: UUID,
        target_id: UUID,
        *,
        max_distance: Decimal = Decimal("1000"),
    ) -> TravelCostScore:
        distance_result = self.get_distance(warehouse_id, source_id, target_id)
        time_result = self.get_travel_time(warehouse_id, source_id, target_id)

        walking_distance = distance_result.metric_value if distance_result else None
        travel_time = time_result.metric_value if time_result else None

        if walking_distance is not None:
            normalized = min(walking_distance / max_distance, Decimal("1"))
        elif travel_time is not None:
            normalized = min(travel_time / Decimal("600"), Decimal("1"))
        else:
            normalized = Decimal("0.5")

        score = (Decimal("1") - normalized) * Decimal("100")

        return TravelCostScore(
            walking_distance=walking_distance,
            travel_time=travel_time,
            normalized_distance=normalized,
            score=score.quantize(Decimal("0.01")),
        )

    def list_reachable_locations(
        self,
        warehouse_id: UUID,
        source_id: UUID,
        *,
        metric_type: str | None = None,
    ) -> list[ProximityResult]:
        profiles = self._proximity_repo.list_from_location(
            warehouse_id, source_id, metric_type=metric_type
        )
        return [
            ProximityResult(
                source_location_id=p.source_location_id,
                target_location_id=p.target_location_id,
                target_zone_id=p.target_zone_id,
                metric_type=p.metric_type,
                metric_value=p.metric_value,
                metric_unit=p.metric_unit,
                source_type=p.source_type,
            )
            for p in profiles
        ]

    def list_locations_near_zone(
        self,
        warehouse_id: UUID,
        zone_id: UUID,
        *,
        metric_type: str | None = None,
    ) -> list[ProximityResult]:
        profiles = self._proximity_repo.list_to_zone(
            warehouse_id, zone_id, metric_type=metric_type
        )
        return [
            ProximityResult(
                source_location_id=p.source_location_id,
                target_location_id=p.target_location_id,
                target_zone_id=p.target_zone_id,
                metric_type=p.metric_type,
                metric_value=p.metric_value,
                metric_unit=p.metric_unit,
                source_type=p.source_type,
            )
            for p in profiles
        ]

    def create_profile(
        self,
        *,
        warehouse_id: UUID,
        source_location_id: UUID,
        target_zone_id: UUID | None = None,
        target_location_id: UUID | None = None,
        metric_type: str,
        metric_value: Decimal,
        metric_unit: str,
        source_type: str = MetricSourceType.MANUAL_MEASUREMENT.value,
    ):
        from ...infrastructure.persistence.models import WarehouseLocationProximityProfileModel
        profile = WarehouseLocationProximityProfileModel(
            warehouse_id=warehouse_id,
            source_location_id=source_location_id,
            target_zone_id=target_zone_id,
            target_location_id=target_location_id,
            metric_type=metric_type,
            metric_value=metric_value,
            metric_unit=metric_unit,
            source_type=source_type,
        )
        return self._proximity_repo.create(profile)
