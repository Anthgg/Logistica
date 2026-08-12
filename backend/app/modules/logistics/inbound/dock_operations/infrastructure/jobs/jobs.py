"""Retry-safe, database-backed jobs for dock operations.

These jobs do not depend on in-process timers.  A scheduler invokes the CLI;
row locks and deduplication keys make concurrent invocations safe.
"""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import ArrivalNoticeOutboxEventModel
from app.modules.logistics.inbound.dock_operations.application.services.common import server_now
from app.modules.logistics.inbound.dock_operations.application.services.export_service import process_pending_exports
from app.modules.logistics.inbound.dock_operations.application.services.unloading_services import DockOperationalProjectionService
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    DockAssignmentPlanModel,
    DockOperationMetricsProjectionModel,
    InboundDockAssignmentModel,
    UnloadingOperationModel,
)


def _enqueue_alert(db: Session, *, organization_id, aggregate_id, event_type: str, payload: dict, key: str) -> bool:
    if db.scalar(select(ArrivalNoticeOutboxEventModel.id).where(ArrivalNoticeOutboxEventModel.deduplication_key == key)):
        return False
    db.add(ArrivalNoticeOutboxEventModel(
        id=uuid4(), organization_id=organization_id, aggregate_type="DOCK_OPERATION_ALERT",
        aggregate_id=aggregate_id, event_type=event_type, payload=payload,
        deduplication_key=key, status="PENDING",
    ))
    return True


def expire_assignment_plans(db: Session, *, batch_size: int = 500) -> int:
    now = server_now()
    rows = list(db.scalars(
        select(DockAssignmentPlanModel).where(
            DockAssignmentPlanModel.status == "ACTIVE", DockAssignmentPlanModel.expires_at <= now,
        ).order_by(DockAssignmentPlanModel.expires_at).with_for_update(skip_locked=True).limit(batch_size)
    ))
    for row in rows:
        row.status = "EXPIRED"
    db.flush()
    return len(rows)


def detect_stale_dock_movements(db: Session, *, stale_minutes: int = 60, batch_size: int = 200) -> int:
    threshold = server_now() - timedelta(minutes=stale_minutes)
    rows = list(db.scalars(
        select(InboundDockAssignmentModel).where(
            InboundDockAssignmentModel.status.in_({"ASSIGNED", "MOVING_TO_DOCK"}),
            InboundDockAssignmentModel.assigned_at <= threshold,
        ).order_by(InboundDockAssignmentModel.assigned_at).with_for_update(skip_locked=True).limit(batch_size)
    ))
    created = 0
    for row in rows:
        bucket = int(row.assigned_at.timestamp()) // 3600
        created += int(_enqueue_alert(
            db, organization_id=row.organization_id, aggregate_id=row.id,
            event_type="DockAssignmentMovementStale",
            payload={"assignment_id": str(row.id), "status": row.status, "assigned_at": row.assigned_at.isoformat()},
            key=f"dock-assignment:{row.id}:movement-stale:{bucket}",
        ))
    db.flush()
    return created


def detect_abandoned_unloading(db: Session, *, stale_hours: int = 8, batch_size: int = 200) -> int:
    threshold = server_now() - timedelta(hours=stale_hours)
    rows = list(db.scalars(
        select(UnloadingOperationModel).where(
            UnloadingOperationModel.status.in_({"IN_PROGRESS", "PAUSED"}),
            UnloadingOperationModel.started_at <= threshold,
        ).order_by(UnloadingOperationModel.started_at).with_for_update(skip_locked=True).limit(batch_size)
    ))
    created = 0
    for row in rows:
        day = threshold.date().isoformat()
        created += int(_enqueue_alert(
            db, organization_id=row.organization_id, aggregate_id=row.id,
            event_type="UnloadingOperationAbandoned",
            payload={"unloading_operation_id": str(row.id), "status": row.status, "started_at": row.started_at.isoformat()},
            key=f"unloading:{row.id}:abandoned:{day}",
        ))
    db.flush()
    return created


def refresh_operational_projections(db: Session, *, batch_size: int = 500) -> int:
    rows = list(db.scalars(
        select(UnloadingOperationModel).where(
            UnloadingOperationModel.status.in_({"COMPLETED", "ABORTED"}),
        ).order_by(UnloadingOperationModel.updated_at).with_for_update(skip_locked=True).limit(batch_size)
    ))
    refreshed = 0
    for row in rows:
        projection = db.scalar(select(DockOperationMetricsProjectionModel).where(DockOperationMetricsProjectionModel.unloading_operation_id == row.id))
        if projection is None or projection.calculated_at < row.updated_at:
            DockOperationalProjectionService(db).refresh(row)
            refreshed += 1
    db.flush()
    return refreshed
