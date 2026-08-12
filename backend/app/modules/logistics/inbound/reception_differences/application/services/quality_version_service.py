"""Phase 041. Quality inspection plan version management service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import (
    VersionStatus,
    PLAN_STATUS_TRANSITIONS,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanNotFound,
    QualityPlanVersionNotFound,
    QualityPlanVersionStatusInvalid,
    QualityPlanActivationFailed,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    canonical_hash_quality_plan,
    require_version_transition,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityInspectionPlanVersionModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


class QualityPlanVersionService:
    def __init__(self, db: Session):
        self.db = db

    def get_version(self, version_id: UUID, organization_id: UUID) -> QualityInspectionPlanVersionModel:
        version = self.db.scalar(
            select(QualityInspectionPlanVersionModel)
            .join(QualityInspectionPlanModel)
            .where(
                QualityInspectionPlanVersionModel.id == version_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not version:
            raise QualityPlanVersionNotFound("QualityPlanVersionNotFound", f"Versión {version_id} no encontrada", 404)
        return version

    def list_versions(
        self,
        plan_id: UUID,
        organization_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[QualityInspectionPlanVersionModel], int]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)

        query = select(QualityInspectionPlanVersionModel).where(
            QualityInspectionPlanVersionModel.plan_id == plan_id,
        )
        total = self.db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
        query = query.order_by(QualityInspectionPlanVersionModel.version_number.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        rows = list(self.db.scalars(query))
        return rows, total

    def create_version(
        self,
        plan_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityInspectionPlanVersionModel:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)
        if plan.status not in ("DRAFT", "ACTIVE"):
            raise QualityPlanActivationFailed(
                "QualityPlanActivationFailed",
                f"No se puede crear versión para plan en estado {plan.status}",
                409,
            )

        next_number = plan.current_version_number + 1
        version = QualityInspectionPlanVersionModel(
            id=uuid4(),
            plan_id=plan_id,
            version_number=next_number,
            status=VersionStatus.DRAFT,
            change_summary=data.get("change_summary"),
            plan_snapshot=data.get("plan_snapshot"),
            created_by=principal.user_id,
        )
        self.db.add(version)

        plan.current_version_number = next_number
        plan.updated_at = _now()
        plan.row_version += 1
        self.db.flush()
        return version

    def transition_version(
        self,
        version_id: UUID,
        organization_id: UUID,
        target_status: str,
        principal: LogisticsPrincipal,
        reason: str | None = None,
    ) -> QualityInspectionPlanVersionModel:
        version = self.get_version(version_id, organization_id)
        require_version_transition(version.status, target_status)

        version.status = target_status
        version.updated_at = _now()
        version.row_version += 1

        if target_status == VersionStatus.ACTIVATED or target_status == VersionStatus.ACTIVE:
            version.activated_at = _now()
            version.activated_by = principal.user_id
        elif target_status == VersionStatus.RETIRED:
            version.retired_at = _now()
            version.retired_by = principal.user_id

        self.db.flush()
        return version

    def activate_version(
        self,
        version_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
    ) -> QualityInspectionPlanVersionModel:
        version = self.get_version(version_id, organization_id)
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == version.plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {version.plan_id} no encontrado", 404)

        if version.status not in (VersionStatus.VALIDATED, VersionStatus.SCHEDULED):
            raise QualityPlanActivationFailed(
                "QualityPlanActivationFailed",
                f"La versión debe estar VALIDATED o SCHEDULED para activarla (actual: {version.status})",
                409,
            )

        if plan.active_version_id and str(plan.active_version_id) != str(version_id):
            old_version = self.db.scalar(
                select(QualityInspectionPlanVersionModel).where(
                    QualityInspectionPlanVersionModel.id == plan.active_version_id,
                )
            )
            if old_version and old_version.status == VersionStatus.ACTIVE:
                old_version.status = VersionStatus.SUPERSEDED
                old_version.updated_at = _now()
                old_version.row_version += 1

        version.status = VersionStatus.ACTIVE
        version.activated_at = _now()
        version.activated_by = principal.user_id
        version.updated_at = _now()
        version.row_version += 1

        plan.active_version_id = version_id
        plan.status = "ACTIVE"
        plan.updated_at = _now()
        plan.row_version += 1
        self.db.flush()
        return version

    def retire_version(
        self,
        version_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        reason: str | None = None,
    ) -> QualityInspectionPlanVersionModel:
        version = self.get_version(version_id, organization_id)
        if version.status != VersionStatus.ACTIVE:
            raise QualityPlanActivationFailed(
                "QualityPlanActivationFailed",
                f"Solo se puede retirar una versión activa (actual: {version.status})",
                409,
            )

        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == version.plan_id,
            )
        )
        if plan:
            plan.active_version_id = None
            plan.status = "INACTIVE"
            plan.updated_at = _now()
            plan.row_version += 1

        version.status = VersionStatus.RETIRED
        version.retired_at = _now()
        version.retired_by = principal.user_id
        version.updated_at = _now()
        version.row_version += 1
        self.db.flush()
        return version

    def compute_content_hash(self, version_id: UUID, organization_id: UUID) -> str:
        version = self.get_version(version_id, organization_id)
        snapshot = version.plan_snapshot or {}
        h = canonical_hash_quality_plan(snapshot)
        version.content_hash = h
        version.updated_at = _now()
        self.db.flush()
        return h
