"""Phase 043 — Scoring engine for putaway candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from ..enums import RotationStrategy
from ..errors import PutawayIntegrityFailed
from .compatibility_service import StorageCompatibilityService, CompatibilityResult
from .capacity_service import CapacityService, CapacityEvaluation
from .proximity_service import ProximityService, TravelCostScore
from .rotation_service import RotationService, RotationEvaluation


@dataclass
class CandidateScore:
    location_id: UUID
    rank: int = 0
    compatible: bool = True
    capacity_available: bool = True
    capacity_score: Decimal = Decimal("0")
    rotation_score: Decimal = Decimal("0")
    picking_proximity_score: Decimal = Decimal("0")
    consolidation_score: Decimal = Decimal("0")
    fragmentation_score: Decimal = Decimal("0")
    travel_cost_score: Decimal = Decimal("0")
    penalty_score: Decimal = Decimal("0")
    total_score: Decimal = Decimal("0")
    capacity_snapshot: dict = field(default_factory=dict)
    compatibility_snapshot: dict = field(default_factory=dict)
    proximity_snapshot: dict = field(default_factory=dict)
    rotation_snapshot: dict = field(default_factory=dict)
    explanation: dict = field(default_factory=dict)


@dataclass
class ScoringWeights:
    capacity_weight: Decimal = Decimal("0.25")
    rotation_weight: Decimal = Decimal("0.20")
    picking_proximity_weight: Decimal = Decimal("0.20")
    consolidation_weight: Decimal = Decimal("0.10")
    fragmentation_penalty_weight: Decimal = Decimal("0.10")
    travel_cost_weight: Decimal = Decimal("0.15")


class ScoringService:
    """Scores putaway candidates based on weighted multi-criteria analysis."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._compatibility = StorageCompatibilityService(db)
        self._capacity = CapacityService(db)
        self._proximity = ProximityService(db)
        self._rotation = RotationService(db)

    def score_candidate(
        self,
        *,
        location_id: UUID,
        organization_id: UUID,
        warehouse_id: UUID,
        source_location_id: UUID,
        product_id: UUID,
        product_category_id: UUID | None,
        required_base_quantity: Decimal,
        weights: ScoringWeights,
        existing_product_ids: list[UUID] | None = None,
    ) -> CandidateScore:
        compat_result = self._compatibility.evaluate(
            warehouse_id, location_id,
            product_id=product_id,
            product_category_id=product_category_id,
        )

        capacity_eval = self._capacity.evaluate(
            organization_id, warehouse_id, location_id, required_base_quantity
        )

        capacity_score = self._score_capacity(capacity_eval)
        rotation_eval = self._rotation.evaluate(location_id)
        rotation_score = rotation_eval.score

        proximity_result = self._proximity.calculate_travel_cost_score(
            warehouse_id, source_location_id, location_id
        )

        travel_cost_score = proximity_result.score
        picking_proximity_score = proximity_result.score

        consolidation_score = self._score_consolidation(
            location_id, product_id, existing_product_ids
        )
        fragmentation_score = self._score_fragmentation(
            capacity_eval, required_base_quantity
        )
        penalty_score = self._calculate_penalty(compat_result)

        total = (
            capacity_score * weights.capacity_weight
            + rotation_score * weights.rotation_weight
            + picking_proximity_score * weights.picking_proximity_weight
            + consolidation_score * weights.consolidation_weight
            + (Decimal("100") - fragmentation_score) * weights.fragmentation_penalty_weight
            + travel_cost_score * weights.travel_cost_weight
            - penalty_score
        ).quantize(Decimal("0.01"))

        total = max(Decimal("0"), min(Decimal("100"), total))

        return CandidateScore(
            location_id=location_id,
            compatible=compat_result.compatible,
            capacity_available=capacity_eval.has_enough if capacity_eval else False,
            capacity_score=capacity_score,
            rotation_score=rotation_score,
            picking_proximity_score=picking_proximity_score,
            consolidation_score=consolidation_score,
            fragmentation_score=fragmentation_score,
            travel_cost_score=travel_cost_score,
            penalty_score=penalty_score,
            total_score=total,
            capacity_snapshot={
                "maximum": str(capacity_eval.maximum_value) if capacity_eval else None,
                "projected_free": str(capacity_eval.projected_free) if capacity_eval else None,
                "data_quality": capacity_eval.data_quality_status if capacity_eval else None,
            },
            compatibility_snapshot={
                "compatible": compat_result.compatible,
                "action": compat_result.action,
                "severity": compat_result.severity,
                "warnings": compat_result.warnings,
            },
            proximity_snapshot={
                "walking_distance": str(proximity_result.walking_distance) if proximity_result.walking_distance else None,
                "travel_time": str(proximity_result.travel_time) if proximity_result.travel_time else None,
            },
            rotation_snapshot={
                "strategy": rotation_eval.rotation_strategy,
                "placement_count": rotation_eval.placement_count,
                "days_since_last": rotation_eval.days_since_last_putaway,
            },
            explanation={
                "weights": {
                    "capacity": str(weights.capacity_weight),
                    "rotation": str(weights.rotation_weight),
                    "picking_proximity": str(weights.picking_proximity_weight),
                    "consolidation": str(weights.consolidation_weight),
                    "fragmentation": str(weights.fragmentation_penalty_weight),
                    "travel_cost": str(weights.travel_cost_weight),
                },
            },
        )

    def _score_capacity(self, eval: CapacityEvaluation | None) -> Decimal:
        if eval is None:
            return Decimal("50")

        if not eval.has_enough:
            return Decimal("0")

        if eval.maximum_value == 0:
            return Decimal("100")

        utilization = eval.operational_occupied / eval.maximum_value
        if utilization < Decimal("0.5"):
            return Decimal("90")
        elif utilization < Decimal("0.8"):
            return Decimal("70")
        else:
            return Decimal("40")

    def _score_consolidation(
        self, location_id: UUID, product_id: UUID,
        existing_product_ids: list[UUID] | None,
    ) -> Decimal:
        if existing_product_ids and product_id in existing_product_ids:
            return Decimal("90")
        return Decimal("50")

    def _score_fragmentation(
        self, capacity_eval: CapacityEvaluation | None,
        required_base_quantity: Decimal,
    ) -> Decimal:
        if capacity_eval is None:
            return Decimal("50")

        if capacity_eval.projected_free == 0:
            return Decimal("100")

        fit_ratio = required_base_quantity / capacity_eval.projected_free
        if fit_ratio <= Decimal("0.25"):
            return Decimal("20")
        elif fit_ratio <= Decimal("0.5"):
            return Decimal("40")
        elif fit_ratio <= Decimal("0.75"):
            return Decimal("60")
        else:
            return Decimal("80")

    def _calculate_penalty(self, compat: CompatibilityResult) -> Decimal:
        if not compat.compatible:
            return Decimal("50")

        penalty = Decimal("0")
        if compat.severity == "HIGH":
            penalty += Decimal("10")
        elif compat.severity == "CRITICAL":
            penalty += Decimal("20")

        penalty += Decimal(str(len(compat.warnings))) * Decimal("2")
        return penalty

    def rank_candidates(self, candidates: list[CandidateScore]) -> list[CandidateScore]:
        sorted_candidates = sorted(
            candidates, key=lambda c: c.total_score, reverse=True
        )
        for i, candidate in enumerate(sorted_candidates, 1):
            candidate.rank = i
        return sorted_candidates

    def get_weights_from_policy_version(self, policy_version) -> ScoringWeights:
        return ScoringWeights(
            capacity_weight=Decimal(str(policy_version.capacity_weight)),
            rotation_weight=Decimal(str(policy_version.rotation_weight)),
            picking_proximity_weight=Decimal(str(policy_version.picking_proximity_weight)),
            consolidation_weight=Decimal(str(policy_version.consolidation_weight)),
            fragmentation_penalty_weight=Decimal(str(policy_version.fragmentation_penalty_weight)),
            travel_cost_weight=Decimal(str(policy_version.travel_cost_weight)),
        )
