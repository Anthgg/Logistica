"""Phase 041. Quality plan reference files service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanReferenceFileInvalid,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityPlanReferenceFileModel,
    QualityInspectionPlanModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


class QualityPlanReferenceFileService:
    def __init__(self, db: Session):
        self.db = db

    def get_reference_file(self, reference_file_id: UUID) -> QualityPlanReferenceFileModel:
        rf = self.db.scalar(
            select(QualityPlanReferenceFileModel).where(
                QualityPlanReferenceFileModel.id == reference_file_id,
            )
        )
        if not rf:
            raise quality_plan_error("QualityPlanReferenceFileNotFound", f"Archivo de referencia {reference_file_id} no encontrado", 404)
        return rf

    def list_reference_files(
        self,
        plan_id: UUID,
        organization_id: UUID,
    ) -> list[QualityPlanReferenceFileModel]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise quality_plan_error("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)
        return list(
            self.db.scalars(
                select(QualityPlanReferenceFileModel).where(
                    QualityPlanReferenceFileModel.plan_id == plan_id,
                )
            )
        )

    def link_reference_file(
        self,
        plan_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityPlanReferenceFileModel:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise quality_plan_error("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)
        if plan.status not in ("DRAFT",):
            raise quality_plan_error(
                "QualityPlanStatusInvalid",
                f"Solo se pueden vincular archivos a un plan en DRAFT (actual: {plan.status})",
                409,
            )

        rf = QualityPlanReferenceFileModel(
            id=uuid4(),
            plan_id=plan_id,
            version_id=data.get("version_id"),
            file_asset_id=data["file_asset_id"],
            file_version_id=data.get("file_version_id"),
            reference_type=data.get("reference_type", "MANUAL"),
            description=data.get("description"),
            linked_by=principal.user_id,
            content_hash=data.get("content_hash"),
        )
        self.db.add(rf)
        self.db.flush()
        return rf

    def unlink_reference_file(
        self,
        reference_file_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
    ) -> None:
        rf = self.get_reference_file(reference_file_id)
        self.db.delete(rf)
        self.db.flush()
