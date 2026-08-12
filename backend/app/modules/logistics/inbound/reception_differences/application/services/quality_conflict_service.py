"""Phase 041. Quality plan conflict detection and resolution service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import ResolutionSpecificity
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    compute_specificity_rank,
    resolve_plan_specificity,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityPlanScopeModel,
)


class QualityConflictDetectionService:
    def __init__(self, db: Session):
        self.db = db

    def detect_conflicts(
        self,
        organization_id: UUID,
        *,
        product_id: UUID | None = None,
        product_category_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        branch_id: UUID | None = None,
        exclude_plan_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        query = (
            select(QualityPlanScopeModel, QualityInspectionPlanModel)
            .join(QualityInspectionPlanModel, QualityPlanScopeModel.plan_id == QualityInspectionPlanModel.id)
            .where(
                QualityInspectionPlanModel.organization_id == organization_id,
                QualityInspectionPlanModel.status == "ACTIVE",
                QualityPlanScopeModel.is_active == True,
            )
        )
        if exclude_plan_id:
            query = query.where(QualityInspectionPlanModel.id != exclude_plan_id)

        rows = list(self.db.execute(query))
        conflicts = []
        for scope, plan in rows:
            if product_id and scope.scope_product_id and str(scope.scope_product_id) == str(product_id):
                if warehouse_id and scope.scope_warehouse_id and str(scope.scope_warehouse_id) == str(warehouse_id):
                    conflicts.append({
                        "plan_id": str(plan.id),
                        "plan_code": plan.plan_code,
                        "scope_id": str(scope.id),
                        "scope_type": scope.scope_type,
                        "conflict_type": "EXACT_PRODUCT_WAREHOUSE",
                    })
                elif branch_id and scope.scope_branch_id and str(scope.scope_branch_id) == str(branch_id):
                    conflicts.append({
                        "plan_id": str(plan.id),
                        "plan_code": plan.plan_code,
                        "scope_id": str(scope.id),
                        "scope_type": scope.scope_type,
                        "conflict_type": "EXACT_PRODUCT_BRANCH",
                    })
            if product_category_id and scope.scope_category_id and str(scope.scope_category_id) == str(product_category_id):
                if warehouse_id and scope.scope_warehouse_id and str(scope.scope_warehouse_id) == str(warehouse_id):
                    conflicts.append({
                        "plan_id": str(plan.id),
                        "plan_code": plan.plan_code,
                        "scope_id": str(scope.id),
                        "scope_type": scope.scope_type,
                        "conflict_type": "CATEGORY_WAREHOUSE",
                    })
        return conflicts

    def resolve_for_context(
        self,
        organization_id: UUID,
        *,
        product_id: UUID | None = None,
        product_category_id: UUID | None = None,
        warehouse_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> dict[str, Any]:
        query = (
            select(QualityPlanScopeModel, QualityInspectionPlanModel)
            .join(QualityInspectionPlanModel, QualityPlanScopeModel.plan_id == QualityInspectionPlanModel.id)
            .where(
                QualityInspectionPlanModel.organization_id == organization_id,
                QualityInspectionPlanModel.status == "ACTIVE",
                QualityPlanScopeModel.is_active == True,
            )
        )
        rows = list(self.db.execute(query))

        plans_data = []
        for scope, plan in rows:
            plans_data.append({
                "id": str(plan.id),
                "plan_id": str(plan.id),
                "plan_code": plan.plan_code,
                "scope_type": scope.scope_type,
                "scope_product_id": str(scope.scope_product_id) if scope.scope_product_id else None,
                "scope_category_id": str(scope.scope_category_id) if scope.scope_category_id else None,
                "scope_warehouse_id": str(scope.scope_warehouse_id) if scope.scope_warehouse_id else None,
                "scope_branch_id": str(scope.scope_branch_id) if scope.scope_branch_id else None,
            })

        plan_id, specificity = resolve_plan_specificity(
            product_id=product_id,
            product_category_id=product_category_id,
            warehouse_id=warehouse_id,
            branch_id=branch_id,
            plans=plans_data,
        )

        return {
            "resolved_plan_id": plan_id,
            "resolution_specificity": specificity,
            "candidate_plans_count": len(plans_data),
        }
