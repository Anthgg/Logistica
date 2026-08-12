"""Phase 043 — Recommendation run orchestration service."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ..enums import (
    PutawayRecommendationRunStatus,
    PutawayCandidateStatus,
    RotationStrategy,
)
from ..errors import (
    PutawayRecommendationNoCandidate,
    PutawaySourceNotEligible,
)
from ...infrastructure.persistence.repositories import (
    PutawayRecommendationRunRepository,
    PutawayLocationCandidateRepository,
    WarehouseLocationCapacityProfileRepository,
)
from ...infrastructure.persistence.models import (
    PutawayRecommendationRunModel,
    PutawayLocationCandidateModel,
)
from .policy_service import PutawayPolicyService
from .scoring_service import ScoringService, ScoringWeights, CandidateScore


class RecommendationService:
    """Orchestrates putaway recommendation runs."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._run_repo = PutawayRecommendationRunRepository(db)
        self._candidate_repo = PutawayLocationCandidateRepository(db)
        self._location_capacity_repo = WarehouseLocationCapacityProfileRepository(db)
        self._policy_service = PutawayPolicyService(db)
        self._scoring = ScoringService(db)

    def execute_recommendation(
        self,
        *,
        organization_id: UUID,
        warehouse_id: UUID,
        source_allocation_id: UUID,
        requested_quantity: Decimal,
        requested_unit_id: UUID,
        requested_base_quantity: Decimal,
        source_location_id: UUID,
        product_id: UUID,
        product_category_id: UUID | None,
        created_by: UUID,
    ) -> PutawayRecommendationRunModel:
        policy_version = self._policy_service.resolve_effective_version(
            organization_id, warehouse_id,
            product_id=product_id,
            product_category_id=product_category_id,
        )

        run = PutawayRecommendationRunModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            source_allocation_id=source_allocation_id,
            policy_version_id=policy_version.id,
            status=PutawayRecommendationRunStatus.PROCESSING.value,
            requested_quantity=requested_quantity,
            requested_unit_id=requested_unit_id,
            requested_base_quantity=requested_base_quantity,
            scoring_version="1.0",
            created_by=created_by,
            started_at=datetime.now(timezone.utc),
        )
        run = self._run_repo.create(run)

        try:
            weights = self._scoring.get_weights_from_policy_version(policy_version)
            candidates = self._find_and_score_candidates(
                run_id=run.id,
                organization_id=organization_id,
                warehouse_id=warehouse_id,
                source_location_id=source_location_id,
                product_id=product_id,
                product_category_id=product_category_id,
                required_base_quantity=requested_base_quantity,
                weights=weights,
            )

            ranked = self._scoring.rank_candidates(candidates)
            max_candidates = policy_version.maximum_candidate_count or 50
            ranked = ranked[:max_candidates]

            min_score = Decimal(str(policy_version.minimum_score)) if policy_version.minimum_score else None
            eligible = [c for c in ranked if c.compatible and c.capacity_available]
            if min_score is not None:
                eligible = [c for c in eligible if c.total_score >= min_score]

            candidate_models = []
            for c in ranked:
                model = PutawayLocationCandidateModel(
                    id=uuid4(),
                    recommendation_run_id=run.id,
                    location_id=c.location_id,
                    rank=c.rank,
                    compatible=c.compatible,
                    capacity_available=c.capacity_available,
                    capacity_score=c.capacity_score,
                    rotation_score=c.rotation_score,
                    picking_proximity_score=c.picking_proximity_score,
                    consolidation_score=c.consolidation_score,
                    fragmentation_score=c.fragmentation_score,
                    travel_cost_score=c.travel_cost_score,
                    penalty_score=c.penalty_score,
                    total_score=c.total_score,
                    capacity_snapshot=c.capacity_snapshot,
                    compatibility_snapshot=c.compatibility_snapshot,
                    proximity_snapshot=c.proximity_snapshot,
                    rotation_snapshot=c.rotation_snapshot,
                    explanation=c.explanation,
                    status=PutawayCandidateStatus.CANDIDATE.value,
                )
                candidate_models.append(model)

            if candidate_models:
                self._candidate_repo.create_many(candidate_models)

            run.candidate_count = len(candidate_models)
            run.eligible_candidate_count = len(eligible)
            run.status = PutawayRecommendationRunStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            self._run_repo.update_status(
                run.id,
                status=PutawayRecommendationRunStatus.COMPLETED.value,
                candidate_count=len(candidate_models),
                eligible_candidate_count=len(eligible),
                completed_at=datetime.now(timezone.utc),
            )

            return run

        except Exception as exc:
            self._run_repo.update_status(
                run.id,
                status=PutawayRecommendationRunStatus.FAILED.value,
                completed_at=datetime.now(timezone.utc),
            )
            raise

    def _find_and_score_candidates(
        self,
        *,
        run_id: UUID,
        organization_id: UUID,
        warehouse_id: UUID,
        source_location_id: UUID,
        product_id: UUID,
        product_category_id: UUID | None,
        required_base_quantity: Decimal,
        weights: ScoringWeights,
    ) -> list[CandidateScore]:
        from ...infrastructure.persistence.repositories import (
            WarehouseLocationRepository,
        )

        locations = self._get_eligible_locations(warehouse_id)

        candidates = []
        for location in locations:
            try:
                candidate = self._scoring.score_candidate(
                    location_id=location.id,
                    organization_id=organization_id,
                    warehouse_id=warehouse_id,
                    source_location_id=source_location_id,
                    product_id=product_id,
                    product_category_id=product_category_id,
                    required_base_quantity=required_base_quantity,
                    weights=weights,
                )
                candidates.append(candidate)
            except Exception:
                continue

        return candidates

    def _get_eligible_locations(self, warehouse_id: UUID):
        from ...infrastructure.persistence.models import WarehouseLocationModel
        return list(self._db.execute(
            select(WarehouseLocationModel).where(
                WarehouseLocationModel.warehouse_id == warehouse_id,
                WarehouseLocationModel.status == "ACTIVE",
                WarehouseLocationModel.putaway_priority > 0,
            )
        ).scalars().all())

    def get_recommendation(self, run_id: UUID) -> PutawayRecommendationRunModel | None:
        return self._run_repo.get(run_id)

    def get_best_candidate(self, run_id: UUID) -> PutawayLocationCandidateModel | None:
        return self._candidate_repo.get_best_candidate(run_id)

    def list_candidates(self, run_id: UUID) -> list[PutawayLocationCandidateModel]:
        return self._candidate_repo.list_by_run(run_id)

    def get_latest_for_allocation(self, source_allocation_id: UUID) -> PutawayRecommendationRunModel | None:
        return self._run_repo.get_latest_for_allocation(source_allocation_id)
