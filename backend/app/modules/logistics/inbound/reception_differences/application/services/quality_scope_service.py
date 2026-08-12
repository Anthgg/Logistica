"""Phase 041. Quality plan scope management service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanNotFound,
    QualityPlanScopeNotFound,
    QualityPlanScopeDuplicate,
    QualityPlanScopeConflict,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityPlanScopeModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


class QualityPlanScopeService:
    def __init__(self, db: Session):
        self.db = db

    def get_scope(self, scope_id: UUID, organization_id: UUID) -> QualityPlanScopeModel:
        scope = self.db.scalar(
            select(QualityPlanScopeModel)
            .join(QualityInspectionPlanModel)
            .where(
                QualityPlanScopeModel.id == scope_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not scope:
            raise QualityPlanScopeNotFound("QualityPlanScopeNotFound", f"Ámbito {scope_id} no encontrado", 404)
        return scope

    def list_scopes(
        self,
        plan_id: UUID,
        organization_id: UUID,
    ) -> list[QualityPlanScopeModel]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)
        return list(
            self.db.scalars(
                select(QualityPlanScopeModel).where(QualityPlanScopeModel.plan_id == plan_id)
            )
        )

    def create_scope(
        self,
        plan_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityPlanScopeModel:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)
        if plan.status not in ("DRAFT",):
            raise quality_plan_error(
                "QualityPlanStatusInvalid",
                f"Solo se puede editar ámbitos de un plan en DRAFT (actual: {plan.status})",
                409,
            )

        existing = self.db.scalar(
            select(QualityPlanScopeModel).where(
                QualityPlanScopeModel.plan_id == plan_id,
                QualityPlanScopeModel.scope_type == data["scope_type"],
                QualityPlanScopeModel.scope_product_id == data.get("scope_product_id"),
                QualityPlanScopeModel.scope_category_id == data.get("scope_category_id"),
                QualityPlanScopeModel.scope_warehouse_id == data.get("scope_warehouse_id"),
                QualityPlanScopeModel.scope_branch_id == data.get("scope_branch_id"),
            )
        )
        if existing:
            raise QualityPlanScopeDuplicate(
                "QualityPlanScopeDuplicate",
                "Ya existe un ámbito idéntico para este plan",
                409,
            )

        scope = QualityPlanScopeModel(
            id=uuid4(),
            plan_id=plan_id,
            version_id=data.get("version_id"),
            scope_type=data["scope_type"],
            scope_product_id=data.get("scope_product_id"),
            scope_product_name=data.get("scope_product_name"),
            scope_category_id=data.get("scope_category_id"),
            scope_category_name=data.get("scope_category_name"),
            scope_warehouse_id=data.get("scope_warehouse_id"),
            scope_warehouse_name=data.get("scope_warehouse_name"),
            scope_branch_id=data.get("scope_branch_id"),
            scope_branch_name=data.get("scope_branch_name"),
            resolution_specificity=data.get("resolution_specificity"),
            is_active=data.get("is_active", True),
        )
        self.db.add(scope)
        self.db.flush()
        return scope

    def update_scope(
        self,
        scope_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityPlanScopeModel:
        scope = self.get_scope(scope_id, organization_id)
        for field in ("resolution_specificity", "is_active", "scope_product_name", "scope_category_name", "scope_warehouse_name", "scope_branch_name"):
            if field in data and data[field] is not None:
                setattr(scope, field, data[field])
        self.db.flush()
        return scope

    def delete_scope(self, scope_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> None:
        scope = self.get_scope(scope_id, organization_id)
        self.db.delete(scope)
        self.db.flush()
