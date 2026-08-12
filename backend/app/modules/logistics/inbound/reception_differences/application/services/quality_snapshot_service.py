"""Phase 041. Quality plan snapshot provider."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanSnapshotFailed,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    canonical_hash_quality_plan,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityInspectionPlanVersionModel,
    QualityPlanScopeModel,
    QualityControlDefinitionModel,
    QualityToleranceDefinitionModel,
    QualitySamplingPlanModel,
    QualityCertificateRequirementModel,
    QualityControlApplicabilityConditionModel,
    QualityPlanReferenceFileModel,
)


class QualityPlanSnapshotProvider:
    def __init__(self, db: Session):
        self.db = db

    def capture(self, plan_id: UUID, organization_id: UUID) -> dict[str, Any]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise quality_plan_error("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)

        scopes = list(
            self.db.scalars(
                select(QualityPlanScopeModel).where(QualityPlanScopeModel.plan_id == plan_id)
            )
        )
        controls = list(
            self.db.scalars(
                select(QualityControlDefinitionModel).where(
                    QualityControlDefinitionModel.plan_id == plan_id,
                )
            )
        )

        tolerances_map: dict[str, list] = {}
        sampling_map: dict[str, list] = {}
        certificate_map: dict[str, list] = {}
        condition_map: dict[str, list] = {}

        for ctrl in controls:
            ctrl_id = str(ctrl.id)
            tolerances_map[ctrl_id] = list(
                self.db.scalars(
                    select(QualityToleranceDefinitionModel).where(
                        QualityToleranceDefinitionModel.control_id == ctrl.id,
                    )
                )
            )
            sampling_map[ctrl_id] = list(
                self.db.scalars(
                    select(QualitySamplingPlanModel).where(
                        QualitySamplingPlanModel.control_id == ctrl.id,
                    )
                )
            )
            certificate_map[ctrl_id] = list(
                self.db.scalars(
                    select(QualityCertificateRequirementModel).where(
                        QualityCertificateRequirementModel.control_id == ctrl.id,
                    )
                )
            )
            condition_map[ctrl_id] = list(
                self.db.scalars(
                    select(QualityControlApplicabilityConditionModel).where(
                        QualityControlApplicabilityConditionModel.control_id == ctrl.id,
                    )
                )
            )

        ref_files = list(
            self.db.scalars(
                select(QualityPlanReferenceFileModel).where(
                    QualityPlanReferenceFileModel.plan_id == plan_id,
                )
            )
        )

        snapshot = {
            "canonicalization_version": "1.0",
            "plan": {
                "id": str(plan.id),
                "plan_code": plan.plan_code,
                "plan_name": plan.plan_name,
                "description": plan.description,
                "plan_family": plan.plan_family,
                "status": plan.status,
                "current_version_number": plan.current_version_number,
                "is_global": plan.is_global,
                "priority": plan.priority,
            },
            "scopes": [
                {
                    "id": str(s.id),
                    "scope_type": s.scope_type,
                    "scope_product_id": str(s.scope_product_id) if s.scope_product_id else None,
                    "scope_category_id": str(s.scope_category_id) if s.scope_category_id else None,
                    "scope_warehouse_id": str(s.scope_warehouse_id) if s.scope_warehouse_id else None,
                    "scope_branch_id": str(s.scope_branch_id) if s.scope_branch_id else None,
                    "resolution_specificity": s.resolution_specificity,
                    "is_active": s.is_active,
                }
                for s in scopes
            ],
            "controls": [
                {
                    "id": str(c.id),
                    "control_type": c.control_type,
                    "control_code": c.control_code,
                    "control_name": c.control_name,
                    "display_order": c.display_order,
                    "is_mandatory": c.is_mandatory,
                    "is_blocking": c.is_blocking,
                    "tolerances": [
                        {
                            "id": str(t.id),
                            "tolerance_type": t.tolerance_type,
                            "min_value": str(t.min_value) if t.min_value else None,
                            "max_value": str(t.max_value) if t.max_value else None,
                            "target_value": str(t.target_value) if t.target_value else None,
                        }
                        for t in tolerances_map.get(str(c.id), [])
                    ],
                    "samplings": [
                        {
                            "id": str(sp.id),
                            "sampling_type": sp.sampling_type,
                            "fixed_count": sp.fixed_count,
                            "percentage": str(sp.percentage) if sp.percentage else None,
                        }
                        for sp in sampling_map.get(str(c.id), [])
                    ],
                    "certificates": [
                        {
                            "id": str(cr.id),
                            "certificate_type": cr.certificate_type,
                            "is_mandatory": cr.is_mandatory,
                        }
                        for cr in certificate_map.get(str(c.id), [])
                    ],
                }
                for c in controls
            ],
            "reference_files": [
                {
                    "id": str(rf.id),
                    "file_asset_id": str(rf.file_asset_id),
                    "reference_type": rf.reference_type,
                }
                for rf in ref_files
            ],
            "captured_at": datetime.now().astimezone().isoformat(),
        }

        content_hash = canonical_hash_quality_plan(snapshot)
        snapshot["content_hash"] = content_hash
        return snapshot
