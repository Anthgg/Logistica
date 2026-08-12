"""Phase 041. Quality plan integrity verification service."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanIntegrityFailed,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    canonical_hash_quality_plan,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityInspectionPlanVersionModel,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_snapshot_service import (
    QualityPlanSnapshotProvider,
)


class QualityPlanIntegrityService:
    def __init__(self, db: Session):
        self.db = db

    def verify(self, plan_id: UUID, organization_id: UUID) -> dict[str, Any]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise quality_plan_error("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)

        snapshot = QualityPlanSnapshotProvider(self.db).capture(plan_id, organization_id)
        computed_hash = snapshot.get("content_hash")

        stored_hash = plan.content_hash if hasattr(plan, "content_hash") else None

        status = "VALID"
        if stored_hash and computed_hash != stored_hash:
            status = "MISMATCH"

        return {
            "plan_id": str(plan_id),
            "plan_code": plan.plan_code,
            "status": status,
            "stored_hash": stored_hash,
            "computed_hash": computed_hash,
            "verified_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        }
