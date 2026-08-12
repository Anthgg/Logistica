"""Phase 043 — Putaway repositories (22 tables, grouped by domain)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import Session, selectinload

from .models import (
    PutawayPolicyModel,
    PutawayPolicyVersionModel,
    StorageCompatibilityRuleModel,
    WarehouseLocationCapacityProfileModel,
    PutawayLocationCapacityProjectionModel,
    WarehouseLocationProximityProfileModel,
    PutawayRecommendationRunModel,
    PutawayLocationCandidateModel,
    PutawayOrderModel,
    PutawayOrderRevisionModel,
    PutawayTaskModel,
    PutawayTaskDestinationModel,
    PutawayTaskAssignmentModel,
    PutawayLocationReservationModel,
    PutawayExecutionSessionModel,
    PutawayScanEventModel,
    PutawayPlacementConfirmationModel,
    PutawayLocationOverrideModel,
    PutawayTaskExceptionModel,
    PutawayTaskPauseModel,
    OperationalInventoryPlacementModel,
    PutawayLocationPlacementProjectionModel,
)

SORT_FIELDS_POLICY = {
    "created_at": PutawayPolicyModel.created_at,
    "code": PutawayPolicyModel.code,
    "name": PutawayPolicyModel.name,
    "status": PutawayPolicyModel.status,
}

SORT_FIELDS_ORDER = {
    "created_at": PutawayOrderModel.created_at,
    "order_code": PutawayOrderModel.order_code,
    "status": PutawayOrderModel.status,
    "priority": PutawayOrderModel.priority,
}

SORT_FIELDS_TASK = {
    "created_at": PutawayTaskModel.created_at,
    "task_number": PutawayTaskModel.task_number,
    "status": PutawayTaskModel.status,
    "priority": PutawayTaskModel.priority,
}


# =============================================================================
# 1. PutawayPolicyRepository
# =============================================================================
class PutawayPolicyRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, policy_id: UUID, organization_id: UUID | None = None) -> PutawayPolicyModel | None:
        stmt = select(PutawayPolicyModel).where(PutawayPolicyModel.id == policy_id)
        if organization_id:
            stmt = stmt.where(PutawayPolicyModel.organization_id == organization_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_code(self, organization_id: UUID, code: str) -> PutawayPolicyModel | None:
        normalized = code.strip().upper()
        return self._db.execute(
            select(PutawayPolicyModel).where(
                PutawayPolicyModel.organization_id == organization_id,
                PutawayPolicyModel.normalized_code == normalized,
            )
        ).scalar_one_or_none()

    def create(self, policy: PutawayPolicyModel) -> PutawayPolicyModel:
        self._db.add(policy)
        self._db.flush()
        return policy

    def update(self, policy: PutawayPolicyModel, *, expected_version: int | None = None) -> PutawayPolicyModel:
        if expected_version is not None:
            if policy.row_version != expected_version:
                raise ValueError("Row version mismatch")
            policy.row_version = expected_version + 1
        self._db.flush()
        return policy

    def list(
        self, organization_id: UUID, *, page: int = 1, page_size: int = 20,
        search: str | None = None, status: str | None = None,
        sort_by: str = "created_at", sort_order: str = "desc",
    ) -> tuple[list[PutawayPolicyModel], int]:
        filters = [PutawayPolicyModel.organization_id == organization_id]
        if status:
            filters.append(PutawayPolicyModel.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(sa.or_(
                PutawayPolicyModel.code.ilike(pattern),
                PutawayPolicyModel.name.ilike(pattern),
            ))
        total = self._db.scalar(
            select(func.count()).select_from(PutawayPolicyModel).where(*filters)
        ) or 0
        sort_col = SORT_FIELDS_POLICY.get(sort_by, PutawayPolicyModel.created_at)
        sort_col = sort_col.desc() if sort_order == "desc" else sort_col.asc()
        items = list(self._db.scalars(
            select(PutawayPolicyModel).where(*filters).order_by(sort_col)
            .offset((page - 1) * page_size).limit(page_size)
        ))
        return items, total

    def count_by_org(self, organization_id: UUID) -> int:
        return self._db.scalar(
            select(func.count()).select_from(PutawayPolicyModel).where(
                PutawayPolicyModel.organization_id == organization_id
            )
        ) or 0

    def exists_active_for_product(self, organization_id: UUID, product_id: UUID) -> bool:
        stmt = (
            select(PutawayPolicyVersionModel.id)
            .join(PutawayPolicyModel, PutawayPolicyModel.id == PutawayPolicyVersionModel.policy_id)
            .where(
                PutawayPolicyModel.organization_id == organization_id,
                PutawayPolicyModel.status == "ACTIVE",
                PutawayPolicyVersionModel.status == "ACTIVE",
                sa.or_(
                    PutawayPolicyVersionModel.product_id == product_id,
                    PutawayPolicyVersionModel.product_id.is_(None),
                ),
            )
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none() is not None


# =============================================================================
# 2. PutawayPolicyVersionRepository
# =============================================================================
class PutawayPolicyVersionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, version_id: UUID) -> PutawayPolicyVersionModel | None:
        return self._db.get(PutawayPolicyVersionModel, version_id)

    def get_active_for_policy(self, policy_id: UUID) -> PutawayPolicyVersionModel | None:
        return self._db.execute(
            select(PutawayPolicyVersionModel).where(
                PutawayPolicyVersionModel.policy_id == policy_id,
                PutawayPolicyVersionModel.status == "ACTIVE",
            ).order_by(PutawayPolicyVersionModel.version_number.desc()).limit(1)
        ).scalar_one_or_none()

    def get_effective_for_context(
        self, organization_id: UUID, warehouse_id: UUID,
        product_id: UUID | None = None, product_category_id: UUID | None = None,
        at: datetime | None = None,
    ) -> PutawayPolicyVersionModel | None:
        now = at or datetime.now(timezone.utc)
        stmt = (
            select(PutawayPolicyVersionModel)
            .join(PutawayPolicyModel, PutawayPolicyModel.id == PutawayPolicyVersionModel.policy_id)
            .where(
                PutawayPolicyModel.organization_id == organization_id,
                PutawayPolicyModel.status == "ACTIVE",
                PutawayPolicyVersionModel.status == "ACTIVE",
                PutawayPolicyVersionModel.effective_from <= now,
                sa.or_(
                    PutawayPolicyVersionModel.effective_to.is_(None),
                    PutawayPolicyVersionModel.effective_to > now,
                ),
                sa.or_(
                    PutawayPolicyVersionModel.warehouse_id == warehouse_id,
                    PutawayPolicyVersionModel.warehouse_id.is_(None),
                ),
            )
            .order_by(
                PutawayPolicyVersionModel.priority.desc(),
                PutawayPolicyVersionModel.version_number.desc(),
            )
        )
        if product_id:
            stmt = stmt.where(sa.or_(
                PutawayPolicyVersionModel.product_id == product_id,
                PutawayPolicyVersionModel.product_id.is_(None),
            ))
        if product_category_id:
            stmt = stmt.where(sa.or_(
                PutawayPolicyVersionModel.product_category_id == product_category_id,
                PutawayPolicyVersionModel.product_category_id.is_(None),
            ))
        return self._db.execute(stmt.limit(1)).scalar_one_or_none()

    def create(self, version: PutawayPolicyVersionModel) -> PutawayPolicyVersionModel:
        self._db.add(version)
        self._db.flush()
        return version

    def next_version_number(self, policy_id: UUID) -> int:
        result = self._db.scalar(
            select(func.max(PutawayPolicyVersionModel.version_number)).where(
                PutawayPolicyVersionModel.policy_id == policy_id
            )
        )
        return (result or 0) + 1

    def list_by_policy(self, policy_id: UUID) -> list[PutawayPolicyVersionModel]:
        return list(self._db.scalars(
            select(PutawayPolicyVersionModel)
            .where(PutawayPolicyVersionModel.policy_id == policy_id)
            .order_by(PutawayPolicyVersionModel.version_number.desc())
        ))


# =============================================================================
# 3. StorageCompatibilityRuleRepository
# =============================================================================
class StorageCompatibilityRuleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, rule_id: UUID) -> StorageCompatibilityRuleModel | None:
        return self._db.get(StorageCompatibilityRuleModel, rule_id)

    def create(self, rule: StorageCompatibilityRuleModel) -> StorageCompatibilityRuleModel:
        self._db.add(rule)
        self._db.flush()
        return rule

    def list_by_warehouse(
        self, warehouse_id: UUID, *, rule_type: str | None = None,
        product_id: UUID | None = None, location_id: UUID | None = None,
    ) -> list[StorageCompatibilityRuleModel]:
        filters = [
            StorageCompatibilityRuleModel.warehouse_id == warehouse_id,
            StorageCompatibilityRuleModel.status == "ACTIVE",
        ]
        if rule_type:
            filters.append(StorageCompatibilityRuleModel.rule_type == rule_type)
        if product_id:
            filters.append(sa.or_(
                StorageCompatibilityRuleModel.product_id == product_id,
                StorageCompatibilityRuleModel.product_id.is_(None),
            ))
        if location_id:
            filters.append(sa.or_(
                StorageCompatibilityRuleModel.location_id == location_id,
                StorageCompatibilityRuleModel.location_id.is_(None),
            ))
        return list(self._db.scalars(
            select(StorageCompatibilityRuleModel).where(*filters)
            .order_by(StorageCompatibilityRuleModel.created_at.desc())
        ))

    def list_by_policy_version(self, policy_version_id: UUID) -> list[StorageCompatibilityRuleModel]:
        return list(self._db.scalars(
            select(StorageCompatibilityRuleModel).where(
                StorageCompatibilityRuleModel.policy_version_id == policy_version_id,
                StorageCompatibilityRuleModel.status == "ACTIVE",
            )
        ))

    def deactivate(self, rule_id: UUID) -> None:
        self._db.execute(
            update(StorageCompatibilityRuleModel)
            .where(StorageCompatibilityRuleModel.id == rule_id)
            .values(status="INACTIVE")
        )
        self._db.flush()

    def delete_by_policy_version(self, policy_version_id: UUID) -> None:
        self._db.execute(
            delete(StorageCompatibilityRuleModel).where(
                StorageCompatibilityRuleModel.policy_version_id == policy_version_id
            )
        )
        self._db.flush()


# =============================================================================
# 4. WarehouseLocationCapacityProfileRepository
# =============================================================================
class WarehouseLocationCapacityProfileRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, profile_id: UUID) -> WarehouseLocationCapacityProfileModel | None:
        return self._db.get(WarehouseLocationCapacityProfileModel, profile_id)

    def create(self, profile: WarehouseLocationCapacityProfileModel) -> WarehouseLocationCapacityProfileModel:
        self._db.add(profile)
        self._db.flush()
        return profile

    def list_by_location(self, location_id: UUID) -> list[WarehouseLocationCapacityProfileModel]:
        return list(self._db.scalars(
            select(WarehouseLocationCapacityProfileModel).where(
                WarehouseLocationCapacityProfileModel.warehouse_location_id == location_id,
                WarehouseLocationCapacityProfileModel.status == "ACTIVE",
            )
        ))

    def get_effective(self, location_id: UUID, capacity_type: str, at: datetime | None = None) -> WarehouseLocationCapacityProfileModel | None:
        now = at or datetime.now(timezone.utc)
        return self._db.execute(
            select(WarehouseLocationCapacityProfileModel).where(
                WarehouseLocationCapacityProfileModel.warehouse_location_id == location_id,
                WarehouseLocationCapacityProfileModel.capacity_type == capacity_type,
                WarehouseLocationCapacityProfileModel.status == "ACTIVE",
                WarehouseLocationCapacityProfileModel.effective_from <= now,
                sa.or_(
                    WarehouseLocationCapacityProfileModel.effective_to.is_(None),
                    WarehouseLocationCapacityProfileModel.effective_to > now,
                ),
            ).order_by(WarehouseLocationCapacityProfileModel.effective_from.desc()).limit(1)
        ).scalar_one_or_none()

    def update(self, profile: WarehouseLocationCapacityProfileModel) -> None:
        profile.row_version += 1
        self._db.flush()


# =============================================================================
# 5. PutawayLocationCapacityProjectionRepository
# =============================================================================
class PutawayLocationCapacityProjectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_or_none(
        self, organization_id: UUID, warehouse_id: UUID,
        location_id: UUID, capacity_profile_id: UUID,
    ) -> PutawayLocationCapacityProjectionModel | None:
        return self._db.execute(
            select(PutawayLocationCapacityProjectionModel).where(
                PutawayLocationCapacityProjectionModel.organization_id == organization_id,
                PutawayLocationCapacityProjectionModel.warehouse_id == warehouse_id,
                PutawayLocationCapacityProjectionModel.location_id == location_id,
                PutawayLocationCapacityProjectionModel.capacity_profile_id == capacity_profile_id,
            )
        ).scalar_one_or_none()

    def upsert(self, projection: PutawayLocationCapacityProjectionModel) -> PutawayLocationCapacityProjectionModel:
        existing = self.get_or_none(
            projection.organization_id, projection.warehouse_id,
            projection.location_id, projection.capacity_profile_id,
        )
        if existing:
            for field in (
                "maximum_value", "safety_margin_value", "operational_occupied_value",
                "active_reserved_value", "projected_free_value", "data_quality_status",
                "last_placement_at", "calculated_at",
            ):
                setattr(existing, field, getattr(projection, field))
            existing.projection_version += 1
            self._db.flush()
            return existing
        self._db.add(projection)
        self._db.flush()
        return projection

    def list_available_for_product(
        self, organization_id: UUID, warehouse_id: UUID,
        required_base_quantity: Decimal, *,
        location_ids: list[UUID] | None = None,
    ) -> list[PutawayLocationCapacityProjectionModel]:
        filters = [
            PutawayLocationCapacityProjectionModel.organization_id == organization_id,
            PutawayLocationCapacityProjectionModel.warehouse_id == warehouse_id,
            PutawayLocationCapacityProjectionModel.projected_free_value >= required_base_quantity,
        ]
        if location_ids:
            filters.append(PutawayLocationCapacityProjectionModel.location_id.in_(location_ids))
        return list(self._db.scalars(
            select(PutawayLocationCapacityProjectionModel).where(*filters)
        ))


# =============================================================================
# 6. WarehouseLocationProximityProfileRepository
# =============================================================================
class WarehouseLocationProximityProfileRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, profile_id: UUID) -> WarehouseLocationProximityProfileModel | None:
        return self._db.get(WarehouseLocationProximityProfileModel, profile_id)

    def create(self, profile: WarehouseLocationProximityProfileModel) -> WarehouseLocationProximityProfileModel:
        self._db.add(profile)
        self._db.flush()
        return profile

    def list_from_location(
        self, warehouse_id: UUID, source_location_id: UUID, *,
        metric_type: str | None = None,
    ) -> list[WarehouseLocationProximityProfileModel]:
        filters = [
            WarehouseLocationProximityProfileModel.warehouse_id == warehouse_id,
            WarehouseLocationProximityProfileModel.source_location_id == source_location_id,
            WarehouseLocationProximityProfileModel.status == "ACTIVE",
        ]
        if metric_type:
            filters.append(WarehouseLocationProximityProfileModel.metric_type == metric_type)
        return list(self._db.scalars(
            select(WarehouseLocationProximityProfileModel).where(*filters)
        ))

    def list_to_zone(
        self, warehouse_id: UUID, target_zone_id: UUID, *,
        metric_type: str | None = None,
    ) -> list[WarehouseLocationProximityProfileModel]:
        filters = [
            WarehouseLocationProximityProfileModel.warehouse_id == warehouse_id,
            WarehouseLocationProximityProfileModel.target_zone_id == target_zone_id,
            WarehouseLocationProximityProfileModel.status == "ACTIVE",
        ]
        if metric_type:
            filters.append(WarehouseLocationProximityProfileModel.metric_type == metric_type)
        return list(self._db.scalars(
            select(WarehouseLocationProximityProfileModel).where(*filters)
        ))

    def get_distance(
        self, warehouse_id: UUID, source_id: UUID, target_id: UUID, *,
        metric_type: str = "WALKING_DISTANCE_M",
    ) -> WarehouseLocationProximityProfileModel | None:
        return self._db.execute(
            select(WarehouseLocationProximityProfileModel).where(
                WarehouseLocationProximityProfileModel.warehouse_id == warehouse_id,
                WarehouseLocationProximityProfileModel.source_location_id == source_id,
                WarehouseLocationProximityProfileModel.target_location_id == target_id,
                WarehouseLocationProximityProfileModel.metric_type == metric_type,
                WarehouseLocationProximityProfileModel.status == "ACTIVE",
            )
        ).scalar_one_or_none()

    def delete_by_warehouse(self, warehouse_id: UUID) -> None:
        self._db.execute(
            delete(WarehouseLocationProximityProfileModel).where(
                WarehouseLocationProximityProfileModel.warehouse_id == warehouse_id
            )
        )
        self._db.flush()


# =============================================================================
# 7. PutawayRecommendationRunRepository
# =============================================================================
class PutawayRecommendationRunRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, run_id: UUID) -> PutawayRecommendationRunModel | None:
        return self._db.execute(
            select(PutawayRecommendationRunModel)
            .options(selectinload(PutawayRecommendationRunModel.candidates))
            .where(PutawayRecommendationRunModel.id == run_id)
        ).scalar_one_or_none()

    def create(self, run: PutawayRecommendationRunModel) -> PutawayRecommendationRunModel:
        self._db.add(run)
        self._db.flush()
        return run

    def update_status(self, run_id: UUID, *, status: str, **extra) -> None:
        values = {"status": status}
        values.update(extra)
        self._db.execute(
            update(PutawayRecommendationRunModel)
            .where(PutawayRecommendationRunModel.id == run_id)
            .values(**values)
        )
        self._db.flush()

    def get_latest_for_allocation(self, source_allocation_id: UUID) -> PutawayRecommendationRunModel | None:
        return self._db.execute(
            select(PutawayRecommendationRunModel).where(
                PutawayRecommendationRunModel.source_allocation_id == source_allocation_id
            ).order_by(PutawayRecommendationRunModel.created_at.desc()).limit(1)
        ).scalar_one_or_none()


# =============================================================================
# 8. PutawayLocationCandidateRepository
# =============================================================================
class PutawayLocationCandidateRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, candidate: PutawayLocationCandidateModel) -> PutawayLocationCandidateModel:
        self._db.add(candidate)
        self._db.flush()
        return candidate

    def create_many(self, candidates: list[PutawayLocationCandidateModel]) -> list[PutawayLocationCandidateModel]:
        self._db.add_all(candidates)
        self._db.flush()
        return candidates

    def list_by_run(self, run_id: UUID) -> list[PutawayLocationCandidateModel]:
        return list(self._db.scalars(
            select(PutawayLocationCandidateModel).where(
                PutawayLocationCandidateModel.recommendation_run_id == run_id
            ).order_by(PutawayLocationCandidateModel.rank)
        ))

    def get_best_candidate(self, run_id: UUID) -> PutawayLocationCandidateModel | None:
        return self._db.execute(
            select(PutawayLocationCandidateModel).where(
                PutawayLocationCandidateModel.recommendation_run_id == run_id,
                PutawayLocationCandidateModel.compatible == True,
                PutawayLocationCandidateModel.capacity_available == True,
                PutawayLocationCandidateModel.status == "CANDIDATE",
            ).order_by(PutawayLocationCandidateModel.total_score.desc()).limit(1)
        ).scalar_one_or_none()

    def update_status(self, candidate_id: UUID, *, status: str) -> None:
        self._db.execute(
            update(PutawayLocationCandidateModel)
            .where(PutawayLocationCandidateModel.id == candidate_id)
            .values(status=status)
        )
        self._db.flush()


# =============================================================================
# 9. PutawayOrderRepository
# =============================================================================
class PutawayOrderRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, order_id: UUID, organization_id: UUID | None = None) -> PutawayOrderModel | None:
        stmt = select(PutawayOrderModel).where(PutawayOrderModel.id == order_id)
        if organization_id:
            stmt = stmt.where(PutawayOrderModel.organization_id == organization_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_code(self, organization_id: UUID, order_code: str) -> PutawayOrderModel | None:
        normalized = order_code.strip().upper()
        return self._db.execute(
            select(PutawayOrderModel).where(
                PutawayOrderModel.organization_id == organization_id,
                PutawayOrderModel.normalized_order_code == normalized,
            )
        ).scalar_one_or_none()

    def create(self, order: PutawayOrderModel) -> PutawayOrderModel:
        self._db.add(order)
        self._db.flush()
        return order

    def update(self, order: PutawayOrderModel, *, expected_version: int | None = None) -> PutawayOrderModel:
        if expected_version is not None:
            if order.row_version != expected_version:
                raise ValueError("Row version mismatch")
            order.row_version = expected_version + 1
        self._db.flush()
        return order

    def list(
        self, organization_id: UUID, *, page: int = 1, page_size: int = 20,
        warehouse_id: UUID | None = None, status: str | None = None,
        source_type: str | None = None, search: str | None = None,
        sort_by: str = "created_at", sort_order: str = "desc",
    ) -> tuple[list[PutawayOrderModel], int]:
        filters = [PutawayOrderModel.organization_id == organization_id]
        if warehouse_id:
            filters.append(PutawayOrderModel.warehouse_id == warehouse_id)
        if status:
            filters.append(PutawayOrderModel.status == status)
        if source_type:
            filters.append(PutawayOrderModel.source_type == source_type)
        if search:
            pattern = f"%{search}%"
            filters.append(PutawayOrderModel.order_code.ilike(pattern))
        total = self._db.scalar(
            select(func.count()).select_from(PutawayOrderModel).where(*filters)
        ) or 0
        sort_col = SORT_FIELDS_ORDER.get(sort_by, PutawayOrderModel.created_at)
        sort_col = sort_col.desc() if sort_order == "desc" else sort_col.asc()
        items = list(self._db.scalars(
            select(PutawayOrderModel).where(*filters).order_by(sort_col)
            .offset((page - 1) * page_size).limit(page_size)
        ))
        return items, total


# =============================================================================
# 10. PutawayOrderRevisionRepository
# =============================================================================
class PutawayOrderRevisionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, revision_id: UUID) -> PutawayOrderRevisionModel | None:
        return self._db.get(PutawayOrderRevisionModel, revision_id)

    def create(self, revision: PutawayOrderRevisionModel) -> PutawayOrderRevisionModel:
        self._db.add(revision)
        self._db.flush()
        return revision

    def list_by_order(self, order_id: UUID) -> list[PutawayOrderRevisionModel]:
        return list(self._db.scalars(
            select(PutawayOrderRevisionModel).where(
                PutawayOrderRevisionModel.putaway_order_id == order_id
            ).order_by(PutawayOrderRevisionModel.revision_number.desc())
        ))

    def get_latest(self, order_id: UUID) -> PutawayOrderRevisionModel | None:
        return self._db.execute(
            select(PutawayOrderRevisionModel).where(
                PutawayOrderRevisionModel.putaway_order_id == order_id
            ).order_by(PutawayOrderRevisionModel.revision_number.desc()).limit(1)
        ).scalar_one_or_none()

    def next_revision_number(self, order_id: UUID) -> int:
        result = self._db.scalar(
            select(func.max(PutawayOrderRevisionModel.revision_number)).where(
                PutawayOrderRevisionModel.putaway_order_id == order_id
            )
        )
        return (result or 0) + 1


# =============================================================================
# 11. PutawayTaskRepository
# =============================================================================
class PutawayTaskRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, task_id: UUID, organization_id: UUID | None = None) -> PutawayTaskModel | None:
        stmt = select(PutawayTaskModel).where(PutawayTaskModel.id == task_id)
        if organization_id:
            stmt = stmt.where(PutawayTaskModel.organization_id == organization_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_number(self, order_id: UUID, task_number: str) -> PutawayTaskModel | None:
        return self._db.execute(
            select(PutawayTaskModel).where(
                PutawayTaskModel.putaway_order_id == order_id,
                PutawayTaskModel.task_number == task_number,
            )
        ).scalar_one_or_none()

    def create(self, task: PutawayTaskModel) -> PutawayTaskModel:
        self._db.add(task)
        self._db.flush()
        return task

    def update(self, task: PutawayTaskModel, *, expected_version: int | None = None) -> PutawayTaskModel:
        if expected_version is not None:
            if task.row_version != expected_version:
                raise ValueError("Row version mismatch")
            task.row_version = expected_version + 1
        self._db.flush()
        return task

    def list(
        self, organization_id: UUID, *, page: int = 1, page_size: int = 20,
        warehouse_id: UUID | None = None, putaway_order_id: UUID | None = None,
        status: str | None = None, assigned_user_id: UUID | None = None,
        sort_by: str = "created_at", sort_order: str = "desc",
    ) -> tuple[list[PutawayTaskModel], int]:
        filters = [PutawayTaskModel.organization_id == organization_id]
        if warehouse_id:
            filters.append(PutawayTaskModel.warehouse_id == warehouse_id)
        if putaway_order_id:
            filters.append(PutawayTaskModel.putaway_order_id == putaway_order_id)
        if status:
            filters.append(PutawayTaskModel.status == status)
        if assigned_user_id:
            filters.append(PutawayTaskModel.assigned_user_id == assigned_user_id)
        total = self._db.scalar(
            select(func.count()).select_from(PutawayTaskModel).where(*filters)
        ) or 0
        sort_col = SORT_FIELDS_TASK.get(sort_by, PutawayTaskModel.created_at)
        sort_col = sort_col.desc() if sort_order == "desc" else sort_col.asc()
        items = list(self._db.scalars(
            select(PutawayTaskModel).where(*filters).order_by(sort_col)
            .offset((page - 1) * page_size).limit(page_size)
        ))
        return items, total

    def count_by_order(self, order_id: UUID) -> int:
        return self._db.scalar(
            select(func.count()).select_from(PutawayTaskModel).where(
                PutawayTaskModel.putaway_order_id == order_id
            )
        ) or 0

    def count_completed_by_order(self, order_id: UUID) -> int:
        return self._db.scalar(
            select(func.count()).select_from(PutawayTaskModel).where(
                PutawayTaskModel.putaway_order_id == order_id,
                PutawayTaskModel.status == "COMPLETED",
            )
        ) or 0

    def count_exception_by_order(self, order_id: UUID) -> int:
        return self._db.scalar(
            select(func.count()).select_from(PutawayTaskModel).where(
                PutawayTaskModel.putaway_order_id == order_id,
                PutawayTaskModel.status == "EXCEPTION",
            )
        ) or 0

    def next_task_number(self, order_id: UUID) -> str:
        count = self.count_by_order(order_id) + 1
        return f"T-{count:04d}"


# =============================================================================
# 12. PutawayTaskDestinationRepository
# =============================================================================
class PutawayTaskDestinationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, dest: PutawayTaskDestinationModel) -> PutawayTaskDestinationModel:
        self._db.add(dest)
        self._db.flush()
        return dest

    def create_many(self, dests: list[PutawayTaskDestinationModel]) -> list[PutawayTaskDestinationModel]:
        self._db.add_all(dests)
        self._db.flush()
        return dests

    def list_by_task(self, task_id: UUID) -> list[PutawayTaskDestinationModel]:
        return list(self._db.scalars(
            select(PutawayTaskDestinationModel).where(
                PutawayTaskDestinationModel.task_id == task_id
            ).order_by(PutawayTaskDestinationModel.sequence_number)
        ))

    def update_status(self, dest_id: UUID, *, status: str) -> None:
        self._db.execute(
            update(PutawayTaskDestinationModel)
            .where(PutawayTaskDestinationModel.id == dest_id)
            .values(status=status)
        )
        self._db.flush()


# =============================================================================
# 13. PutawayTaskAssignmentRepository
# =============================================================================
class PutawayTaskAssignmentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, assignment: PutawayTaskAssignmentModel) -> PutawayTaskAssignmentModel:
        self._db.add(assignment)
        self._db.flush()
        return assignment

    def get_active_for_task(self, task_id: UUID) -> PutawayTaskAssignmentModel | None:
        return self._db.execute(
            select(PutawayTaskAssignmentModel).where(
                PutawayTaskAssignmentModel.task_id == task_id,
                PutawayTaskAssignmentModel.status == "ASSIGNED",
            ).order_by(PutawayTaskAssignmentModel.assigned_at.desc()).limit(1)
        ).scalar_one_or_none()

    def list_by_user(self, user_id: UUID, *, status: str | None = None) -> list[PutawayTaskAssignmentModel]:
        filters = [PutawayTaskAssignmentModel.user_id == user_id]
        if status:
            filters.append(PutawayTaskAssignmentModel.status == status)
        return list(self._db.scalars(
            select(PutawayTaskAssignmentModel).where(*filters)
        ))

    def update_status(self, assignment_id: UUID, *, status: str, **extra) -> None:
        values = {"status": status}
        values.update(extra)
        self._db.execute(
            update(PutawayTaskAssignmentModel)
            .where(PutawayTaskAssignmentModel.id == assignment_id)
            .values(**values)
        )
        self._db.flush()

    def count_by_user_status(self, user_id: UUID, status: str) -> int:
        return self._db.scalar(
            select(func.count()).select_from(PutawayTaskAssignmentModel).where(
                PutawayTaskAssignmentModel.user_id == user_id,
                PutawayTaskAssignmentModel.status == status,
            )
        ) or 0


# =============================================================================
# 14. PutawayLocationReservationRepository
# =============================================================================
class PutawayLocationReservationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, reservation_id: UUID) -> PutawayLocationReservationModel | None:
        return self._db.get(PutawayLocationReservationModel, reservation_id)

    def create(self, reservation: PutawayLocationReservationModel) -> PutawayLocationReservationModel:
        self._db.add(reservation)
        self._db.flush()
        return reservation

    def get_active_for_location(self, location_id: UUID) -> PutawayLocationReservationModel | None:
        return self._db.execute(
            select(PutawayLocationReservationModel).where(
                PutawayLocationReservationModel.location_id == location_id,
                PutawayLocationReservationModel.status == "ACTIVE",
            )
        ).scalar_one_or_none()

    def get_active_for_task(self, task_id: UUID) -> PutawayLocationReservationModel | None:
        return self._db.execute(
            select(PutawayLocationReservationModel).where(
                PutawayLocationReservationModel.task_id == task_id,
                PutawayLocationReservationModel.status == "ACTIVE",
            )
        ).scalar_one_or_none()

    def sum_reserved_for_location(self, location_id: UUID) -> Decimal:
        result = self._db.scalar(
            select(func.coalesce(func.sum(PutawayLocationReservationModel.reserved_base_quantity), 0)).where(
                PutawayLocationReservationModel.location_id == location_id,
                PutawayLocationReservationModel.status == "ACTIVE",
            )
        )
        return Decimal(str(result))

    def list_expired(self, at: datetime | None = None) -> list[PutawayLocationReservationModel]:
        now = at or datetime.now(timezone.utc)
        return list(self._db.scalars(
            select(PutawayLocationReservationModel).where(
                PutawayLocationReservationModel.status == "ACTIVE",
                PutawayLocationReservationModel.expires_at <= now,
            )
        ))

    def update_status(self, reservation_id: UUID, *, status: str, **extra) -> None:
        values = {"status": status}
        values.update(extra)
        self._db.execute(
            update(PutawayLocationReservationModel)
            .where(PutawayLocationReservationModel.id == reservation_id)
            .values(**values)
        )
        self._db.flush()

    def release_expired(self, at: datetime | None = None) -> int:
        now = at or datetime.now(timezone.utc)
        result = self._db.execute(
            update(PutawayLocationReservationModel)
            .where(
                PutawayLocationReservationModel.status == "ACTIVE",
                PutawayLocationReservationModel.expires_at <= now,
            )
            .values(status="EXPIRED", released_at=now)
        )
        self._db.flush()
        return result.rowcount


# =============================================================================
# 15. PutawayExecutionSessionRepository
# =============================================================================
class PutawayExecutionSessionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, session_id: UUID) -> PutawayExecutionSessionModel | None:
        return self._db.get(PutawayExecutionSessionModel, session_id)

    def create(self, session: PutawayExecutionSessionModel) -> PutawayExecutionSessionModel:
        self._db.add(session)
        self._db.flush()
        return session

    def get_active_for_task(self, task_id: UUID) -> PutawayExecutionSessionModel | None:
        return self._db.execute(
            select(PutawayExecutionSessionModel).where(
                PutawayExecutionSessionModel.task_id == task_id,
                PutawayExecutionSessionModel.status == "ACTIVE",
            )
        ).scalar_one_or_none()

    def update_status(self, session_id: UUID, *, status: str, **extra) -> None:
        values = {"status": status}
        values.update(extra)
        self._db.execute(
            update(PutawayExecutionSessionModel)
            .where(PutawayExecutionSessionModel.id == session_id)
            .values(**values)
        )
        self._db.flush()

    def update_activity(self, session_id: UUID) -> None:
        self._db.execute(
            update(PutawayExecutionSessionModel)
            .where(PutawayExecutionSessionModel.id == session_id)
            .values(last_activity_at=datetime.now(timezone.utc))
        )
        self._db.flush()


# =============================================================================
# 16. PutawayScanEventRepository
# =============================================================================
class PutawayScanEventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, event_id: UUID) -> PutawayScanEventModel | None:
        return self._db.get(PutawayScanEventModel, event_id)

    def create(self, event: PutawayScanEventModel) -> PutawayScanEventModel:
        self._db.add(event)
        self._db.flush()
        return event

    def get_by_client_scan_id(self, session_id: UUID, client_scan_id: str) -> PutawayScanEventModel | None:
        return self._db.execute(
            select(PutawayScanEventModel).where(
                PutawayScanEventModel.execution_session_id == session_id,
                PutawayScanEventModel.client_scan_id == client_scan_id,
            )
        ).scalar_one_or_none()

    def next_server_sequence(self, session_id: UUID) -> int:
        result = self._db.scalar(
            select(func.max(PutawayScanEventModel.server_sequence)).where(
                PutawayScanEventModel.execution_session_id == session_id
            )
        )
        return (result or 0) + 1

    def list_by_task(self, task_id: UUID) -> list[PutawayScanEventModel]:
        return list(self._db.scalars(
            select(PutawayScanEventModel).where(
                PutawayScanEventModel.task_id == task_id
            ).order_by(PutawayScanEventModel.server_sequence)
        ))

    def list_by_session(self, session_id: UUID) -> list[PutawayScanEventModel]:
        return list(self._db.scalars(
            select(PutawayScanEventModel).where(
                PutawayScanEventModel.execution_session_id == session_id
            ).order_by(PutawayScanEventModel.server_sequence)
        ))

    def has_product_scan(self, session_id: UUID) -> bool:
        return self._db.scalar(
            select(func.count()).select_from(PutawayScanEventModel).where(
                PutawayScanEventModel.execution_session_id == session_id,
                PutawayScanEventModel.scan_type == "PRODUCT",
                PutawayScanEventModel.resolution_status == "MATCHED",
            )
        ) > 0

    def has_location_scan(self, session_id: UUID) -> bool:
        return self._db.scalar(
            select(func.count()).select_from(PutawayScanEventModel).where(
                PutawayScanEventModel.execution_session_id == session_id,
                PutawayScanEventModel.scan_type == "LOCATION",
                PutawayScanEventModel.resolution_status == "MATCHED",
            )
        ) > 0


# =============================================================================
# 17. PutawayPlacementConfirmationRepository
# =============================================================================
class PutawayPlacementConfirmationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, confirmation_id: UUID) -> PutawayPlacementConfirmationModel | None:
        return self._db.get(PutawayPlacementConfirmationModel, confirmation_id)

    def create(self, confirmation: PutawayPlacementConfirmationModel) -> PutawayPlacementConfirmationModel:
        self._db.add(confirmation)
        self._db.flush()
        return confirmation

    def list_by_task(self, task_id: UUID) -> list[PutawayPlacementConfirmationModel]:
        return list(self._db.scalars(
            select(PutawayPlacementConfirmationModel).where(
                PutawayPlacementConfirmationModel.task_id == task_id
            ).order_by(PutawayPlacementConfirmationModel.created_at)
        ))

    def sum_placed_for_allocation(self, source_allocation_id: UUID) -> Decimal:
        result = self._db.scalar(
            select(func.coalesce(func.sum(PutawayPlacementConfirmationModel.base_quantity), 0)).where(
                PutawayPlacementConfirmationModel.source_allocation_id == source_allocation_id,
                PutawayPlacementConfirmationModel.confirmation_status == "CONFIRMED",
            )
        )
        return Decimal(str(result))

    def get_by_hash(self, content_hash: str) -> PutawayPlacementConfirmationModel | None:
        return self._db.execute(
            select(PutawayPlacementConfirmationModel).where(
                PutawayPlacementConfirmationModel.content_hash == content_hash
            )
        ).scalar_one_or_none()


# =============================================================================
# 18. PutawayLocationOverrideRepository
# =============================================================================
class PutawayLocationOverrideRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, override: PutawayLocationOverrideModel) -> PutawayLocationOverrideModel:
        self._db.add(override)
        self._db.flush()
        return override

    def list_by_task(self, task_id: UUID) -> list[PutawayLocationOverrideModel]:
        return list(self._db.scalars(
            select(PutawayLocationOverrideModel).where(
                PutawayLocationOverrideModel.task_id == task_id
            ).order_by(PutawayLocationOverrideModel.created_at)
        ))

    def approve(self, override_id: UUID, approved_by: UUID, step_up_summary: dict | None = None) -> None:
        self._db.execute(
            update(PutawayLocationOverrideModel)
            .where(PutawayLocationOverrideModel.id == override_id)
            .values(approved_by=approved_by, step_up_assurance_summary=step_up_summary)
        )
        self._db.flush()


# =============================================================================
# 19. PutawayTaskExceptionRepository
# =============================================================================
class PutawayTaskExceptionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, exception_id: UUID) -> PutawayTaskExceptionModel | None:
        return self._db.get(PutawayTaskExceptionModel, exception_id)

    def create(self, exc: PutawayTaskExceptionModel) -> PutawayTaskExceptionModel:
        self._db.add(exc)
        self._db.flush()
        return exc

    def list_by_task(self, task_id: UUID, *, status: str | None = None) -> list[PutawayTaskExceptionModel]:
        filters = [PutawayTaskExceptionModel.task_id == task_id]
        if status:
            filters.append(PutawayTaskExceptionModel.status == status)
        return list(self._db.scalars(
            select(PutawayTaskExceptionModel).where(*filters)
        ))

    def count_open_by_task(self, task_id: UUID) -> int:
        return self._db.scalar(
            select(func.count()).select_from(PutawayTaskExceptionModel).where(
                PutawayTaskExceptionModel.task_id == task_id,
                PutawayTaskExceptionModel.status == "OPEN",
            )
        ) or 0

    def update_status(self, exception_id: UUID, *, status: str, resolved_by: UUID | None = None,
                      resolution: str | None = None) -> None:
        values = {"status": status}
        if resolved_by:
            values["resolved_by"] = resolved_by
            values["resolved_at"] = datetime.now(timezone.utc)
        if resolution:
            values["resolution"] = resolution
        self._db.execute(
            update(PutawayTaskExceptionModel)
            .where(PutawayTaskExceptionModel.id == exception_id)
            .values(**values)
        )
        self._db.flush()


# =============================================================================
# 20. PutawayTaskPauseRepository
# =============================================================================
class PutawayTaskPauseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, pause: PutawayTaskPauseModel) -> PutawayTaskPauseModel:
        self._db.add(pause)
        self._db.flush()
        return pause

    def get_active_for_task(self, task_id: UUID) -> PutawayTaskPauseModel | None:
        return self._db.execute(
            select(PutawayTaskPauseModel).where(
                PutawayTaskPauseModel.task_id == task_id,
                PutawayTaskPauseModel.resumed_at.is_(None),
            ).order_by(PutawayTaskPauseModel.paused_at.desc()).limit(1)
        ).scalar_one_or_none()

    def resume(self, pause_id: UUID) -> None:
        self._db.execute(
            update(PutawayTaskPauseModel)
            .where(PutawayTaskPauseModel.id == pause_id)
            .values(resumed_at=datetime.now(timezone.utc))
        )
        self._db.flush()

    def list_by_task(self, task_id: UUID) -> list[PutawayTaskPauseModel]:
        return list(self._db.scalars(
            select(PutawayTaskPauseModel).where(
                PutawayTaskPauseModel.task_id == task_id
            ).order_by(PutawayTaskPauseModel.paused_at.desc())
        ))


# =============================================================================
# 21. OperationalInventoryPlacementRepository
# =============================================================================
class OperationalInventoryPlacementRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, placement_id: UUID) -> OperationalInventoryPlacementModel | None:
        return self._db.get(OperationalInventoryPlacementModel, placement_id)

    def create(self, placement: OperationalInventoryPlacementModel) -> OperationalInventoryPlacementModel:
        self._db.add(placement)
        self._db.flush()
        return placement

    def list_by_location(self, location_id: UUID, *, product_id: UUID | None = None) -> list[OperationalInventoryPlacementModel]:
        filters = [OperationalInventoryPlacementModel.location_id == location_id]
        if product_id:
            filters.append(OperationalInventoryPlacementModel.product_id == product_id)
        return list(self._db.scalars(
            select(OperationalInventoryPlacementModel).where(*filters)
        ))

    def sum_quantity_by_location_product(self, location_id: UUID, product_id: UUID) -> Decimal:
        result = self._db.scalar(
            select(func.coalesce(func.sum(OperationalInventoryPlacementModel.base_quantity), 0)).where(
                OperationalInventoryPlacementModel.location_id == location_id,
                OperationalInventoryPlacementModel.product_id == product_id,
                OperationalInventoryPlacementModel.status != "CANCELLED",
            )
        )
        return Decimal(str(result))

    def count_by_order(self, putaway_order_id: UUID) -> int:
        return self._db.scalar(
            select(func.count()).select_from(OperationalInventoryPlacementModel).where(
                OperationalInventoryPlacementModel.putaway_order_id == putaway_order_id
            )
        ) or 0

    def list_by_order(self, putaway_order_id: UUID) -> list[OperationalInventoryPlacementModel]:
        return list(self._db.scalars(
            select(OperationalInventoryPlacementModel).where(
                OperationalInventoryPlacementModel.putaway_order_id == putaway_order_id
            )
        ))

    def get_by_hash(self, content_hash: str) -> OperationalInventoryPlacementModel | None:
        return self._db.execute(
            select(OperationalInventoryPlacementModel).where(
                OperationalInventoryPlacementModel.content_hash == content_hash
            )
        ).scalar_one_or_none()


# =============================================================================
# 22. PutawayLocationPlacementProjectionRepository
# =============================================================================
class PutawayLocationPlacementProjectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_or_none(
        self, organization_id: UUID, warehouse_id: UUID,
        location_id: UUID, product_id: UUID,
    ) -> PutawayLocationPlacementProjectionModel | None:
        return self._db.execute(
            select(PutawayLocationPlacementProjectionModel).where(
                PutawayLocationPlacementProjectionModel.organization_id == organization_id,
                PutawayLocationPlacementProjectionModel.warehouse_id == warehouse_id,
                PutawayLocationPlacementProjectionModel.location_id == location_id,
                PutawayLocationPlacementProjectionModel.product_id == product_id,
            )
        ).scalar_one_or_none()

    def upsert(self, projection: PutawayLocationPlacementProjectionModel) -> PutawayLocationPlacementProjectionModel:
        existing = self.get_or_none(
            projection.organization_id, projection.warehouse_id,
            projection.location_id, projection.product_id,
        )
        if existing:
            for field in (
                "quantity", "base_quantity", "placement_count",
                "active_reservation_value", "operational_capacity_used",
                "operational_capacity_free", "data_quality_status",
                "last_putaway_at", "calculated_at",
            ):
                setattr(existing, field, getattr(projection, field))
            existing.projection_version += 1
            self._db.flush()
            return existing
        self._db.add(projection)
        self._db.flush()
        return projection

    def list_by_location(self, location_id: UUID) -> list[PutawayLocationPlacementProjectionModel]:
        return list(self._db.scalars(
            select(PutawayLocationPlacementProjectionModel).where(
                PutawayLocationPlacementProjectionModel.location_id == location_id
            )
        ))

    def list_by_product(self, organization_id: UUID, product_id: UUID) -> list[PutawayLocationPlacementProjectionModel]:
        return list(self._db.scalars(
            select(PutawayLocationPlacementProjectionModel).where(
                PutawayLocationPlacementProjectionModel.organization_id == organization_id,
                PutawayLocationPlacementProjectionModel.product_id == product_id,
            )
        ))

    def update_quantity(
        self, organization_id: UUID, warehouse_id: UUID,
        location_id: UUID, product_id: UUID,
        *, quantity_delta: Decimal, base_quantity_delta: Decimal,
    ) -> None:
        existing = self.get_or_none(organization_id, warehouse_id, location_id, product_id)
        if existing:
            existing.quantity += quantity_delta
            existing.base_quantity += base_quantity_delta
            existing.calculated_at = datetime.now(timezone.utc)
            existing.projection_version += 1
            self._db.flush()
        else:
            projection = PutawayLocationPlacementProjectionModel(
                organization_id=organization_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                product_id=product_id,
                quantity=quantity_delta,
                base_quantity=base_quantity_delta,
                placement_count=1 if quantity_delta > 0 else 0,
                calculated_at=datetime.now(timezone.utc),
            )
            self._db.add(projection)
            self._db.flush()


# =============================================================================
# Utility: compute content hash
# =============================================================================
def compute_content_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()
