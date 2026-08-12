"""Phase 041. Quality plan metrics projection service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityPlanScopeModel,
    QualityControlDefinitionModel,
    QualityToleranceDefinitionModel,
    QualitySamplingPlanModel,
    QualityCertificateRequirementModel,
    QualityPlanReferenceFileModel,
    QualityPlanUsageProjectionModel,
)


class QualityPlanMetricsProjectionService:
    def __init__(self, db: Session):
        self.db = db

    def update_metrics(self, plan_id: UUID, organization_id: UUID) -> dict[str, Any]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            return {}

        scopes_count = self.db.scalar(
            select(func.count()).select_from(
                select(QualityPlanScopeModel).where(QualityPlanScopeModel.plan_id == plan_id).subquery()
            )
        ) or 0

        controls = list(
            self.db.scalars(
                select(QualityControlDefinitionModel).where(
                    QualityControlDefinitionModel.plan_id == plan_id,
                )
            )
        )
        controls_count = len(controls)
        mandatory_count = sum(1 for c in controls if c.is_mandatory)
        blocking_count = sum(1 for c in controls if c.is_blocking)

        control_ids = [c.id for c in controls]

        tolerances_count = 0
        sampling_count = 0
        certificate_count = 0
        if control_ids:
            tolerances_count = self.db.scalar(
                select(func.count()).select_from(
                    select(QualityToleranceDefinitionModel).where(
                        QualityToleranceDefinitionModel.control_id.in_(control_ids)
                    ).subquery()
                )
            ) or 0
            sampling_count = self.db.scalar(
                select(func.count()).select_from(
                    select(QualitySamplingPlanModel).where(
                        QualitySamplingPlanModel.control_id.in_(control_ids)
                    ).subquery()
                )
            ) or 0
            certificate_count = self.db.scalar(
                select(func.count()).select_from(
                    select(QualityCertificateRequirementModel).where(
                        QualityCertificateRequirementModel.control_id.in_(control_ids)
                    ).subquery()
                )
            ) or 0

        ref_files_count = self.db.scalar(
            select(func.count()).select_from(
                select(QualityPlanReferenceFileModel).where(
                    QualityPlanReferenceFileModel.plan_id == plan_id,
                ).subquery()
            )
        ) or 0

        product_scopes = self.db.scalar(
            select(func.count()).select_from(
                select(QualityPlanScopeModel).where(
                    QualityPlanScopeModel.plan_id == plan_id,
                    QualityPlanScopeModel.scope_type == "PRODUCT",
                ).subquery()
            )
        ) or 0

        category_scopes = self.db.scalar(
            select(func.count()).select_from(
                select(QualityPlanScopeModel).where(
                    QualityPlanScopeModel.plan_id == plan_id,
                    QualityPlanScopeModel.scope_type == "PRODUCT_CATEGORY",
                ).subquery()
            )
        ) or 0

        existing = self.db.scalar(
            select(QualityPlanUsageProjectionModel).where(
                QualityPlanUsageProjectionModel.plan_id == plan_id,
            )
        )
        if existing:
            existing.total_scopes = scopes_count
            existing.total_controls = controls_count
            existing.mandatory_controls = mandatory_count
            existing.blocking_controls = blocking_count
            existing.total_tolerances = tolerances_count
            existing.total_sampling_plans = sampling_count
            existing.total_certificate_requirements = certificate_count
            existing.total_reference_files = ref_files_count
            existing.resolved_for_products = product_scopes
            existing.resolved_for_categories = category_scopes
            existing.calculated_at = datetime.now().astimezone()
            metrics = existing
        else:
            metrics = QualityPlanUsageProjectionModel(
                plan_id=plan_id,
                organization_id=organization_id,
                total_scopes=scopes_count,
                total_controls=controls_count,
                mandatory_controls=mandatory_count,
                blocking_controls=blocking_count,
                total_tolerances=tolerances_count,
                total_sampling_plans=sampling_count,
                total_certificate_requirements=certificate_count,
                total_reference_files=ref_files_count,
                resolved_for_products=product_scopes,
                resolved_for_categories=category_scopes,
            )
            self.db.add(metrics)

        self.db.flush()

        return {
            "plan_id": str(plan_id),
            "total_scopes": scopes_count,
            "total_controls": controls_count,
            "mandatory_controls": mandatory_count,
            "blocking_controls": blocking_count,
            "total_tolerances": tolerances_count,
            "total_sampling_plans": sampling_count,
            "total_certificate_requirements": certificate_count,
            "total_reference_files": ref_files_count,
            "resolved_for_products": product_scopes,
            "resolved_for_categories": category_scopes,
        }

    def get_metrics(self, plan_id: UUID) -> dict[str, Any] | None:
        existing = self.db.scalar(
            select(QualityPlanUsageProjectionModel).where(
                QualityPlanUsageProjectionModel.plan_id == plan_id,
            )
        )
        if not existing:
            return None
        return {
            "plan_id": str(existing.plan_id),
            "total_scopes": existing.total_scopes,
            "total_controls": existing.total_controls,
            "mandatory_controls": existing.mandatory_controls,
            "blocking_controls": existing.blocking_controls,
            "total_tolerances": existing.total_tolerances,
            "total_sampling_plans": existing.total_sampling_plans,
            "total_certificate_requirements": existing.total_certificate_requirements,
            "total_reference_files": existing.total_reference_files,
            "resolved_for_products": existing.resolved_for_products,
            "resolved_for_categories": existing.resolved_for_categories,
            "calculated_at": existing.calculated_at.isoformat() if existing.calculated_at else None,
        }
