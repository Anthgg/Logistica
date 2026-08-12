"""Phase 041. Quality inspection plan background jobs."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
    QualityInspectionPlanModel,
    QualityInspectionPlanVersionModel,
    QualityPlanScopeModel,
    QualityControlDefinitionModel,
    QualityPlanUsageProjectionModel,
)


def detect_plans_without_active_version(db: Session) -> list[dict[str, Any]]:
    plans = list(db.scalars(
        select(QualityInspectionPlanModel).where(
            QualityInspectionPlanModel.status == "ACTIVE",
            QualityInspectionPlanModel.active_version_id.is_(None),
        )
    ))
    return [{"plan_id": str(p.id), "plan_code": p.plan_code, "status": p.status} for p in plans]


def detect_draft_plans_stale(db: Session, days: int = 30) -> list[dict[str, Any]]:
    cutoff = datetime.now().astimezone() - timedelta(days=days)
    plans = list(db.scalars(
        select(QualityInspectionPlanModel).where(
            QualityInspectionPlanModel.status == "DRAFT",
            QualityInspectionPlanModel.created_at < cutoff,
        )
    ))
    return [{"plan_id": str(p.id), "plan_code": p.plan_code, "created_at": p.created_at.isoformat()} for p in plans]


def detect_plans_without_scopes(db: Session) -> list[dict[str, Any]]:
    subq = select(QualityPlanScopeModel.plan_id).distinct().subquery()
    plans = list(db.scalars(
        select(QualityInspectionPlanModel).where(
            QualityInspectionPlanModel.id.notin_(select(subq.c.plan_id)),
            QualityInspectionPlanModel.status != "ARCHIVED",
        )
    ))
    return [{"plan_id": str(p.id), "plan_code": p.plan_code, "status": p.status} for p in plans]


def detect_plans_without_controls(db: Session) -> list[dict[str, Any]]:
    subq = select(QualityControlDefinitionModel.plan_id).distinct().subquery()
    plans = list(db.scalars(
        select(QualityInspectionPlanModel).where(
            QualityInspectionPlanModel.id.notin_(select(subq.c.plan_id)),
            QualityInspectionPlanModel.status != "ARCHIVED",
        )
    ))
    return [{"plan_id": str(p.id), "plan_code": p.plan_code, "status": p.status} for p in plans]


def update_usage_projections(db: Session) -> list[dict[str, Any]]:
    from app.modules.logistics.inbound.reception_differences.application.services.quality_metrics_service import (
        QualityPlanMetricsProjectionService,
    )

    plans = list(db.scalars(
        select(QualityInspectionPlanModel).where(
            QualityInspectionPlanModel.status.in_(["ACTIVE", "DRAFT"]),
        )
    ))
    results = []
    for plan in plans:
        try:
            result = QualityPlanMetricsProjectionService(db).update_metrics(plan.id, plan.organization_id)
            results.append(result)
        except Exception:
            pass
    return results


def detect_version_conflicts(db: Session) -> list[dict[str, Any]]:
    versions = list(db.scalars(
        select(QualityInspectionPlanVersionModel).where(
            QualityInspectionPlanVersionModel.status == "ACTIVE",
        )
    ))
    plan_versions: dict[str, list] = {}
    for v in versions:
        plan_versions.setdefault(str(v.plan_id), []).append(str(v.id))

    conflicts = []
    for plan_id, vids in plan_versions.items():
        if len(vids) > 1:
            conflicts.append({"plan_id": plan_id, "active_version_ids": vids})
    return conflicts
