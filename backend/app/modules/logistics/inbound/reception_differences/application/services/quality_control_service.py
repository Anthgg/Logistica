"""Phase 041. Quality control definition management service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import ControlType
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanNotFound,
    QualityPlanControlNotFound,
    QualityPlanControlDuplicate,
    QualityPlanControlTypeInvalid,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityControlDefinitionModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


class QualityControlService:
    def __init__(self, db: Session):
        self.db = db

    def get_control(self, control_id: UUID, organization_id: UUID) -> QualityControlDefinitionModel:
        ctrl = self.db.scalar(
            select(QualityControlDefinitionModel)
            .join(QualityInspectionPlanModel)
            .where(
                QualityControlDefinitionModel.id == control_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not ctrl:
            raise QualityPlanControlNotFound("QualityPlanControlNotFound", f"Control {control_id} no encontrado", 404)
        return ctrl

    def list_controls(
        self,
        plan_id: UUID,
        organization_id: UUID,
        *,
        scope_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[QualityControlDefinitionModel], int]:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)

        query = select(QualityControlDefinitionModel).where(
            QualityControlDefinitionModel.plan_id == plan_id,
        )
        if scope_id:
            query = query.where(QualityControlDefinitionModel.scope_id == scope_id)

        total = self.db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
        query = query.order_by(QualityControlDefinitionModel.display_order.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        rows = list(self.db.scalars(query))
        return rows, total

    def create_control(
        self,
        plan_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityControlDefinitionModel:
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
                f"Solo se puede editar controles de un plan en DRAFT (actual: {plan.status})",
                409,
            )

        control_type = data.get("control_type")
        valid_types = [t.value for t in ControlType]
        if control_type not in valid_types:
            raise QualityPlanControlTypeInvalid(
                "QualityPlanControlTypeInvalid",
                f"Tipo de control '{control_type}' no es válido. Válidos: {valid_types}",
                400,
            )

        existing = self.db.scalar(
            select(QualityControlDefinitionModel).where(
                QualityControlDefinitionModel.plan_id == plan_id,
                QualityControlDefinitionModel.control_code == data.get("control_code"),
            )
        )
        if existing:
            raise QualityPlanControlDuplicate(
                "QualityPlanControlDuplicate",
                f"Ya existe un control con código '{data.get('control_code')}' en este plan",
                409,
            )

        ctrl = QualityControlDefinitionModel(
            id=uuid4(),
            plan_id=plan_id,
            version_id=data.get("version_id"),
            scope_id=data.get("scope_id"),
            control_type=control_type,
            control_code=data["control_code"],
            control_name=data["control_name"],
            description=data.get("description"),
            display_order=data.get("display_order", 0),
            is_mandatory=data.get("is_mandatory", True),
            is_blocking=data.get("is_blocking", False),
            applies_to_all_units=data.get("applies_to_all_units", False),
            applies_to_sample=data.get("applies_to_sample", True),
            configuration_json=data.get("configuration_json"),
        )
        self.db.add(ctrl)
        self.db.flush()
        return ctrl

    def update_control(
        self,
        control_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityControlDefinitionModel:
        ctrl = self.get_control(control_id, organization_id)
        for field in ("control_name", "description", "display_order", "is_mandatory", "is_blocking", "applies_to_all_units", "applies_to_sample", "configuration_json"):
            if field in data and data[field] is not None:
                setattr(ctrl, field, data[field])
        ctrl.updated_at = _now()
        self.db.flush()
        return ctrl

    def delete_control(self, control_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> None:
        ctrl = self.get_control(control_id, organization_id)
        self.db.delete(ctrl)
        self.db.flush()
