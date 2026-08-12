"""Phase 041. Quality inspection plan CRUD service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import (
    PLAN_STATUS_TRANSITIONS,
    PlanStatus,
    PlanFamily,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
    QualityPlanNotFound,
    QualityPlanAlreadyExists,
    QualityPlanStatusInvalid,
    quality_plan_error,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    canonical_hash_quality_plan,
    require_plan_transition,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityInspectionPlanVersionModel,
    QualityPlanScopeModel,
    QualityControlDefinitionModel,
    QualityPlanUsageProjectionModel,
)
from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.principal import LogisticsPrincipal


def _now() -> datetime:
    return datetime.now().astimezone()


def _actor(principal: LogisticsPrincipal) -> dict:
    return {
        "user_id": principal.user_id,
        "display_name": principal.full_name,
        "role_codes": principal.role_codes,
    }


class QualityInspectionPlanService:
    def __init__(self, db: Session):
        self.db = db

    def get_plan(self, plan_id: UUID, organization_id: UUID) -> QualityInspectionPlanModel:
        plan = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == plan_id,
                QualityInspectionPlanModel.organization_id == organization_id,
            )
        )
        if not plan:
            raise QualityPlanNotFound("QualityPlanNotFound", f"Plan {plan_id} no encontrado", 404)
        return plan

    def list_plans(
        self,
        organization_id: UUID,
        *,
        status: str | None = None,
        family: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[list[QualityInspectionPlanModel], int]:
        query = select(QualityInspectionPlanModel).where(
            QualityInspectionPlanModel.organization_id == organization_id,
        )
        if status:
            query = query.where(QualityInspectionPlanModel.status == status)
        if family:
            query = query.where(QualityInspectionPlanModel.plan_family == family)

        total = self.db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0

        col = getattr(QualityInspectionPlanModel, sort_by, QualityInspectionPlanModel.created_at)
        if sort_direction == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())

        query = query.offset((page - 1) * page_size).limit(page_size)
        rows = list(self.db.scalars(query))
        return rows, total

    def create_plan(
        self,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityInspectionPlanModel:
        existing = self.db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.organization_id == organization_id,
                QualityInspectionPlanModel.plan_code == data["plan_code"],
            )
        )
        if existing:
            raise QualityPlanAlreadyExists(
                "QualityPlanAlreadyExists",
                f"Ya existe un plan con código '{data['plan_code']}'",
                409,
            )

        plan = QualityInspectionPlanModel(
            id=uuid4(),
            organization_id=organization_id,
            plan_code=data["plan_code"],
            plan_name=data["plan_name"],
            description=data.get("description"),
            plan_family=data.get("plan_family", PlanFamily.GENERAL_QUALITY),
            status=PlanStatus.DRAFT,
            current_version_number=0,
            is_global=data.get("is_global", False),
            priority=data.get("priority", 0),
            metadata_json=data.get("metadata_json"),
            created_by=principal.user_id,
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def update_plan(
        self,
        plan_id: UUID,
        organization_id: UUID,
        data: dict[str, Any],
        principal: LogisticsPrincipal,
    ) -> QualityInspectionPlanModel:
        plan = self.get_plan(plan_id, organization_id)
        if plan.status not in (PlanStatus.DRAFT,):
            raise QualityPlanStatusInvalid(
                "QualityPlanStatusInvalid",
                f"Solo se puede editar un plan en estado DRAFT (actual: {plan.status})",
                409,
            )
        for field in ("plan_name", "description", "plan_family", "is_global", "priority", "metadata_json"):
            if field in data and data[field] is not None:
                setattr(plan, field, data[field])
        plan.updated_at = _now()
        plan.row_version += 1
        self.db.flush()
        return plan

    def transition_plan(
        self,
        plan_id: UUID,
        organization_id: UUID,
        target_status: str,
        principal: LogisticsPrincipal,
        reason: str | None = None,
    ) -> QualityInspectionPlanModel:
        plan = self.get_plan(plan_id, organization_id)
        require_plan_transition(plan.status, target_status)

        plan.status = target_status
        plan.updated_at = _now()
        plan.row_version += 1
        self.db.flush()

        self._emit_audit(plan, principal, f"plan_{target_status.lower()}", reason=reason)
        return plan

    def delete_plan(self, plan_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> None:
        plan = self.get_plan(plan_id, organization_id)
        if plan.status != PlanStatus.DRAFT:
            raise QualityPlanStatusInvalid(
                "QualityPlanStatusInvalid",
                f"Solo se puede eliminar un plan en estado DRAFT (actual: {plan.status})",
                409,
            )
        self.db.delete(plan)
        self.db.flush()
        self._emit_audit(plan, principal, "plan_deleted")

    def _emit_audit(
        self,
        plan: QualityInspectionPlanModel,
        principal: LogisticsPrincipal,
        event_code: str,
        reason: str | None = None,
    ) -> None:
        try:
            AuditService().write_event(
                self.db,
                AuditEventCommand(
                    event_code=f"logistics.quality_plan.{event_code}",
                    actor_user_id=principal.user_id,
                    actor_display_name=principal.full_name,
                    actor_role_codes=principal.role_codes,
                    session_id=principal.session_id,
                    device_id=principal.device_id,
                    authentication_level=principal.authentication_level,
                    correlation_id=principal.correlation_id,
                    ip_address=principal.ip_address,
                    user_agent=principal.user_agent,
                    organization_id=str(plan.organization_id),
                    resource_type="quality_inspection_plan",
                    resource_id=str(plan.id),
                    action=event_code,
                    reason_text=reason,
                    metadata={"plan_code": plan.plan_code, "status": plan.status},
                    source_module="logistics.inbound.reception_differences",
                    source_service="QualityInspectionPlanService",
                ),
            )
        except Exception:
            pass
