"""FastAPI endpoints for Phase 038 dock assignment and unloading execution.

Every command is CSRF-protected and requires an idempotency key.  Actor,
status, timestamps and durations are always obtained from the authenticated
principal and server-side services; none are accepted from command payloads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id, verify_csrf
from app.modules.logistics.inbound.dock_operations.application.services.common import DockIdempotencyService, DockMasterEventService, server_now
from app.modules.logistics.inbound.dock_operations.application.services.dock_services import (
    DockAssignmentService,
    DockReassignmentService,
    InboundDockQueueOrderingService,
    InboundDockQueueService,
    WarehouseDockAvailabilityService,
    WarehouseDockService,
)
from app.modules.logistics.inbound.dock_operations.application.services.export_service import (
    DockOperationExportService,
)
from app.modules.logistics.inbound.dock_operations.application.services.unloading_services import (
    DockOperationIntegrityService,
    DockOperationalProjectionService,
    ReceivingScanPreparationService,
    UnloadingCompletionService,
    UnloadingEquipmentService,
    UnloadingOperationService,
    UnloadingReadinessService,
    UnloadingResponsibilityService,
    UnloadingSealOpeningService,
    UnloadingTimeCorrectionService,
)
from app.modules.logistics.inbound.dock_operations.domain.enums import DockMasterStatus, QueueStatus
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    DockOperationalEventModel,
    DockOperationMetricsProjectionModel,
    DockOperationExportJobModel,
    DockOperationalTimeCorrectionModel,
    InboundDockAssignmentModel,
    InboundDockQueueEntryModel,
    UnloadingCompletionCheckDefinitionModel,
    UnloadingCompletionCheckResultModel,
    UnloadingEquipmentAssignmentModel,
    UnloadingOperationModel,
    UnloadingPauseModel,
    UnloadingReadinessCheckDefinitionModel,
    UnloadingReadinessCheckResultModel,
    UnloadingResponsibleAssignmentModel,
    UnloadingSealOpeningEventModel,
    WarehouseDockBlackoutModel,
    WarehouseDockCapabilityModel,
    WarehouseDockOperatingWindowModel,
    WarehouseDockModel,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticePurchaseOrderReferenceModel,
    ArrivalNoticeRevisionModel,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import GateCheckInModel
from app.modules.logistics.inbound.dock_operations.presentation.schemas import (
    DockAssignmentPlanRequest,
    DockAssignmentPlanResponse,
    DockAssignmentPlanExecuteRequest,
    DockAssignmentCreate,
    DockAssignmentReassignRequest,
    DockAssignmentResponse,
    DockOperationalTimeCorrectionCreate,
    DockOperationExportRequest,
    DockOperationExportResponse,
    InboundDockQueueCreate,
    InboundDockQueuePriorityChangeRequest,
    InboundDockQueueResponse,
    PageResponse,
    ReasonRequest,
    ReceivingScanPreparationResponse,
    UnloadingAbortRequest,
    UnloadingCompleteRequest,
    UnloadingCompletionCheckRequest,
    UnloadingEquipmentCreate,
    UnloadingOperationCreate,
    UnloadingOperationResponse,
    UnloadingPauseRequest,
    UnloadingReadinessCheckRequest,
    UnloadingResponsibleCreate,
    UnloadingResumeRequest,
    UnloadingSealOpeningRequest,
    WarehouseDockBlackoutCreate,
    WarehouseDockCapabilityCreate,
    WarehouseDockCreate,
    WarehouseDockOperatingWindowCreate,
    WarehouseDockOperatingWindowUpdate,
    WarehouseDockResponse,
    WarehouseDockUpdate,
)
from app.modules.logistics.principal import LogisticsPrincipal


router = APIRouter(tags=["Dock Operations (Phase 038)"])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)]


def _organization(principal: LogisticsPrincipal) -> UUID:
    return resolve_organization_id(principal)


def _assert_warehouse_scope(principal: LogisticsPrincipal, warehouse_id: UUID) -> None:
    if not principal.can_access_warehouse(warehouse_id):
        raise ApplicationError("WAREHOUSE_SCOPE_FORBIDDEN", "No tiene alcance sobre el almacén solicitado.", 403)


def _row_dict(row: object) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _command(
    *,
    db: Session,
    principal: LogisticsPrincipal,
    idempotency_key: str,
    operation: str,
    payload: dict,
    execute: Callable[[], object],
    response_model: type | None = None,
) -> object:
    organization_id = _organization(principal)
    canonical_payload = jsonable_encoder(payload)
    replay = DockIdempotencyService.replay(db, organization_id, operation, idempotency_key, canonical_payload)
    if replay is not None:
        return replay
    value = execute()
    if response_model is not None:
        response = response_model.model_validate(value).model_dump(mode="json")
    elif isinstance(value, dict):
        response = jsonable_encoder(value)
    else:
        response = jsonable_encoder(_row_dict(value))
    DockIdempotencyService.save(
        db, principal, organization_id, operation, idempotency_key, canonical_payload, response
    )
    db.commit()
    return value


def _event_history(db: Session, organization_id: UUID, **filters: UUID) -> list[dict]:
    query = select(DockOperationalEventModel).where(DockOperationalEventModel.organization_id == organization_id)
    for name, value in filters.items():
        query = query.where(getattr(DockOperationalEventModel, name) == value)
    rows = db.scalars(query.order_by(DockOperationalEventModel.event_at, DockOperationalEventModel.sequence_number))
    return [_row_dict(row) for row in rows]


# Warehouse dock master -----------------------------------------------------

@router.get("/warehouse-docks", response_model=list[WarehouseDockResponse])
def list_warehouse_docks(
    warehouse_id: UUID | None = None,
    dock_status: str | None = Query(default=None, alias="status"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_docks.read")),
    db: Session = Depends(get_db),
):
    if warehouse_id is not None:
        _assert_warehouse_scope(principal, warehouse_id)
    rows = WarehouseDockService(db).list(_organization(principal), warehouse_id, dock_status)
    return [row for row in rows if principal.can_access_warehouse(row.warehouse_id)]


@router.post("/warehouse-docks", response_model=WarehouseDockResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse_dock(
    body: WarehouseDockCreate,
    idempotency_key: IdempotencyKey,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_docks.manage")),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    _assert_warehouse_scope(principal, body.warehouse_id)
    return _command(
        db=db, principal=principal, idempotency_key=idempotency_key,
        operation="phase038.warehouse_dock.create", payload=body.model_dump(mode="json"),
        execute=lambda: WarehouseDockService(db).create(_organization(principal), principal, body),
        response_model=WarehouseDockResponse,
    )


@router.get("/warehouse-docks/{dock_id}", response_model=WarehouseDockResponse)
def get_warehouse_dock(
    dock_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_docks.read")),
    db: Session = Depends(get_db),
):
    row = WarehouseDockService(db).get(dock_id, _organization(principal))
    _assert_warehouse_scope(principal, row.warehouse_id)
    return row


@router.patch("/warehouse-docks/{dock_id}", response_model=WarehouseDockResponse)
def update_warehouse_dock(
    dock_id: UUID,
    body: WarehouseDockUpdate,
    idempotency_key: IdempotencyKey,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_docks.manage")),
    db: Session = Depends(get_db),
    _csrf=Depends(verify_csrf),
):
    current = WarehouseDockService(db).get(dock_id, _organization(principal))
    _assert_warehouse_scope(principal, current.warehouse_id)
    return _command(
        db=db, principal=principal, idempotency_key=idempotency_key,
        operation=f"phase038.warehouse_dock.update:{dock_id}", payload=body.model_dump(mode="json", exclude_unset=True),
        execute=lambda: WarehouseDockService(db).update(dock_id, _organization(principal), principal, body),
        response_model=WarehouseDockResponse,
    )


def _dock_transition(
    dock_id: UUID, target: DockMasterStatus, body: ReasonRequest, idempotency_key: str,
    principal: LogisticsPrincipal, db: Session,
):
    current = WarehouseDockService(db).get(dock_id, _organization(principal))
    _assert_warehouse_scope(principal, current.warehouse_id)
    if body.row_version is not None and current.row_version != body.row_version:
        raise ApplicationError("OPTIMISTIC_LOCK_CONFLICT", "El muelle fue modificado; recargue e intente nuevamente.", 409)
    return _command(
        db=db, principal=principal, idempotency_key=idempotency_key,
        operation=f"phase038.warehouse_dock.{target.value.lower()}:{dock_id}", payload=body.model_dump(mode="json"),
        execute=lambda: WarehouseDockService(db).transition(dock_id, _organization(principal), principal, target, body.reason),
        response_model=WarehouseDockResponse,
    )


@router.post("/warehouse-docks/{dock_id}/activate", response_model=WarehouseDockResponse)
def activate_warehouse_dock(dock_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.activate")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _dock_transition(dock_id, DockMasterStatus.ACTIVE, body, idempotency_key, principal, db)


@router.post("/warehouse-docks/{dock_id}/deactivate", response_model=WarehouseDockResponse)
@router.post("/warehouse-docks/{dock_id}/inactivate", response_model=WarehouseDockResponse, include_in_schema=False)
def inactivate_warehouse_dock(dock_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _dock_transition(dock_id, DockMasterStatus.INACTIVE, body, idempotency_key, principal, db)


@router.post("/warehouse-docks/{dock_id}/mark-maintenance", response_model=WarehouseDockResponse)
def mark_warehouse_dock_maintenance(dock_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.block")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _dock_transition(dock_id, DockMasterStatus.MAINTENANCE, body, idempotency_key, principal, db)


@router.post("/warehouse-docks/{dock_id}/block", response_model=WarehouseDockResponse)
def block_warehouse_dock(dock_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.block")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _dock_transition(dock_id, DockMasterStatus.BLOCKED, body, idempotency_key, principal, db)


@router.post("/warehouse-docks/{dock_id}/unblock", response_model=WarehouseDockResponse)
def unblock_warehouse_dock(dock_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.block")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _dock_transition(dock_id, DockMasterStatus.ACTIVE, body, idempotency_key, principal, db)


@router.post("/warehouse-docks/{dock_id}/archive", response_model=WarehouseDockResponse)
def archive_warehouse_dock(dock_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _dock_transition(dock_id, DockMasterStatus.ARCHIVED, body, idempotency_key, principal, db)


@router.post("/warehouse-docks/{dock_id}/capabilities", status_code=status.HTTP_201_CREATED)
def add_warehouse_dock_capability(dock_id: UUID, body: WarehouseDockCapabilityCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.dock_capability.create:{dock_id}", payload=body.model_dump(mode="json"), execute=lambda: WarehouseDockService(db).add_capability(dock_id, _organization(principal), principal, body))


@router.get("/warehouse-docks/{dock_id}/capabilities")
def list_warehouse_dock_capabilities(dock_id: UUID, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return [_row_dict(row) for row in db.scalars(select(WarehouseDockCapabilityModel).where(WarehouseDockCapabilityModel.dock_id == dock_id))]


@router.post("/warehouse-docks/{dock_id}/operating-windows", status_code=status.HTTP_201_CREATED)
def add_warehouse_dock_window(dock_id: UUID, body: WarehouseDockOperatingWindowCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.dock_window.create:{dock_id}", payload=body.model_dump(mode="json"), execute=lambda: WarehouseDockService(db).add_window(dock_id, _organization(principal), principal, body))


@router.get("/warehouse-docks/{dock_id}/operating-windows")
def list_warehouse_dock_windows(dock_id: UUID, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return [_row_dict(row) for row in db.scalars(select(WarehouseDockOperatingWindowModel).where(WarehouseDockOperatingWindowModel.dock_id == dock_id))]


@router.post("/warehouse-docks/{dock_id}/blackouts", status_code=status.HTTP_201_CREATED)
def add_warehouse_dock_blackout(dock_id: UUID, body: WarehouseDockBlackoutCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage_blackouts")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.dock_blackout.create:{dock_id}", payload=body.model_dump(mode="json"), execute=lambda: WarehouseDockService(db).add_blackout(dock_id, _organization(principal), principal, body))


@router.get("/warehouse-docks/{dock_id}/blackouts")
def list_warehouse_dock_blackouts(dock_id: UUID, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return [_row_dict(row) for row in db.scalars(select(WarehouseDockBlackoutModel).where(WarehouseDockBlackoutModel.dock_id == dock_id))]


@router.post("/warehouse-docks/{dock_id}/blackouts/{blackout_id}/cancel")
def cancel_warehouse_dock_blackout(dock_id: UUID, blackout_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage_blackouts")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    def execute():
        row = db.scalar(select(WarehouseDockBlackoutModel).where(WarehouseDockBlackoutModel.id == blackout_id, WarehouseDockBlackoutModel.dock_id == dock_id).with_for_update())
        if row is None: raise ApplicationError("WAREHOUSE_DOCK_BLACKOUT_NOT_FOUND", "Blackout no encontrado.", 404)
        row.status = "CANCELLED"; row.cancelled_at = server_now(); row.cancelled_by = principal.user_id; db.flush()
        DockMasterEventService(db).append(dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_BLACKOUT_CANCELLED", audit_code="logistics.warehouse_dock.blackout_cancelled", reason=body.reason, new_data={"blackout_id": str(row.id), "status": row.status})
        return row
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.dock_blackout.cancel:{blackout_id}", payload=body.model_dump(mode="json"), execute=execute)


@router.post("/warehouse-dock-blackouts/{blackout_id}/cancel")
def cancel_warehouse_dock_blackout_by_id(blackout_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage_blackouts")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    row = db.get(WarehouseDockBlackoutModel, blackout_id)
    if row is None:
        raise ApplicationError("WAREHOUSE_DOCK_BLACKOUT_NOT_FOUND", "Blackout no encontrado.", 404)
    return cancel_warehouse_dock_blackout(row.dock_id, blackout_id, body, idempotency_key, principal, db, _csrf)


def _get_dock_window(window_id: UUID, principal: LogisticsPrincipal, db: Session, *, lock: bool = False):
    query = select(WarehouseDockOperatingWindowModel).where(WarehouseDockOperatingWindowModel.id == window_id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if row is None:
        raise ApplicationError("WAREHOUSE_DOCK_WINDOW_NOT_FOUND", "Horario de muelle no encontrado.", 404)
    dock = WarehouseDockService(db).get(row.dock_id, _organization(principal))
    _assert_warehouse_scope(principal, dock.warehouse_id)
    return row, dock


@router.patch("/warehouse-dock-operating-windows/{window_id}")
def update_warehouse_dock_window(window_id: UUID, body: WarehouseDockOperatingWindowUpdate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    _get_dock_window(window_id, principal, db)
    def execute():
        row, dock = _get_dock_window(window_id, principal, db, lock=True)
        changes = body.model_dump(exclude_unset=True)
        for name, value in changes.items():
            setattr(row, name, value)
        if row.start_local_time >= row.end_local_time or (row.effective_to is not None and row.effective_to < row.effective_from):
            raise ApplicationError("WAREHOUSE_DOCK_WINDOW_INVALID", "El intervalo o vigencia del horario es inválido.", 422)
        DockMasterEventService(db).append(dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_WINDOW_UPDATED", audit_code="logistics.warehouse_dock.window_updated", new_data={"window_id": str(row.id), **jsonable_encoder(changes)})
        db.flush()
        return row
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.dock_window.update:{window_id}", payload=body.model_dump(mode="json", exclude_unset=True), execute=execute)


@router.post("/warehouse-dock-operating-windows/{window_id}/deactivate")
def deactivate_warehouse_dock_window(window_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.warehouse_docks.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    _get_dock_window(window_id, principal, db)
    def execute():
        row, dock = _get_dock_window(window_id, principal, db, lock=True)
        if row.status != "ACTIVE":
            raise ApplicationError("WAREHOUSE_DOCK_WINDOW_NOT_ACTIVE", "El horario ya no está activo.", 409)
        row.status = "INACTIVE"
        DockMasterEventService(db).append(dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_WINDOW_DEACTIVATED", audit_code="logistics.warehouse_dock.window_deactivated", reason=body.reason, new_data={"window_id": str(row.id), "status": row.status})
        db.flush()
        return row
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.dock_window.deactivate:{window_id}", payload=body.model_dump(mode="json"), execute=execute)


@router.get("/warehouse-docks/{dock_id}/availability")
def get_warehouse_dock_availability(dock_id: UUID, at: datetime | None = None, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return WarehouseDockAvailabilityService(db).resolve(dock, at)


@router.get("/warehouse-docks/{dock_id}/operational-status")
def get_warehouse_dock_operational_status(dock_id: UUID, at: datetime | None = None, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    availability = WarehouseDockAvailabilityService(db).resolve(dock, at)
    return {
        "dock_id": dock.id,
        "master_status": dock.status,
        "operational_status": availability["operational_status"],
        "available": availability["available"],
        "capacity": availability["capacity"],
        "occupied_slots": availability["occupied_slots"],
        "reasons": availability["reasons"],
        "server_time": availability["server_time"],
    }


@router.get("/warehouse-docks/{dock_id}/schedule")
def get_warehouse_dock_schedule(dock_id: UUID, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return {
        "dock_id": dock.id,
        "operating_windows": [_row_dict(row) for row in db.scalars(select(WarehouseDockOperatingWindowModel).where(WarehouseDockOperatingWindowModel.dock_id == dock_id))],
        "blackouts": [_row_dict(row) for row in db.scalars(select(WarehouseDockBlackoutModel).where(WarehouseDockBlackoutModel.dock_id == dock_id))],
        "assignments": [_row_dict(row) for row in db.scalars(select(InboundDockAssignmentModel).where(InboundDockAssignmentModel.dock_id == dock_id))],
        "server_time": server_now(),
    }


@router.get("/warehouse-docks/{dock_id}/history")
def get_warehouse_dock_history(dock_id: UUID, principal=Depends(require_permission("logistics.warehouse_docks.read")), db: Session = Depends(get_db)):
    dock = WarehouseDockService(db).get(dock_id, _organization(principal)); _assert_warehouse_scope(principal, dock.warehouse_id)
    return _event_history(db, _organization(principal), dock_id=dock_id)


# Internal inbound queue ----------------------------------------------------

@router.get("/inbound-dock-queue", response_model=list[InboundDockQueueResponse])
def list_inbound_dock_queue(warehouse_id: UUID | None = None, queue_status: str | None = Query(default=None, alias="status"), principal=Depends(require_permission("logistics.inbound_dock_queue.read")), db: Session = Depends(get_db)):
    query = select(InboundDockQueueEntryModel).where(InboundDockQueueEntryModel.organization_id == _organization(principal))
    if warehouse_id is not None: _assert_warehouse_scope(principal, warehouse_id); query = query.where(InboundDockQueueEntryModel.warehouse_id == warehouse_id)
    if queue_status is not None: query = query.where(InboundDockQueueEntryModel.queue_status == queue_status)
    rows = list(db.scalars(query))
    return InboundDockQueueOrderingService.order([row for row in rows if principal.can_access_warehouse(row.warehouse_id)])


@router.post("/inbound-dock-queue/from-gate-check-in", response_model=InboundDockQueueResponse, status_code=status.HTTP_201_CREATED)
def create_inbound_dock_queue_entry(body: InboundDockQueueCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_queue.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.queue.create:{body.gate_check_in_id}", payload=body.model_dump(mode="json"), execute=lambda: InboundDockQueueService(db).create_from_gate(_organization(principal), principal, body.gate_check_in_id, body.priority.value, body.priority_reason), response_model=InboundDockQueueResponse)


@router.get("/inbound-dock-queue/ordered", response_model=list[InboundDockQueueResponse])
def get_ordered_inbound_dock_queue(warehouse_id: UUID | None = None, principal=Depends(require_permission("logistics.inbound_dock_queue.read")), db: Session = Depends(get_db)):
    return list_inbound_dock_queue(warehouse_id, None, principal, db)


@router.get("/inbound-dock-queue/summary")
def get_inbound_dock_queue_summary(warehouse_id: UUID | None = None, principal=Depends(require_permission("logistics.inbound_dock_queue.read")), db: Session = Depends(get_db)):
    rows = list_inbound_dock_queue(warehouse_id, None, principal, db)
    counts: dict[str, int] = {}
    for row in rows: counts[row.queue_status] = counts.get(row.queue_status, 0) + 1
    return {"total": len(rows), "by_status": counts, "server_time": server_now()}


@router.get("/inbound-dock-queue/{queue_entry_id}", response_model=InboundDockQueueResponse)
def get_inbound_dock_queue_entry(queue_entry_id: UUID, principal=Depends(require_permission("logistics.inbound_dock_queue.read")), db: Session = Depends(get_db)):
    row = InboundDockQueueService(db).get(queue_entry_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id); return row


def _queue_transition(queue_entry_id: UUID, target: QueueStatus, body: ReasonRequest, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    current = InboundDockQueueService(db).get(queue_entry_id, _organization(principal)); _assert_warehouse_scope(principal, current.warehouse_id)
    if body.row_version is not None and current.row_version != body.row_version: raise ApplicationError("OPTIMISTIC_LOCK_CONFLICT", "La cola fue modificada; recargue.", 409)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.queue.{target.value.lower()}:{queue_entry_id}", payload=body.model_dump(mode="json"), execute=lambda: InboundDockQueueService(db).transition(queue_entry_id, _organization(principal), principal, target, body.reason), response_model=InboundDockQueueResponse)


@router.post("/inbound-dock-queue/{queue_entry_id}/mark-ready", response_model=InboundDockQueueResponse)
def ready_inbound_dock_queue_entry(queue_entry_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_queue.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _queue_transition(queue_entry_id, QueueStatus.READY, body, idempotency_key, principal, db)


@router.post("/inbound-dock-queue/{queue_entry_id}/hold", response_model=InboundDockQueueResponse)
def hold_inbound_dock_queue_entry(queue_entry_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_queue.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _queue_transition(queue_entry_id, QueueStatus.ON_HOLD, body, idempotency_key, principal, db)


@router.post("/inbound-dock-queue/{queue_entry_id}/resume", response_model=InboundDockQueueResponse)
def resume_inbound_dock_queue_entry(queue_entry_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_queue.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _queue_transition(queue_entry_id, QueueStatus.READY, body, idempotency_key, principal, db)


@router.post("/inbound-dock-queue/{queue_entry_id}/remove", response_model=InboundDockQueueResponse)
def remove_inbound_dock_queue_entry(queue_entry_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_queue.manage")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _queue_transition(queue_entry_id, QueueStatus.REMOVED, body, idempotency_key, principal, db)


@router.post("/inbound-dock-queue/{queue_entry_id}/change-priority", response_model=InboundDockQueueResponse)
def change_inbound_dock_queue_priority(queue_entry_id: UUID, body: InboundDockQueuePriorityChangeRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_queue.change_priority")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    current = InboundDockQueueService(db).get(queue_entry_id, _organization(principal)); _assert_warehouse_scope(principal, current.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.queue.priority:{queue_entry_id}", payload=body.model_dump(mode="json"), execute=lambda: InboundDockQueueService(db).change_priority(queue_entry_id, _organization(principal), principal, body.priority.value, body.reason, body.row_version), response_model=InboundDockQueueResponse)


@router.get("/inbound-dock-queue/{queue_entry_id}/history")
def get_inbound_dock_queue_history(queue_entry_id: UUID, principal=Depends(require_permission("logistics.inbound_dock_queue.read")), db: Session = Depends(get_db)):
    row = InboundDockQueueService(db).get(queue_entry_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id); return _event_history(db, _organization(principal), gate_check_in_id=row.gate_check_in_id)


# Assignment planning and execution ---------------------------------------

@router.post("/dock-assignment-plans", response_model=DockAssignmentPlanResponse, status_code=status.HTTP_201_CREATED)
def create_dock_assignment_plan(body: DockAssignmentPlanRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.plan")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    request_data = body.model_dump()
    return _command(
        db=db, principal=principal, idempotency_key=idempotency_key,
        operation=f"phase038.assignment_plan.create:{body.gate_check_in_id}", payload=body.model_dump(mode="json"),
        execute=lambda: DockAssignmentService(db).create_plan(_organization(principal), principal, request_data)[1],
        response_model=DockAssignmentPlanResponse,
    )


@router.post("/dock-assignment-plans/{assignment_hash}/execute", response_model=DockAssignmentResponse, status_code=status.HTTP_201_CREATED)
def execute_dock_assignment_plan(assignment_hash: str, body: DockAssignmentPlanExecuteRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.assign")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _command(
        db=db,
        principal=principal,
        idempotency_key=idempotency_key,
        operation=f"phase038.assignment_plan.execute:{assignment_hash}",
        payload={"assignment_hash": assignment_hash, **body.model_dump(mode="json")},
        execute=lambda: DockAssignmentService(db).execute_plan(
            _organization(principal),
            principal,
            assignment_hash,
            body.dock_id,
            body.assignment_reason,
        ),
        response_model=DockAssignmentResponse,
    )


@router.post("/inbound-dock-assignments", response_model=DockAssignmentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/dock-assignments", response_model=DockAssignmentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_dock_assignment(body: DockAssignmentCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.assign")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        row = DockAssignmentService(db).execute_plan(_organization(principal), principal, body.assignment_hash, body.dock_id, body.assignment_reason)
        if row.gate_check_in_id != body.gate_check_in_id:
            raise ApplicationError("DOCK_ASSIGNMENT_HASH_MISMATCH", "El plan no corresponde al control de puerta enviado.", 409)
        return row
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.assignment.create:{body.assignment_hash}", payload=body.model_dump(mode="json"), execute=execute, response_model=DockAssignmentResponse)


def _public_party_summary(snapshot: dict | None) -> dict | None:
    if not snapshot:
        return None
    allowed = {
        "id", "business_partner_id", "partner_code", "legal_name",
        "trade_name", "name", "code",
    }
    return {key: value for key, value in snapshot.items() if key in allowed}


def _dock_operation_list_item(db: Session, assignment: InboundDockAssignmentModel) -> dict:
    operation = db.scalar(select(UnloadingOperationModel).where(UnloadingOperationModel.dock_assignment_id == assignment.id))
    gate = db.get(GateCheckInModel, assignment.gate_check_in_id)
    queue = db.get(InboundDockQueueEntryModel, assignment.queue_entry_id)
    dock = db.get(WarehouseDockModel, assignment.dock_id)
    responsibles = list(db.scalars(select(UnloadingResponsibleAssignmentModel).where(UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id))) if operation else []
    pause_count = int(db.scalar(select(func.count()).select_from(UnloadingPauseModel).where(UnloadingPauseModel.unloading_operation_id == operation.id)) or 0) if operation else 0
    quality = DockOperationalProjectionService(db).metrics(operation).get("data_quality_status") if operation else "INCOMPLETE"
    now = server_now()
    current_elapsed = None
    if operation and operation.started_at and operation.completed_at is None:
        current_elapsed = max(int((now - operation.started_at).total_seconds()), 0)
    assignment_capabilities = {
        "ASSIGNED": ["start_movement", "cancel", "request_reassignment"],
        "MOVING_TO_DOCK": ["confirm_dock_arrival", "cancel", "request_reassignment"],
        "AT_DOCK": ["create_unloading_operation", "request_reassignment"],
        "READY_FOR_UNLOADING": ["create_unloading_operation"],
        "UNLOADING_COMPLETED": ["release_dock"],
        "RELEASE_PENDING": ["release_dock"],
    }
    return {
        "id": operation.id if operation else assignment.id,
        "assignment_id": assignment.id,
        "unloading_operation_id": operation.id if operation else None,
        "CPV_code": gate.check_in_code if gate else None,
        "CIT_code": gate.appointment_code_snapshot if gate else None,
        "supplier_summary": _public_party_summary(gate.supplier_snapshot if gate else None),
        "carrier_summary": _public_party_summary(gate.carrier_snapshot if gate else None),
        "warehouse_summary": {"id": assignment.warehouse_id},
        "dock_summary": {"id": assignment.dock_id, "code": dock.code if dock else None, "name": dock.name if dock else None},
        "vehicle_summary": {"id": assignment.vehicle_id} if assignment.vehicle_id else None,
        "plate": assignment.observed_plate_snapshot,
        "queue_priority": queue.priority if queue else None,
        "assignment_status": assignment.status,
        "unloading_status": operation.status if operation else None,
        "gate_cleared_at": gate.entry_authorized_at if gate else None,
        "dock_arrived_at": assignment.dock_arrived_at,
        "unloading_started_at": operation.started_at if operation else None,
        "unloading_completed_at": operation.completed_at if operation else None,
        "dock_released_at": assignment.released_at,
        "current_elapsed_seconds": current_elapsed,
        "pause_count": pause_count,
        "warning_count": gate.warning_count if gate else 0,
        "responsible_summary": [
            {
                "responsibility_type": row.responsibility_type,
                "user_id": row.user_id,
                "business_partner_id": row.business_partner_id,
                "status": row.status,
            }
            for row in responsibles
        ],
        "data_quality_status": quality,
        "capabilities": assignment_capabilities.get(assignment.status, []),
    }


def _search_dock_assignments(
    *, db: Session, principal: LogisticsPrincipal, operation_required: bool,
    search: str | None, cpv_code: str | None, cit_code: str | None,
    purchase_order_code: str | None, supplier_id: UUID | None, carrier_id: UUID | None,
    warehouse_id: UUID | None, dock_id: UUID | None, gate_check_in_id: UUID | None,
    vehicle_id: UUID | None, plate: str | None, assignment_status: str | None,
    unloading_status: str | None, priority: str | None, assigned_by: UUID | None,
    responsible_user_id: UUID | None, arrived_from: datetime | None, arrived_to: datetime | None,
    unloading_started_from: datetime | None, unloading_started_to: datetime | None,
    unloading_completed_from: datetime | None, unloading_completed_to: datetime | None,
    dock_released_from: datetime | None, dock_released_to: datetime | None,
    has_pauses: bool | None, has_anomalies: bool | None, has_time_corrections: bool | None,
    data_quality_status: str | None, active: bool | None, mine: bool | None,
    page: int, page_size: int, sort_by: str, sort_direction: str,
) -> dict:
    organization_id = _organization(principal)
    operation_join = InboundDockAssignmentModel.id == UnloadingOperationModel.dock_assignment_id
    query = (
        select(InboundDockAssignmentModel)
        .join(GateCheckInModel, GateCheckInModel.id == InboundDockAssignmentModel.gate_check_in_id)
        .outerjoin(UnloadingOperationModel, operation_join)
        .outerjoin(DockOperationMetricsProjectionModel, DockOperationMetricsProjectionModel.assignment_id == InboundDockAssignmentModel.id)
        .where(InboundDockAssignmentModel.organization_id == organization_id)
    )
    if principal.warehouse_ids:
        query = query.where(
            InboundDockAssignmentModel.warehouse_id.in_(
                [UUID(str(value)) for value in principal.warehouse_ids]
            )
        )
    if operation_required:
        query = query.where(UnloadingOperationModel.id.is_not(None))
    if warehouse_id is not None:
        _assert_warehouse_scope(principal, warehouse_id); query = query.where(InboundDockAssignmentModel.warehouse_id == warehouse_id)
    if dock_id is not None: query = query.where(InboundDockAssignmentModel.dock_id == dock_id)
    if gate_check_in_id is not None: query = query.where(InboundDockAssignmentModel.gate_check_in_id == gate_check_in_id)
    if vehicle_id is not None: query = query.where(InboundDockAssignmentModel.vehicle_id == vehicle_id)
    if plate: query = query.where(InboundDockAssignmentModel.observed_plate_snapshot.ilike(f"%{plate.strip()}%"))
    if assignment_status: query = query.where(InboundDockAssignmentModel.status == assignment_status)
    if unloading_status: query = query.where(UnloadingOperationModel.status == unloading_status)
    if priority: query = query.join(InboundDockQueueEntryModel, InboundDockQueueEntryModel.id == InboundDockAssignmentModel.queue_entry_id).where(InboundDockQueueEntryModel.priority == priority)
    if assigned_by: query = query.where(InboundDockAssignmentModel.assigned_by_user_id == assigned_by)
    if cpv_code: query = query.where(GateCheckInModel.check_in_code.ilike(f"%{cpv_code.strip()}%"))
    if cit_code: query = query.where(GateCheckInModel.appointment_code_snapshot.ilike(f"%{cit_code.strip()}%"))
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(InboundDockAssignmentModel.observed_plate_snapshot.ilike(term), GateCheckInModel.check_in_code.ilike(term), GateCheckInModel.appointment_code_snapshot.ilike(term), UnloadingOperationModel.operation_code.ilike(term)))
    if supplier_id: query = query.where(DockOperationMetricsProjectionModel.supplier_id == supplier_id)
    if carrier_id: query = query.where(DockOperationMetricsProjectionModel.carrier_id == carrier_id)
    if purchase_order_code:
        po_exists = (
            select(ArrivalNoticePurchaseOrderReferenceModel.id)
            .join(ArrivalNoticeRevisionModel, ArrivalNoticeRevisionModel.id == ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id)
            .where(ArrivalNoticeRevisionModel.arrival_notice_id == InboundDockAssignmentModel.arrival_notice_id, ArrivalNoticePurchaseOrderReferenceModel.purchase_order_code.ilike(f"%{purchase_order_code.strip()}%"))
            .exists()
        )
        query = query.where(po_exists)
    if responsible_user_id:
        query = query.where(select(UnloadingResponsibleAssignmentModel.id).where(UnloadingResponsibleAssignmentModel.unloading_operation_id == UnloadingOperationModel.id, UnloadingResponsibleAssignmentModel.user_id == responsible_user_id).exists())
    if arrived_from: query = query.where(GateCheckInModel.arrived_at >= arrived_from)
    if arrived_to: query = query.where(GateCheckInModel.arrived_at <= arrived_to)
    if unloading_started_from: query = query.where(UnloadingOperationModel.started_at >= unloading_started_from)
    if unloading_started_to: query = query.where(UnloadingOperationModel.started_at <= unloading_started_to)
    if unloading_completed_from: query = query.where(UnloadingOperationModel.completed_at >= unloading_completed_from)
    if unloading_completed_to: query = query.where(UnloadingOperationModel.completed_at <= unloading_completed_to)
    if dock_released_from: query = query.where(InboundDockAssignmentModel.released_at >= dock_released_from)
    if dock_released_to: query = query.where(InboundDockAssignmentModel.released_at <= dock_released_to)
    if has_pauses is not None:
        condition = select(UnloadingPauseModel.id).where(UnloadingPauseModel.unloading_operation_id == UnloadingOperationModel.id).exists()
        query = query.where(condition if has_pauses else ~condition)
    if has_anomalies is not None:
        condition = or_(GateCheckInModel.warning_count > 0, select(UnloadingSealOpeningEventModel.id).where(UnloadingSealOpeningEventModel.unloading_operation_id == UnloadingOperationModel.id, UnloadingSealOpeningEventModel.anomaly_detected.is_(True)).exists())
        query = query.where(condition if has_anomalies else ~condition)
    if has_time_corrections is not None:
        condition = select(DockOperationalTimeCorrectionModel.id).where(DockOperationalTimeCorrectionModel.organization_id == organization_id, or_(DockOperationalTimeCorrectionModel.resource_id == InboundDockAssignmentModel.id, DockOperationalTimeCorrectionModel.resource_id == UnloadingOperationModel.id)).exists()
        query = query.where(condition if has_time_corrections else ~condition)
    if data_quality_status: query = query.where(DockOperationMetricsProjectionModel.data_quality_status == data_quality_status)
    if active is not None:
        active_values = {"ASSIGNED", "MOVING_TO_DOCK", "AT_DOCK", "READY_FOR_UNLOADING", "UNLOADING_IN_PROGRESS", "UNLOADING_PAUSED", "UNLOADING_COMPLETED", "RELEASE_PENDING", "REASSIGNMENT_REQUIRED"}
        query = query.where(InboundDockAssignmentModel.status.in_(active_values) if active else ~InboundDockAssignmentModel.status.in_(active_values))
    if mine:
        mine_responsible = select(UnloadingResponsibleAssignmentModel.id).where(UnloadingResponsibleAssignmentModel.unloading_operation_id == UnloadingOperationModel.id, UnloadingResponsibleAssignmentModel.user_id == principal.user_id).exists()
        query = query.where(or_(InboundDockAssignmentModel.assigned_by_user_id == principal.user_id, mine_responsible))
    sort_columns = {
        "assigned_at": InboundDockAssignmentModel.assigned_at,
        "dock_arrived_at": InboundDockAssignmentModel.dock_arrived_at,
        "unloading_started_at": UnloadingOperationModel.started_at,
        "unloading_completed_at": UnloadingOperationModel.completed_at,
        "dock_released_at": InboundDockAssignmentModel.released_at,
        "plate": InboundDockAssignmentModel.observed_plate_snapshot,
    }
    sort_column = sort_columns.get(sort_by, InboundDockAssignmentModel.assigned_at)
    ordering = sort_column.asc() if sort_direction == "asc" else sort_column.desc()
    total = int(db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0)
    rows = list(db.scalars(query.order_by(ordering, InboundDockAssignmentModel.id).offset((page - 1) * page_size).limit(page_size)).unique())
    rows = [row for row in rows if principal.can_access_warehouse(row.warehouse_id)]
    return {"items": [_dock_operation_list_item(db, row) for row in rows], "total": total, "page": page, "page_size": page_size, "server_time": server_now()}


@router.get("/inbound-dock-assignments", response_model=PageResponse)
@router.get("/dock-assignments", response_model=PageResponse, include_in_schema=False)
def list_dock_assignments(
    search: str | None = None, cpv_code: str | None = Query(default=None, alias="CPV_code"), cit_code: str | None = Query(default=None, alias="CIT_code"), purchase_order_code: str | None = None,
    supplier_id: UUID | None = None, carrier_id: UUID | None = None, warehouse_id: UUID | None = None, dock_id: UUID | None = None, gate_check_in_id: UUID | None = None, vehicle_id: UUID | None = None, plate: str | None = None,
    assignment_status: str | None = None, unloading_status: str | None = None, priority: str | None = None, assigned_by: UUID | None = None, responsible_user_id: UUID | None = None,
    arrived_from: datetime | None = None, arrived_to: datetime | None = None, unloading_started_from: datetime | None = None, unloading_started_to: datetime | None = None, unloading_completed_from: datetime | None = None, unloading_completed_to: datetime | None = None, dock_released_from: datetime | None = None, dock_released_to: datetime | None = None,
    has_pauses: bool | None = None, has_anomalies: bool | None = None, has_time_corrections: bool | None = None, data_quality_status: str | None = None, active: bool | None = None, mine: bool | None = None,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=50, ge=1, le=200), sort_by: str = "assigned_at", sort_direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    principal=Depends(require_permission("logistics.inbound_dock_assignments.read")), db: Session = Depends(get_db),
):
    return _search_dock_assignments(db=db, principal=principal, operation_required=False, search=search, cpv_code=cpv_code, cit_code=cit_code, purchase_order_code=purchase_order_code, supplier_id=supplier_id, carrier_id=carrier_id, warehouse_id=warehouse_id, dock_id=dock_id, gate_check_in_id=gate_check_in_id, vehicle_id=vehicle_id, plate=plate, assignment_status=assignment_status, unloading_status=unloading_status, priority=priority, assigned_by=assigned_by, responsible_user_id=responsible_user_id, arrived_from=arrived_from, arrived_to=arrived_to, unloading_started_from=unloading_started_from, unloading_started_to=unloading_started_to, unloading_completed_from=unloading_completed_from, unloading_completed_to=unloading_completed_to, dock_released_from=dock_released_from, dock_released_to=dock_released_to, has_pauses=has_pauses, has_anomalies=has_anomalies, has_time_corrections=has_time_corrections, data_quality_status=data_quality_status, active=active, mine=mine, page=page, page_size=page_size, sort_by=sort_by, sort_direction=sort_direction)


@router.get("/inbound-dock-assignments/{assignment_id}", response_model=DockAssignmentResponse)
@router.get("/dock-assignments/{assignment_id}", response_model=DockAssignmentResponse, include_in_schema=False)
def get_dock_assignment(assignment_id: UUID, principal=Depends(require_permission("logistics.inbound_dock_assignments.read")), db: Session = Depends(get_db)):
    row = DockAssignmentService(db).get(assignment_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id); return row


def _assignment_command(assignment_id: UUID, action: str, idempotency_key: str, principal: LogisticsPrincipal, db: Session, execute: Callable[[], object], payload: dict | None = None):
    row = DockAssignmentService(db).get(assignment_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.assignment.{action}:{assignment_id}", payload=payload or {"assignment_id": str(assignment_id)}, execute=execute, response_model=DockAssignmentResponse)


@router.post("/inbound-dock-assignments/{assignment_id}/start-movement", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/start-movement", response_model=DockAssignmentResponse, include_in_schema=False)
def start_dock_movement(assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.assign")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _assignment_command(assignment_id, "start_movement", idempotency_key, principal, db, lambda: DockAssignmentService(db).start_movement(assignment_id, _organization(principal), principal))


@router.post("/inbound-dock-assignments/{assignment_id}/confirm-dock-arrival", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/confirm-arrival", response_model=DockAssignmentResponse, include_in_schema=False)
def confirm_dock_arrival(assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.assign")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _assignment_command(assignment_id, "confirm_arrival", idempotency_key, principal, db, lambda: DockAssignmentService(db).confirm_arrival(assignment_id, _organization(principal), principal))


@router.post("/inbound-dock-assignments/{assignment_id}/mark-ready", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/ready-for-unloading", response_model=DockAssignmentResponse, include_in_schema=False)
def mark_dock_assignment_ready(assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_readiness")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _assignment_command(assignment_id, "ready_for_unloading", idempotency_key, principal, db, lambda: DockAssignmentService(db).mark_ready(assignment_id, _organization(principal), principal))


@router.post("/inbound-dock-assignments/{assignment_id}/cancel", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/cancel", response_model=DockAssignmentResponse, include_in_schema=False)
def cancel_dock_assignment(assignment_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.cancel")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _assignment_command(assignment_id, "cancel", idempotency_key, principal, db, lambda: DockAssignmentService(db).cancel(assignment_id, _organization(principal), principal, body.reason), body.model_dump(mode="json"))


@router.post("/inbound-dock-assignments/{assignment_id}/request-reassignment", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/request-reassignment", response_model=DockAssignmentResponse, include_in_schema=False)
def request_dock_reassignment(assignment_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.reassign")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _assignment_command(assignment_id, "request_reassignment", idempotency_key, principal, db, lambda: DockAssignmentService(db).request_reassignment(assignment_id, _organization(principal), principal, body.reason), body.model_dump(mode="json"))


@router.post("/inbound-dock-assignments/{assignment_id}/reassign", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/reassign", response_model=DockAssignmentResponse, include_in_schema=False)
def reassign_dock(assignment_id: UUID, body: DockAssignmentReassignRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.reassign")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    row = DockAssignmentService(db).get(assignment_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.assignment.reassign:{assignment_id}", payload=body.model_dump(mode="json"), execute=lambda: DockReassignmentService(db).reassign(assignment_id, _organization(principal), principal, body.new_dock_id, body.assignment_hash, body.reason, body.row_version), response_model=DockAssignmentResponse)


@router.post("/inbound-dock-assignments/{assignment_id}/release-dock", response_model=DockAssignmentResponse)
@router.post("/dock-assignments/{assignment_id}/release", response_model=DockAssignmentResponse, include_in_schema=False)
def release_dock_assignment(assignment_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_dock_assignments.release")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _assignment_command(assignment_id, "release", idempotency_key, principal, db, lambda: UnloadingOperationService(db).release_dock(assignment_id, _organization(principal), principal, body.reason), body.model_dump(mode="json"))


@router.get("/inbound-dock-assignments/{assignment_id}/history")
@router.get("/dock-assignments/{assignment_id}/history", include_in_schema=False)
def get_dock_assignment_history(assignment_id: UUID, principal=Depends(require_permission("logistics.inbound_dock_assignments.read")), db: Session = Depends(get_db)):
    row = DockAssignmentService(db).get(assignment_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id); return _event_history(db, _organization(principal), dock_assignment_id=assignment_id)


@router.get("/inbound-dock-assignments/{assignment_id}/capabilities")
@router.get("/dock-assignments/{assignment_id}/capabilities", include_in_schema=False)
def get_dock_assignment_capabilities(assignment_id: UUID, principal=Depends(require_permission("logistics.inbound_dock_assignments.read")), db: Session = Depends(get_db)):
    row = get_dock_assignment(assignment_id, principal, db)
    mapping = {
        "ASSIGNED": ["start_movement", "cancel", "request_reassignment"],
        "MOVING_TO_DOCK": ["confirm_arrival", "cancel", "request_reassignment"],
        "AT_DOCK": ["create_unloading", "request_reassignment"],
        "UNLOADING_COMPLETED": ["release"], "RELEASE_PENDING": ["release"],
    }
    return {"assignment_id": row.id, "status": row.status, "capabilities": mapping.get(row.status, []), "server_time": server_now()}


@router.get("/inbound-dock-assignments/{assignment_id}/metrics")
@router.get("/dock-assignments/{assignment_id}/metrics", include_in_schema=False)
def get_dock_assignment_metrics(assignment_id: UUID, principal=Depends(require_permission("logistics.dock_operational_metrics.read")), db: Session = Depends(get_db)):
    assignment = get_dock_assignment(assignment_id, principal, db)
    operation = db.scalar(select(UnloadingOperationModel).where(UnloadingOperationModel.dock_assignment_id == assignment.id))
    return {"assignment_id": assignment.id, "metrics": DockOperationalProjectionService(db).metrics(operation) if operation else {}, "server_time": server_now()}


# Unloading execution -------------------------------------------------------

@router.get("/unloading-operations", response_model=PageResponse)
def list_unloading_operations(
    search: str | None = None, cpv_code: str | None = Query(default=None, alias="CPV_code"), cit_code: str | None = Query(default=None, alias="CIT_code"), purchase_order_code: str | None = None,
    supplier_id: UUID | None = None, carrier_id: UUID | None = None, warehouse_id: UUID | None = None, dock_id: UUID | None = None, gate_check_in_id: UUID | None = None, vehicle_id: UUID | None = None, plate: str | None = None,
    assignment_status: str | None = None, unloading_status: str | None = None, priority: str | None = None, assigned_by: UUID | None = None, responsible_user_id: UUID | None = None,
    arrived_from: datetime | None = None, arrived_to: datetime | None = None, unloading_started_from: datetime | None = None, unloading_started_to: datetime | None = None, unloading_completed_from: datetime | None = None, unloading_completed_to: datetime | None = None, dock_released_from: datetime | None = None, dock_released_to: datetime | None = None,
    has_pauses: bool | None = None, has_anomalies: bool | None = None, has_time_corrections: bool | None = None, data_quality_status: str | None = None, active: bool | None = None, mine: bool | None = None,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=50, ge=1, le=200), sort_by: str = "unloading_started_at", sort_direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db),
):
    return _search_dock_assignments(db=db, principal=principal, operation_required=True, search=search, cpv_code=cpv_code, cit_code=cit_code, purchase_order_code=purchase_order_code, supplier_id=supplier_id, carrier_id=carrier_id, warehouse_id=warehouse_id, dock_id=dock_id, gate_check_in_id=gate_check_in_id, vehicle_id=vehicle_id, plate=plate, assignment_status=assignment_status, unloading_status=unloading_status, priority=priority, assigned_by=assigned_by, responsible_user_id=responsible_user_id, arrived_from=arrived_from, arrived_to=arrived_to, unloading_started_from=unloading_started_from, unloading_started_to=unloading_started_to, unloading_completed_from=unloading_completed_from, unloading_completed_to=unloading_completed_to, dock_released_from=dock_released_from, dock_released_to=dock_released_to, has_pauses=has_pauses, has_anomalies=has_anomalies, has_time_corrections=has_time_corrections, data_quality_status=data_quality_status, active=active, mine=mine, page=page, page_size=page_size, sort_by=sort_by, sort_direction=sort_direction)


@router.post("/inbound-dock-assignments/{assignment_id}/unloading-operation", response_model=UnloadingOperationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/dock-assignments/{assignment_id}/unloading-operation", response_model=UnloadingOperationResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_unloading_operation(assignment_id: UUID, body: UnloadingOperationCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.create")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    assignment = DockAssignmentService(db).get(assignment_id, _organization(principal)); _assert_warehouse_scope(principal, assignment.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.unloading.create:{assignment_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingOperationService(db).create(assignment_id, _organization(principal), principal, body.unloading_method.value, body.notes), response_model=UnloadingOperationResponse)


@router.get("/unloading-operations/{operation_id}", response_model=UnloadingOperationResponse)
def get_unloading_operation(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    row = UnloadingOperationService(db).get(operation_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id); return row


def _unloading_command(operation_id: UUID, action: str, idempotency_key: str, principal: LogisticsPrincipal, db: Session, execute: Callable[[], object], payload: dict | None = None):
    row = UnloadingOperationService(db).get(operation_id, _organization(principal)); _assert_warehouse_scope(principal, row.warehouse_id)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.unloading.{action}:{operation_id}", payload=payload or {"operation_id": str(operation_id)}, execute=execute, response_model=UnloadingOperationResponse)


@router.post("/unloading-operations/{operation_id}/validate-readiness", response_model=UnloadingOperationResponse)
def validate_unloading_readiness(operation_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_readiness")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        operation = UnloadingOperationService(db).get(operation_id, _organization(principal), lock=True)
        assignment = DockAssignmentService(db).get(operation.dock_assignment_id, _organization(principal), lock=True)
        return UnloadingReadinessService(db).validate(operation, assignment, principal)
    return _unloading_command(operation_id, "validate_readiness", idempotency_key, principal, db, execute)


@router.post("/unloading-operations/{operation_id}/start", response_model=UnloadingOperationResponse)
def start_unloading(operation_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.start")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _unloading_command(operation_id, "start", idempotency_key, principal, db, lambda: UnloadingOperationService(db).start(operation_id, _organization(principal), principal))


@router.post("/unloading-operations/{operation_id}/cancel", response_model=UnloadingOperationResponse)
def cancel_unloading(operation_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.cancel")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _unloading_command(operation_id, "cancel", idempotency_key, principal, db, lambda: UnloadingOperationService(db).cancel(operation_id, _organization(principal), principal, body.reason), body.model_dump(mode="json"))


@router.post("/unloading-operations/{operation_id}/pause", response_model=UnloadingOperationResponse)
def pause_unloading(operation_id: UUID, body: UnloadingPauseRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.pause")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _unloading_command(operation_id, "pause", idempotency_key, principal, db, lambda: UnloadingOperationService(db).pause(operation_id, _organization(principal), principal, body.reason_code, body.reason, body.severity, body.evidence_file_id)[0], body.model_dump(mode="json"))


@router.post("/unloading-operations/{operation_id}/resume", response_model=UnloadingOperationResponse)
def resume_unloading(operation_id: UUID, body: UnloadingResumeRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.resume")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _unloading_command(operation_id, "resume", idempotency_key, principal, db, lambda: UnloadingOperationService(db).resume(operation_id, _organization(principal), principal, body.resolution)[0], body.model_dump(mode="json"))


@router.post("/unloading-operations/{operation_id}/abort", response_model=UnloadingOperationResponse)
def abort_unloading(operation_id: UUID, body: UnloadingAbortRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.abort")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _unloading_command(operation_id, "abort", idempotency_key, principal, db, lambda: UnloadingOperationService(db).abort(operation_id, _organization(principal), principal, body.reason), body.model_dump(mode="json"))


@router.post("/unloading-operations/{operation_id}/complete", response_model=UnloadingOperationResponse)
def complete_unloading(operation_id: UUID, body: UnloadingCompleteRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.complete")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _unloading_command(operation_id, "complete", idempotency_key, principal, db, lambda: UnloadingOperationService(db).complete(operation_id, _organization(principal), principal, body.completion_note), body.model_dump(mode="json"))


@router.get("/unloading-operations/{operation_id}/capabilities")
def get_unloading_capabilities(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    row = get_unloading_operation(operation_id, principal, db)
    mapping = {"READINESS_PENDING": ["record_readiness", "validate_readiness", "cancel"], "READY": ["start", "cancel"], "IN_PROGRESS": ["pause", "complete", "abort"], "PAUSED": ["resume", "abort"], "COMPLETED": ["prepare_receiving_scan", "release_dock"], "ABORTED": ["release_dock"]}
    return {"operation_id": row.id, "status": row.status, "readiness_status": row.readiness_status, "capabilities": mapping.get(row.status, []), "server_time": server_now()}


@router.get("/unloading-operations/{operation_id}/history")
def get_unloading_history(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    row = get_unloading_operation(operation_id, principal, db); return _event_history(db, _organization(principal), unloading_operation_id=row.id)


@router.get("/unloading-operations/{operation_id}/metrics")
def get_unloading_metrics(operation_id: UUID, principal=Depends(require_permission("logistics.dock_operational_metrics.read")), db: Session = Depends(get_db)):
    row = get_unloading_operation(operation_id, principal, db); return {"operation_id": row.id, "metrics": DockOperationalProjectionService(db).metrics(row), "server_time": server_now()}


@router.get("/unloading-operations/{operation_id}/integrity")
def get_unloading_integrity(operation_id: UUID, principal=Depends(require_permission("logistics.dock_operational_integrity.read")), db: Session = Depends(get_db)):
    row = get_unloading_operation(operation_id, principal, db); return DockOperationIntegrityService(db).verify(row)


@router.get("/unloading-operations/{operation_id}/receiving-preparation", response_model=ReceivingScanPreparationResponse)
@router.get("/unloading-operations/{operation_id}/receiving-scan-preparation", response_model=ReceivingScanPreparationResponse, include_in_schema=False)
def get_receiving_scan_preparation(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    row = get_unloading_operation(operation_id, principal, db); return ReceivingScanPreparationService(db).get(row)


# Checklists, responsibles, seal, pauses and corrections -------------------

@router.get("/unloading-operations/{operation_id}/readiness-checks")
def list_unloading_readiness_checks(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    definitions = UnloadingReadinessService(db).ensure_definitions(operation)
    results = list(db.scalars(select(UnloadingReadinessCheckResultModel).where(UnloadingReadinessCheckResultModel.unloading_operation_id == operation.id)))
    return {"definitions": [_row_dict(row) for row in definitions], "results": [_row_dict(row) for row in results], "server_time": server_now()}


@router.post("/unloading-operations/{operation_id}/readiness-checks", status_code=status.HTTP_201_CREATED)
def record_unloading_readiness_check(operation_id: UUID, body: UnloadingReadinessCheckRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_readiness")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.readiness.record:{operation_id}:{body.check_definition_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingReadinessService(db).record(operation, principal, body.check_definition_id, body.result.value, body.observation, body.evidence_file_id))


@router.post("/unloading-operations/{operation_id}/readiness-checks/{result_id}/request-override")
def request_readiness_override(operation_id: UUID, result_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.request_override")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.readiness.override_request:{result_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingReadinessService(db).request_override(result_id, operation, principal, body.reason))


def _decide_readiness_override(operation_id: UUID, result_id: UUID, approve: bool, body: ReasonRequest, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.readiness.override_decision:{result_id}", payload={"approve": approve, **body.model_dump(mode="json")}, execute=lambda: UnloadingReadinessService(db).decide_override(result_id, operation, principal, approve, body.reason))


@router.post("/unloading-operations/{operation_id}/readiness-checks/{result_id}/approve-override")
def approve_readiness_override(operation_id: UUID, result_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.approve_override")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _decide_readiness_override(operation_id, result_id, True, body, idempotency_key, principal, db)


@router.post("/unloading-operations/{operation_id}/readiness-checks/{result_id}/reject-override")
def reject_readiness_override(operation_id: UUID, result_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.approve_override")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _decide_readiness_override(operation_id, result_id, False, body, idempotency_key, principal, db)


@router.get("/unloading-operations/{operation_id}/completion-checks")
def list_unloading_completion_checks(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    definitions = UnloadingCompletionService(db).ensure_definitions(operation.organization_id)
    results = list(db.scalars(select(UnloadingCompletionCheckResultModel).where(UnloadingCompletionCheckResultModel.unloading_operation_id == operation.id)))
    return {"definitions": [_row_dict(row) for row in definitions], "results": [_row_dict(row) for row in results], "server_time": server_now()}


@router.post("/unloading-operations/{operation_id}/completion-checks", status_code=status.HTTP_201_CREATED)
def record_unloading_completion_check(operation_id: UUID, body: UnloadingCompletionCheckRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.complete")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.completion_check.record:{operation_id}:{body.check_definition_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingCompletionService(db).record(operation, principal, body.check_definition_id, body.result.value, body.observation))


@router.get("/unloading-operations/{operation_id}/responsibles")
def list_unloading_responsibles(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    return [_row_dict(row) for row in db.scalars(select(UnloadingResponsibleAssignmentModel).where(UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id))]


@router.post("/unloading-operations/{operation_id}/responsibles", status_code=status.HTTP_201_CREATED)
def assign_unloading_responsible(operation_id: UUID, body: UnloadingResponsibleCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.responsible.assign:{operation_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingResponsibilityService(db).assign(operation, principal, body.responsibility_type.value, body.user_id, body.business_partner_id, body.team_reference_id))


def _responsible_transition(operation_id: UUID, responsible_id: UUID, target: str, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.responsible.{target.lower()}:{responsible_id}", payload={"target": target}, execute=lambda: UnloadingResponsibilityService(db).transition(responsible_id, operation, target))


@router.post("/unloading-operations/{operation_id}/responsibles/{responsible_id}/accept")
def accept_unloading_responsible(operation_id: UUID, responsible_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _responsible_transition(operation_id, responsible_id, "ACCEPTED", idempotency_key, principal, db)


@router.post("/unloading-operations/{operation_id}/responsibles/{responsible_id}/release")
def release_unloading_responsible(operation_id: UUID, responsible_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _responsible_transition(operation_id, responsible_id, "RELEASED", idempotency_key, principal, db)


@router.post("/unloading-operations/{operation_id}/responsibles/{responsible_id}/revoke")
def revoke_unloading_responsible(operation_id: UUID, responsible_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _responsible_transition(operation_id, responsible_id, "REVOKED", idempotency_key, principal, db)


@router.get("/unloading-operations/{operation_id}/equipment")
def list_unloading_equipment(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    return [_row_dict(row) for row in db.scalars(select(UnloadingEquipmentAssignmentModel).where(UnloadingEquipmentAssignmentModel.unloading_operation_id == operation.id))]


@router.post("/unloading-operations/{operation_id}/equipment", status_code=status.HTTP_201_CREATED)
def assign_unloading_equipment(operation_id: UUID, body: UnloadingEquipmentCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_readiness")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.equipment.assign:{operation_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingEquipmentService(db).assign(operation, principal, body.equipment_reference_id, body.equipment_type, body.source_type, body.identifier_snapshot))


@router.post("/unloading-operations/{operation_id}/equipment/{equipment_assignment_id}/release")
def release_unloading_equipment(operation_id: UUID, equipment_assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_readiness")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.equipment.release:{equipment_assignment_id}", payload={"equipment_assignment_id": str(equipment_assignment_id)}, execute=lambda: UnloadingEquipmentService(db).release(equipment_assignment_id, operation, principal))


@router.get("/unloading-operations/{operation_id}/seal-opening")
def get_unloading_seal_opening(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    row = db.scalar(select(UnloadingSealOpeningEventModel).where(UnloadingSealOpeningEventModel.unloading_operation_id == operation.id))
    return _row_dict(row) if row else None


@router.post("/unloading-operations/{operation_id}/seal-opening", status_code=status.HTTP_201_CREATED)
def record_unloading_seal_opening(operation_id: UUID, body: UnloadingSealOpeningRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.record_seal_opening")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.seal_opening.record:{operation_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingSealOpeningService(db).record(operation, principal, body.opening_status, body.witnessed_by_user_id, body.photo_file_id, body.observation))


@router.get("/unloading-operations/{operation_id}/pauses")
def list_unloading_pauses(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    return [_row_dict(row) for row in db.scalars(select(UnloadingPauseModel).where(UnloadingPauseModel.unloading_operation_id == operation.id).order_by(UnloadingPauseModel.pause_number))]


@router.get("/unloading-pauses/{pause_id}")
def get_unloading_pause(pause_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    row = db.get(UnloadingPauseModel, pause_id)
    if row is None: raise ApplicationError("UNLOADING_PAUSE_NOT_FOUND", "Pausa no encontrada.", 404)
    operation = get_unloading_operation(row.unloading_operation_id, principal, db)
    return _row_dict(row)


@router.get("/unloading-operations/{operation_id}/operational-times")
@router.get("/unloading-operations/{operation_id}/times", include_in_schema=False)
def get_unloading_times(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    assignment = db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
    return {"movement_started_at": assignment.movement_started_at if assignment else None, "dock_arrived_at": assignment.dock_arrived_at if assignment else None, "unloading_started_at": operation.started_at, "unloading_completed_at": operation.completed_at, "dock_released_at": assignment.released_at if assignment else None, "gross_duration_seconds": operation.gross_duration_seconds, "pause_seconds": operation.total_pause_seconds, "net_duration_seconds": operation.net_duration_seconds, "server_time": server_now()}


@router.get("/unloading-operations/{operation_id}/time-corrections")
def list_unloading_time_corrections(operation_id: UUID, principal=Depends(require_permission("logistics.unloading_operations.read")), db: Session = Depends(get_db)):
    operation = get_unloading_operation(operation_id, principal, db)
    ids = [operation.id, operation.dock_assignment_id]
    return [_row_dict(row) for row in db.scalars(select(DockOperationalTimeCorrectionModel).where(DockOperationalTimeCorrectionModel.organization_id == operation.organization_id, DockOperationalTimeCorrectionModel.resource_id.in_(ids)))]


@router.post("/unloading-operations/{operation_id}/time-corrections", status_code=status.HTTP_201_CREATED)
def request_unloading_time_correction(operation_id: UUID, body: DockOperationalTimeCorrectionCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.correct_times")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.time_correction.request:{operation_id}:{body.field_code}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingTimeCorrectionService(db).request(operation, principal, body.field_code, body.proposed_timestamp, body.reason, body.evidence_file_id))


def _decide_time_correction(operation_id: UUID, correction_id: UUID, approve: bool, body: ReasonRequest, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    operation = get_unloading_operation(operation_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.time_correction.decision:{correction_id}", payload={"approve": approve, **body.model_dump(mode="json")}, execute=lambda: UnloadingTimeCorrectionService(db).decide(correction_id, operation, principal, approve, body.reason))


@router.post("/unloading-operations/{operation_id}/time-corrections/{correction_id}/approve")
def approve_unloading_time_correction(operation_id: UUID, correction_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.correct_times")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _decide_time_correction(operation_id, correction_id, True, body, idempotency_key, principal, db)


@router.post("/unloading-operations/{operation_id}/time-corrections/{correction_id}/reject")
def reject_unloading_time_correction(operation_id: UUID, correction_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.correct_times")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return _decide_time_correction(operation_id, correction_id, False, body, idempotency_key, principal, db)


# Canonical resource-command endpoints required by the Phase 038 contract.

def _readiness_result_operation(result_id: UUID, principal: LogisticsPrincipal, db: Session):
    result = db.get(UnloadingReadinessCheckResultModel, result_id)
    if result is None:
        raise ApplicationError("UNLOADING_READINESS_RESULT_NOT_FOUND", "Resultado de readiness no encontrado.", 404)
    return result, get_unloading_operation(result.unloading_operation_id, principal, db)


@router.post("/unloading-readiness-check-results/{result_id}/request-override")
def request_readiness_override_by_id(result_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.request_override")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    _result, operation = _readiness_result_operation(result_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.readiness.override_request:{result_id}", payload=body.model_dump(mode="json"), execute=lambda: UnloadingReadinessService(db).request_override(result_id, operation, principal, body.reason))


def _decide_readiness_override_by_id(result_id: UUID, approve: bool, body: ReasonRequest, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    _result, operation = _readiness_result_operation(result_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.readiness.override_decision:{result_id}", payload={"approve": approve, **body.model_dump(mode="json")}, execute=lambda: UnloadingReadinessService(db).decide_override(result_id, operation, principal, approve, body.reason))


@router.post("/unloading-readiness-check-results/{result_id}/approve-override")
def approve_readiness_override_by_id(result_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.approve_override")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _decide_readiness_override_by_id(result_id, True, body, idempotency_key, principal, db)


@router.post("/unloading-readiness-check-results/{result_id}/reject-override")
def reject_readiness_override_by_id(result_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.approve_override")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _decide_readiness_override_by_id(result_id, False, body, idempotency_key, principal, db)


def _responsible_operation(responsible_assignment_id: UUID, principal: LogisticsPrincipal, db: Session):
    row = db.get(UnloadingResponsibleAssignmentModel, responsible_assignment_id)
    if row is None:
        raise ApplicationError("UNLOADING_RESPONSIBLE_NOT_FOUND", "Asignación de responsable no encontrada.", 404)
    return row, get_unloading_operation(row.unloading_operation_id, principal, db)


def _responsible_transition_by_id(responsible_assignment_id: UUID, target: str, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    _row, operation = _responsible_operation(responsible_assignment_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.responsible.{target.lower()}:{responsible_assignment_id}", payload={"target": target}, execute=lambda: UnloadingResponsibilityService(db).transition(responsible_assignment_id, operation, target))


@router.post("/unloading-responsible-assignments/{assignment_id}/accept")
def accept_unloading_responsible_by_id(assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _responsible_transition_by_id(assignment_id, "ACCEPTED", idempotency_key, principal, db)


@router.post("/unloading-responsible-assignments/{assignment_id}/release")
def release_unloading_responsible_by_id(assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _responsible_transition_by_id(assignment_id, "RELEASED", idempotency_key, principal, db)


@router.post("/unloading-responsible-assignments/{assignment_id}/revoke")
def revoke_unloading_responsible_by_id(assignment_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.manage_responsibles")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _responsible_transition_by_id(assignment_id, "REVOKED", idempotency_key, principal, db)


@router.post("/unloading-pauses/{pause_id}/resume", response_model=UnloadingOperationResponse)
def resume_unloading_by_pause(pause_id: UUID, body: UnloadingResumeRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.resume")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    pause = db.get(UnloadingPauseModel, pause_id)
    if pause is None:
        raise ApplicationError("UNLOADING_PAUSE_NOT_FOUND", "Pausa no encontrada.", 404)
    operation = get_unloading_operation(pause.unloading_operation_id, principal, db)
    return _unloading_command(operation.id, "resume", idempotency_key, principal, db, lambda: UnloadingOperationService(db).resume(operation.id, _organization(principal), principal, body.resolution)[0], {"pause_id": str(pause_id), **body.model_dump(mode="json")})


@router.post("/unloading-pauses/{pause_id}/cancel", response_model=UnloadingOperationResponse)
def cancel_unloading_pause(pause_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.pause")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    pause = db.get(UnloadingPauseModel, pause_id)
    if pause is None:
        raise ApplicationError("UNLOADING_PAUSE_NOT_FOUND", "Pausa no encontrada.", 404)
    operation = get_unloading_operation(pause.unloading_operation_id, principal, db)
    return _unloading_command(operation.id, "cancel_pause", idempotency_key, principal, db, lambda: UnloadingOperationService(db).cancel_pause(pause_id, _organization(principal), principal, body.reason)[0], {"pause_id": str(pause_id), **body.model_dump(mode="json")})


def _time_correction_operation(correction_id: UUID, principal: LogisticsPrincipal, db: Session):
    correction = db.scalar(select(DockOperationalTimeCorrectionModel).where(DockOperationalTimeCorrectionModel.id == correction_id, DockOperationalTimeCorrectionModel.organization_id == _organization(principal)))
    if correction is None:
        raise ApplicationError("DOCK_TIME_CORRECTION_NOT_FOUND", "Corrección de tiempo no encontrada.", 404)
    if correction.resource_type == "UNLOADING_OPERATION":
        operation = get_unloading_operation(correction.resource_id, principal, db)
    else:
        operation = db.scalar(select(UnloadingOperationModel).where(UnloadingOperationModel.dock_assignment_id == correction.resource_id, UnloadingOperationModel.organization_id == _organization(principal)))
        if operation is None:
            raise ApplicationError("UNLOADING_OPERATION_NOT_FOUND", "Operación de descarga no encontrada.", 404)
        _assert_warehouse_scope(principal, operation.warehouse_id)
    return correction, operation


def _decide_time_correction_by_id(correction_id: UUID, approve: bool, body: ReasonRequest, idempotency_key: str, principal: LogisticsPrincipal, db: Session):
    _correction, operation = _time_correction_operation(correction_id, principal, db)
    return _command(db=db, principal=principal, idempotency_key=idempotency_key, operation=f"phase038.time_correction.decision:{correction_id}", payload={"approve": approve, **body.model_dump(mode="json")}, execute=lambda: UnloadingTimeCorrectionService(db).decide(correction_id, operation, principal, approve, body.reason))


@router.post("/dock-operational-time-corrections/{correction_id}/approve")
def approve_time_correction_by_id(correction_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.correct_times")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _decide_time_correction_by_id(correction_id, True, body, idempotency_key, principal, db)


@router.post("/dock-operational-time-corrections/{correction_id}/reject")
def reject_time_correction_by_id(correction_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.unloading_operations.correct_times")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return _decide_time_correction_by_id(correction_id, False, body, idempotency_key, principal, db)


@router.post("/dock-operation-exports", response_model=DockOperationExportResponse, status_code=status.HTTP_202_ACCEPTED)
def request_dock_operation_export(body: DockOperationExportRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.dock_operational_metrics.export")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    if body.warehouse_id is not None:
        _assert_warehouse_scope(principal, body.warehouse_id)
    filters = jsonable_encoder(body.model_dump(exclude={"export_format"}, exclude_none=True))
    if body.warehouse_id is None and principal.warehouse_ids:
        filters["authorized_warehouse_ids"] = list(principal.warehouse_ids)
    return _command(
        db=db,
        principal=principal,
        idempotency_key=idempotency_key,
        operation="phase038.export.request",
        payload=body.model_dump(mode="json"),
        execute=lambda: DockOperationExportService(db).request(
            principal, _organization(principal), body.export_format, filters
        ),
        response_model=DockOperationExportResponse,
    )


@router.get("/dock-operation-exports/{export_job_id}", response_model=DockOperationExportResponse)
def get_dock_operation_export(export_job_id: UUID, principal=Depends(require_permission("logistics.dock_operational_metrics.export")), db: Session = Depends(get_db)):
    try:
        row = DockOperationExportService(db).get(export_job_id, _organization(principal))
    except LookupError as exc:
        raise ApplicationError("DOCK_OPERATION_EXPORT_NOT_FOUND", "Exportación operativa no encontrada.", 404) from exc
    if row.warehouse_id is not None:
        _assert_warehouse_scope(principal, row.warehouse_id)
    return row


@router.get("/dock-operation-exports/{export_job_id}/download")
def download_dock_operation_export(export_job_id: UUID, principal=Depends(require_permission("logistics.dock_operational_metrics.export")), db: Session = Depends(get_db)):
    row = get_dock_operation_export(export_job_id, principal, db)
    try:
        response = DockOperationExportService(db).download(row, principal)
    except RuntimeError as exc:
        raise ApplicationError("DOCK_OPERATION_EXPORT_NOT_READY", "La exportación aún no está disponible.", 409) from exc
    db.commit()
    return response


@router.get("/dock-operation-metrics")
def list_dock_operational_metrics(warehouse_id: UUID | None = None, dock_id: UUID | None = None, principal=Depends(require_permission("logistics.dock_operational_metrics.read")), db: Session = Depends(get_db)):
    query = select(UnloadingOperationModel).where(UnloadingOperationModel.organization_id == _organization(principal))
    if warehouse_id is not None: _assert_warehouse_scope(principal, warehouse_id); query = query.where(UnloadingOperationModel.warehouse_id == warehouse_id)
    if dock_id is not None: query = query.where(UnloadingOperationModel.dock_id == dock_id)
    rows = [row for row in db.scalars(query) if principal.can_access_warehouse(row.warehouse_id)]
    return [{"operation_id": row.id, "warehouse_id": row.warehouse_id, "dock_id": row.dock_id, "metrics": DockOperationalProjectionService(db).metrics(row)} for row in rows]
