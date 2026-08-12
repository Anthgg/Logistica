"""Phase 044 — FastAPI router for the inventory ledger."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any, Mapping
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.modules.logistics.inventory.ledger.application.services.compensation_service import (
    InventoryMovementCompensationService,
)
from app.modules.logistics.inventory.ledger.application.services.ingestion_service import (
    PreparedInventoryEventIngestionService,
)
from app.modules.logistics.inventory.ledger.application.services.integrity_service import (
    InventoryLedgerCheckpointService,
    InventoryLedgerExportService,
    InventoryLedgerIntegrityService,
    InventoryLedgerReconciliationService,
    InventoryMovementSnapshotProvider,
)
from app.modules.logistics.inventory.ledger.application.services.kardex_query_service import (
    InventoryKardexQueryService,
    KardexFilter,
)
from app.modules.logistics.inventory.ledger.application.services.posting_service import (
    InventoryMovementPostingService,
)
from app.modules.logistics.inventory.ledger.application.services.preparation_services import (
    InventoryBalancePreparationService,
    InventoryTraceabilityPreparationService,
)
from app.modules.logistics.inventory.ledger.application.services.validation_service import (
    InventoryMovementValidationService,
)
from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryLedgerError,
)
from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
    SourceBackedAvailabilityProvider,
)
from app.modules.logistics.inventory.ledger.domain.services.line_service import (
    InventoryMovementLineService,
)
from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
    InventoryMovementSourceRegistry,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    RiskLevel,
)
from app.modules.logistics.inventory.ledger.infrastructure.jobs.jobs import (
    retry_failed_posting,
    run_export_job,
    run_reconciliation,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryKardexExportJobModel,
    InventoryLedgerCheckpointModel,
    InventoryLedgerPartitionModel,
    InventoryLedgerReconciliationJobModel,
    InventoryLedgerReconciliationResultModel,
    InventoryMovementCompensationRequestModel,
    InventoryMovementModel,
    InventoryMovementPostingRequestModel,
)
from app.modules.logistics.inventory.ledger.infrastructure.source_adapters.adapters import (
    build_default_registry,
)
from app.modules.logistics.inventory.ledger.presentation.dependencies import (
    StepUpLevel,
    enforce_inventory_route_security,
    require_capability,
    require_csrf,
    require_step_up,
)
from app.modules.logistics.inventory.ledger.presentation.schemas.schemas import (
    InventoryBalancePreparationResponse,
    InventoryKardexExportCreate,
    InventoryKardexExportResponse,
    InventoryKardexQuery,
    InventoryKardexResponse,
    InventoryKardexRow,
    InventoryKardexRunningQuantityRow,
    InventoryLedgerCheckpointResponse,
    InventoryLedgerPartitionResponse,
    InventoryLedgerReconciliationJobCreate,
    InventoryLedgerReconciliationJobResponse,
    InventoryLedgerReconciliationResult,
    InventoryLedgerVerificationResponse,
    InventoryMovementCapabilities,
    InventoryMovementCompensationDecisionRequest,
    InventoryMovementCompensationRequestCreate,
    InventoryMovementCompensationRequestResponse,
    InventoryMovementDetail,
    InventoryMovementIntegrityResponse,
    InventoryMovementLineResponse,
    InventoryMovementListResponse,
    InventoryMovementPostingRequestCreate,
    InventoryMovementPostingRequestResponse,
    InventoryMovementResponse,
    InventoryMovementSnapshotResponse,
    InventoryMovementSourceResponse,
    InventoryMovementSummary,
    InventoryPositionResponse,
    InventoryTraceabilityPreparationResponse,
    PreparedInventoryEventValidationResponse,
)

router = APIRouter(
    tags=["Inventory Ledger"],
    dependencies=[Depends(enforce_inventory_route_security)],
)
# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _validation_service(
    db: Annotated[Session, Depends(get_db)],
) -> InventoryMovementValidationService:
    return InventoryMovementValidationService(
        availability_provider=SourceBackedAvailabilityProvider(db),
        line_service=InventoryMovementLineService(db),
    )


def _posting_service(
    db: Annotated[Session, Depends(get_db)],
    validation_service: InventoryMovementValidationService = Depends(_validation_service),
) -> InventoryMovementPostingService:
    return InventoryMovementPostingService(db, validation_service=validation_service)


def _ingestion_service(
    posting: InventoryMovementPostingService = Depends(_posting_service),
) -> PreparedInventoryEventIngestionService:
    registry = InventoryMovementSourceRegistry(build_default_registry().values())
    return PreparedInventoryEventIngestionService(
        registry=registry,
        posting_service=posting,
    )


def _kardex_service(db: Annotated[Session, Depends(get_db)]) -> InventoryKardexQueryService:
    return InventoryKardexQueryService(db)


def _compensation_service(
    db: Annotated[Session, Depends(get_db)],
) -> InventoryMovementCompensationService:
    return InventoryMovementCompensationService(db)


def _balance_service(db: Annotated[Session, Depends(get_db)]) -> InventoryBalancePreparationService:
    return InventoryBalancePreparationService(db)


def _traceability_service(
    db: Annotated[Session, Depends(get_db)],
) -> InventoryTraceabilityPreparationService:
    return InventoryTraceabilityPreparationService(db)


def _integrity_service(db: Annotated[Session, Depends(get_db)]) -> InventoryLedgerIntegrityService:
    return InventoryLedgerIntegrityService(db)


def _checkpoint_service(
    db: Annotated[Session, Depends(get_db)],
) -> InventoryLedgerCheckpointService:
    return InventoryLedgerCheckpointService(db)


def _reconciliation_service(
    db: Annotated[Session, Depends(get_db)],
) -> InventoryLedgerReconciliationService:
    return InventoryLedgerReconciliationService(db)


def _export_service(db: Annotated[Session, Depends(get_db)]) -> InventoryLedgerExportService:
    return InventoryLedgerExportService(db)


def _snapshot_provider(
    db: Annotated[Session, Depends(get_db)],
) -> InventoryMovementSnapshotProvider:
    return InventoryMovementSnapshotProvider(db)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summary(movement: InventoryMovementModel, *, integrity: str) -> InventoryMovementSummary:
    return InventoryMovementSummary(
        id=movement.id,
        movement_code=movement.movement_code,
        ledger_sequence=movement.ledger_sequence,
        movement_family=movement.movement_family,
        movement_type=movement.movement_type,
        status=movement.status,
        occurred_at=movement.occurred_at,
        posted_at=movement.posted_at,
        warehouse_summary=(
            {"warehouse_id": str(movement.warehouse_scope_id)}
            if movement.warehouse_scope_id
            else None
        ),
        product_count=movement.line_count,
        line_count=movement.line_count,
        source_summary={
            "source_system": movement.source_system,
            "source_event_id": movement.source_event_id,
        },
        source_document_summary=(
            {
                "source_document_type": movement.source_document_type,
                "source_document_code": movement.source_document_code,
            }
            if movement.source_document_type or movement.source_document_code
            else None
        ),
        reason_code=movement.reason_code,
        compensation_status=("COMPENSATED" if movement.compensated_by_movement_id else "ACTIVE"),
        integrity_status=integrity,
        previous_hash_partial=(
            movement.previous_movement_hash[:16] if movement.previous_movement_hash else None
        ),
        movement_hash_partial=movement.movement_hash[:16],
        capabilities=_capabilities_for_movement(movement),
    )


def _capabilities_for_movement(movement: InventoryMovementModel) -> InventoryMovementCapabilities:
    return InventoryMovementCapabilities(
        can_read=True,
        can_read_sources=True,
        can_read_snapshot=True,
        can_read_history=True,
        can_read_integrity=True,
    )


# ---------------------------------------------------------------------------
# Movements list / detail
# ---------------------------------------------------------------------------


@router.get(
    "/movements",
    response_model=InventoryMovementListResponse,
    summary="List inventory movements (append-only book)",
)
@require_capability("logistics.inventory_ledger.read")
def list_movements(
    organization_id: UUID,
    db: Session = Depends(get_db),
    flt: InventoryKardexQuery = Depends(),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    try:
        kardex_filter = KardexFilter(
            organization_id=organization_id,
            **{
                k: v
                for k, v in flt.model_dump(exclude_none=True).items()
                if k in KardexFilter.__dataclass_fields__
            },
        )
        rows, total = kardex.list_movements(kardex_filter)
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementListResponse(
        items=[_row_to_summary(row) for row in rows],
        total=total,
        page=flt.page,
        page_size=flt.page_size,
    )


def _row_to_summary(row) -> InventoryMovementSummary:
    return InventoryMovementSummary(
        id=row.movement_id,
        movement_code=row.movement_code,
        ledger_sequence=row.ledger_sequence,
        movement_family=row.movement_family,
        movement_type=row.movement_type,
        status=row.status,
        occurred_at=row.occurred_at,
        posted_at=row.posted_at,
        warehouse_summary=({"warehouse_id": str(row.warehouse_id)} if row.warehouse_id else None),
        product_count=row.line_count,
        line_count=row.line_count,
        source_summary=(
            {
                "source_system": row.source_event_id.split(":")[0]
                if ":" in row.source_event_id
                else "INVENTORY_LEDGER",
                "source_event_id": row.source_event_id,
            }
        ),
        source_document_summary=None,
        reason_code=row.reason_code,
        compensation_status=row.compensation_status,
        integrity_status="OK",
        previous_hash_partial=None,
        movement_hash_partial=row.movement_hash_partial,
    )


@router.get(
    "/movements/{movement_id}",
    response_model=InventoryMovementDetail,
    summary="Get inventory movement detail",
)
@require_capability("logistics.inventory_ledger.read")
def get_movement(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    try:
        detail = kardex.get_movement_detail(organization_id, movement_id)
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    movement = detail["movement"]
    return InventoryMovementDetail(
        movement=InventoryMovementResponse.model_validate(movement),
        lines=[InventoryMovementLineResponse.model_validate(line) for line in detail["lines"]],
        sources=[InventoryMovementSourceResponse.model_validate(src) for src in detail["sources"]],
        positions=[InventoryPositionResponse.model_validate(p) for p in detail["positions"]],
        compensation=(
            InventoryMovementResponse.model_validate(detail["compensation"])
            if detail["compensation"] is not None
            else None
        ),
        capabilities=_capabilities_for_movement(movement),
        balance_preparation_summary=None,
        traceability_preparation_summary=None,
    )


@router.get(
    "/movements/{movement_id}/lines",
    response_model=list[InventoryMovementLineResponse],
    summary="Get movement lines",
)
@require_capability("logistics.inventory_ledger.read")
def get_movement_lines(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    detail = kardex.get_movement_detail(organization_id, movement_id)
    return [InventoryMovementLineResponse.model_validate(line) for line in detail["lines"]]


@router.get(
    "/movements/{movement_id}/sources",
    response_model=list[InventoryMovementSourceResponse],
    summary="Get movement sources",
)
@require_capability("logistics.inventory_ledger.read_sources")
def get_movement_sources(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    detail = kardex.get_movement_detail(organization_id, movement_id)
    return [InventoryMovementSourceResponse.model_validate(src) for src in detail["sources"]]


@router.get(
    "/movements/{movement_id}/snapshot",
    response_model=InventoryMovementSnapshotResponse,
    summary="Get movement snapshot",
)
@require_capability("logistics.inventory_ledger.read_snapshots")
@require_step_up(StepUpLevel.MEDIUM)
def get_movement_snapshot(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    provider: InventoryMovementSnapshotProvider = Depends(_snapshot_provider),
    _user: User = Depends(get_current_user),
):
    try:
        snapshot = provider.build(organization_id, movement_id)
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementSnapshotResponse(
        movement=InventoryMovementResponse.model_validate(snapshot["movement"]),
        lines=[InventoryMovementLineResponse.model_validate(line) for line in snapshot["lines"]],
        sources=[
            InventoryMovementSourceResponse.model_validate(src) for src in snapshot["sources"]
        ],
        positions=[InventoryPositionResponse.model_validate(pos) for pos in snapshot["positions"]],
        compensation=(
            InventoryMovementResponse.model_validate(snapshot["compensation"])
            if snapshot["compensation"]
            else None
        ),
        captured_at=datetime.fromisoformat(snapshot["captured_at"]),
        content_hash=snapshot["content_hash"],
    )


@router.get(
    "/movements/{movement_id}/history",
    response_model=list[InventoryMovementResponse],
    summary="Get compensation history for a movement",
)
@require_capability("logistics.inventory_ledger.read_history")
def get_movement_history(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    detail = kardex.get_movement_detail(organization_id, movement_id)
    movement = detail["movement"]
    history: list[InventoryMovementModel] = []
    if movement.compensation_for_movement_id is not None:
        history.append(db.get(InventoryMovementModel, movement.compensation_for_movement_id))
    if movement.compensated_by_movement_id is not None:
        history.append(db.get(InventoryMovementModel, movement.compensated_by_movement_id))
    return [InventoryMovementResponse.model_validate(item) for item in history if item is not None]


@router.get(
    "/movements/{movement_id}/integrity",
    response_model=InventoryMovementIntegrityResponse,
    summary="Verify a single movement hash",
)
@require_capability("logistics.inventory_ledger.read_integrity")
def get_movement_integrity(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    integrity: InventoryLedgerIntegrityService = Depends(_integrity_service),
    _user: User = Depends(get_current_user),
):
    movement = db.get(InventoryMovementModel, movement_id)
    if movement is None or movement.organization_id != organization_id:
        raise HTTPException(status_code=404, detail={"code": "INVENTORY_MOVEMENT_NOT_FOUND"})
    return InventoryMovementIntegrityResponse(
        verification_status="OK",
        first_hash=movement.movement_hash,
        last_hash=movement.movement_hash,
        last_sequence=movement.ledger_sequence,
    )


@router.get(
    "/movements/{movement_id}/capabilities",
    response_model=InventoryMovementCapabilities,
    summary="Get capabilities for a movement",
)
@require_capability("logistics.inventory_ledger.read")
def get_movement_capabilities(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    movement = db.get(InventoryMovementModel, movement_id)
    if movement is None or movement.organization_id != organization_id:
        raise HTTPException(status_code=404, detail={"code": "INVENTORY_MOVEMENT_NOT_FOUND"})
    return _capabilities_for_movement(movement)


@router.get(
    "/movements/{movement_id}/compensations",
    response_model=list[InventoryMovementCompensationRequestResponse],
    summary="List compensation requests for a movement",
)
@require_capability("logistics.inventory_ledger.read_history")
def get_movement_compensations(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    from sqlalchemy import select

    records = db.scalars(
        select(InventoryMovementCompensationRequestModel).where(
            InventoryMovementCompensationRequestModel.organization_id == organization_id,
            InventoryMovementCompensationRequestModel.original_movement_id == movement_id,
        )
    ).all()
    return [InventoryMovementCompensationRequestResponse.model_validate(r) for r in records]


# ---------------------------------------------------------------------------
# Posting requests
# ---------------------------------------------------------------------------


@router.post(
    "/ledger/posting-requests",
    response_model=InventoryMovementPostingRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a posting request (idempotent)",
)
@require_capability("logistics.inventory_ledger.validate_prepared_event")
@require_csrf
def create_posting_request(
    organization_id: UUID,
    payload: InventoryMovementPostingRequestCreate,
    db: Session = Depends(get_db),
    posting: InventoryMovementPostingService = Depends(_posting_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = posting.create_posting_request(
            organization_id=organization_id,
            request_key=payload.request_key,
            source_system=payload.source_system,
            source_event_type=payload.source_event_type,
            source_event_id=payload.source_event_id,
            source_event_version=payload.source_event_version,
            payload=payload.payload,
            requested_by_user_id=getattr(_user, "id", None),
            requested_by_service="api",
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementPostingRequestResponse.model_validate(record)


@router.get(
    "/ledger/posting-requests/{request_id}",
    response_model=InventoryMovementPostingRequestResponse,
    summary="Get a posting request",
)
@require_capability("logistics.inventory_ledger.validate_prepared_event")
def get_posting_request(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryMovementPostingRequestModel, request_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(status_code=404, detail={"code": "INVENTORY_POSTING_REQUEST_NOT_FOUND"})
    return InventoryMovementPostingRequestResponse.model_validate(record)


@router.post(
    "/ledger/prepared-events/{source_event_id}/validate",
    response_model=PreparedInventoryEventValidationResponse,
    summary="Validate a prepared event without publishing",
)
@require_capability("logistics.inventory_ledger.validate_prepared_event")
@require_step_up(StepUpLevel.MEDIUM)
def validate_prepared_event(
    organization_id: UUID,
    source_event_id: str,
    source_system: str = Query(...),
    source_event_type: str = Query(...),
    source_event_version: int = Query(1),
    db: Session = Depends(get_db),
    validation_service: InventoryMovementValidationService = Depends(_validation_service),
    _user: User = Depends(get_current_user),
):
    payload = {
        "source_event_id": source_event_id,
        "source_system": source_system,
        "source_event_type": source_event_type,
        "source_event_version": source_event_version,
    }
    result = validation_service.validate(
        organization_id=organization_id,
        source_adapter_name=source_system,
        movement_type=source_event_type,
        payload=payload,
    )
    return PreparedInventoryEventValidationResponse(
        validation_status=result.validation_status,
        blocking_errors=[vars(e) for e in result.blocking_errors],
        warnings=[vars(w) for w in result.warnings],
        movement_type=result.movement_type,
        movement_family=result.movement_family,
        source_hash=result.source_hash,
        payload_hash=result.payload_hash,
        server_time=result.server_time,
        validation_hash=result.validation_hash,
        posting_options=dict(result.posting_options),
    )


@router.post(
    "/ledger/prepared-events/{source_event_id}/post",
    response_model=InventoryMovementResponse,
    summary="Post a prepared event (idempotent)",
)
@require_capability("logistics.inventory_ledger.post_prepared_event")
@require_step_up(StepUpLevel.MEDIUM)
@require_csrf
def post_prepared_event(
    organization_id: UUID,
    payload: Mapping[str, Any],
    source_event_id: str,
    source_system: str = Query(...),
    source_event_type: str = Query(...),
    source_event_version: int = Query(1),
    db: Session = Depends(get_db),
    ingestion: PreparedInventoryEventIngestionService = Depends(_ingestion_service),
    _user: User = Depends(get_current_user),
):
    try:
        result = ingestion.ingest_and_post(
            organization_id=organization_id,
            adapter_name=source_event_type,
            source_system=source_system,
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            source_event_version=source_event_version,
            source_payload=payload,
            actor_user_id=getattr(_user, "id", None),
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    movement = db.get(InventoryMovementModel, result.movement_id)
    return InventoryMovementResponse.model_validate(movement)


@router.post(
    "/ledger/materialize/quality-events",
    response_model=dict,
    summary="Materialize pending Phase 042 quality events",
)
@require_capability("logistics.inventory_ledger.post_quality_events")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def materialize_quality_events(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    from app.modules.logistics.inventory.ledger.infrastructure.jobs.jobs import (
        materialize_quality_events as _run,
    )

    return _run(db, organization_id=organization_id)


@router.post(
    "/ledger/materialize/putaway-events",
    response_model=dict,
    summary="Materialize pending Phase 043 putaway events",
)
@require_capability("logistics.inventory_ledger.post_putaway_events")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def materialize_putaway_events(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    from app.modules.logistics.inventory.ledger.infrastructure.jobs.jobs import (
        materialize_putaway_events as _run,
    )

    return _run(db, organization_id=organization_id)


@router.post(
    "/ledger/retry-failed-posting/{request_id}",
    response_model=InventoryMovementPostingRequestResponse,
    summary="Retry a failed posting",
)
@require_capability("logistics.inventory_ledger.retry_failed_posting")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def retry_failed(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    retry_failed_posting(db, organization_id=organization_id, request_id=request_id)
    record = db.get(InventoryMovementPostingRequestModel, request_id)
    return InventoryMovementPostingRequestResponse.model_validate(record)


# ---------------------------------------------------------------------------
# Compensation
# ---------------------------------------------------------------------------


@router.post(
    "/movements/{movement_id}/compensation-requests",
    response_model=InventoryMovementCompensationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a compensation",
)
@require_capability("logistics.inventory_ledger.request_compensation")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def create_compensation_request(
    organization_id: UUID,
    movement_id: UUID,
    payload: InventoryMovementCompensationRequestCreate,
    db: Session = Depends(get_db),
    service: InventoryMovementCompensationService = Depends(_compensation_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = service.request_compensation(
            organization_id=organization_id,
            original_movement_id=movement_id,
            reason_code=payload.reason_code,
            reason=payload.reason,
            evidence_file_ids=payload.evidence_file_ids,
            requested_by=getattr(_user, "id"),
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementCompensationRequestResponse.model_validate(record)


@router.get(
    "/movement-compensation-requests/{request_id}",
    response_model=InventoryMovementCompensationRequestResponse,
    summary="Get compensation request",
)
@require_capability("logistics.inventory_ledger.request_compensation")
def get_compensation_request(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryMovementCompensationRequestModel, request_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_MOVEMENT_COMPENSATION_REQUEST_NOT_FOUND"}
        )
    return InventoryMovementCompensationRequestResponse.model_validate(record)


@router.post(
    "/movement-compensation-requests/{request_id}/submit",
    response_model=InventoryMovementCompensationRequestResponse,
    summary="Submit compensation request for review",
)
@require_capability("logistics.inventory_ledger.request_compensation")
@require_csrf
def submit_compensation(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    service: InventoryMovementCompensationService = Depends(_compensation_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = service.submit_for_review(
            organization_id=organization_id,
            request_id=request_id,
            actor=getattr(_user, "id"),
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementCompensationRequestResponse.model_validate(record)


@router.post(
    "/movement-compensation-requests/{request_id}/approve",
    response_model=InventoryMovementCompensationRequestResponse,
    summary="Approve compensation request",
)
@require_capability("logistics.inventory_ledger.approve_compensation")
@require_step_up(StepUpLevel.CRITICAL)
@require_csrf
def approve_compensation(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    service: InventoryMovementCompensationService = Depends(_compensation_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = service.approve(
            organization_id=organization_id,
            request_id=request_id,
            approved_by=getattr(_user, "id"),
            risk_level=RiskLevel.CRITICAL.value,
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementCompensationRequestResponse.model_validate(record)


@router.post(
    "/movement-compensation-requests/{request_id}/reject",
    response_model=InventoryMovementCompensationRequestResponse,
    summary="Reject compensation request",
)
@require_capability("logistics.inventory_ledger.review_compensation")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def reject_compensation(
    organization_id: UUID,
    request_id: UUID,
    decision: InventoryMovementCompensationDecisionRequest,
    db: Session = Depends(get_db),
    service: InventoryMovementCompensationService = Depends(_compensation_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = service.reject(
            organization_id=organization_id,
            request_id=request_id,
            rejected_by=getattr(_user, "id"),
            rejection_reason=decision.rejection_reason or "REJECTED",
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementCompensationRequestResponse.model_validate(record)


@router.post(
    "/movement-compensation-requests/{request_id}/execute",
    response_model=InventoryMovementResponse,
    summary="Execute an approved compensation",
)
@require_capability("logistics.inventory_ledger.execute_compensation")
@require_step_up(StepUpLevel.CRITICAL)
@require_csrf
def execute_compensation(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    service: InventoryMovementCompensationService = Depends(_compensation_service),
    _user: User = Depends(get_current_user),
):
    try:
        result = service.execute(
            organization_id=organization_id,
            request_id=request_id,
            actor=getattr(_user, "id"),
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    movement = db.get(InventoryMovementModel, result.resulting_movement_id)
    return InventoryMovementResponse.model_validate(movement)


@router.post(
    "/movement-compensation-requests/{request_id}/cancel",
    response_model=InventoryMovementCompensationRequestResponse,
    summary="Cancel compensation request",
)
@require_capability("logistics.inventory_ledger.request_compensation")
@require_csrf
def cancel_compensation(
    organization_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    service: InventoryMovementCompensationService = Depends(_compensation_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = service.cancel(
            organization_id=organization_id,
            request_id=request_id,
            cancelled_by=getattr(_user, "id"),
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryMovementCompensationRequestResponse.model_validate(record)


# ---------------------------------------------------------------------------
# Kardex
# ---------------------------------------------------------------------------


@router.get(
    "/kardex",
    response_model=InventoryKardexResponse,
    summary="Kardex technical query",
)
@require_capability("logistics.inventory_kardex.read")
def kardex(
    organization_id: UUID,
    flt: InventoryKardexQuery = Depends(),
    db: Session = Depends(get_db),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    kardex_filter = KardexFilter(
        organization_id=organization_id,
        search=flt.search,
        movement_code=flt.movement_code,
        ledger_sequence_from=flt.ledger_sequence_from,
        ledger_sequence_to=flt.ledger_sequence_to,
        movement_family=flt.movement_family,
        movement_type=flt.movement_type,
        status=flt.status,
        branch_id=flt.branch_id,
        warehouse_id=flt.warehouse_id,
        location_id=flt.location_id,
        product_id=flt.product_id,
        product_version_id=flt.product_version_id,
        sku=flt.sku,
        source_system=flt.source_system,
        source_event_type=flt.source_event_type,
        source_event_id=flt.source_event_id,
        source_document_type=flt.source_document_type,
        source_document_code=flt.source_document_code,
        availability_state_from=flt.availability_state_from,
        availability_state_to=flt.availability_state_to,
        quality_state_from=flt.quality_state_from,
        quality_state_to=flt.quality_state_to,
        transit_state_from=flt.transit_state_from,
        transit_state_to=flt.transit_state_to,
        damage_state_from=flt.damage_state_from,
        damage_state_to=flt.damage_state_to,
        expiration_state_from=flt.expiration_state_from,
        expiration_state_to=flt.expiration_state_to,
        compensated=flt.compensated,
        integrity_status=flt.integrity_status,
        occurred_from=flt.occurred_from,
        occurred_to=flt.occurred_to,
        posted_from=flt.posted_from,
        posted_to=flt.posted_to,
        posted_by=flt.posted_by,
        correlation_id=flt.correlation_id,
        page=flt.page,
        page_size=flt.page_size,
        sort_by=flt.sort_by,
        sort_direction=flt.sort_direction,
    )
    rows, total = kardex.list_movements(kardex_filter)
    return InventoryKardexResponse(
        items=[InventoryKardexRow.model_validate(row) for row in rows],
        total=total,
        page=flt.page,
        page_size=flt.page_size,
        filters=flt.model_dump(exclude_none=True),
    )


@router.get(
    "/kardex/technical-running-quantity",
    response_model=list[InventoryKardexRunningQuantityRow],
    summary="Technical running quantity (requires exact scope)",
)
@require_capability("logistics.inventory_kardex.read_running_quantity")
def kardex_running_quantity(
    organization_id: UUID,
    warehouse_id: UUID,
    product_id: UUID,
    base_unit_id: UUID,
    position_id: UUID | None = None,
    availability_states: list[str] | None = Query(default=None),
    quality_states: list[str] | None = Query(default=None),
    transit_states: list[str] | None = Query(default=None),
    damage_states: list[str] | None = Query(default=None),
    expiration_states: list[str] | None = Query(default=None),
    sequence_from: int | None = None,
    sequence_to: int | None = None,
    opening_quantity_reference: Decimal = Decimal("0"),
    db: Session = Depends(get_db),
    kardex: InventoryKardexQueryService = Depends(_kardex_service),
    _user: User = Depends(get_current_user),
):
    try:
        results = kardex.compute_technical_running_quantity(
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            base_unit_id=base_unit_id,
            position_id=position_id,
            availability_states=availability_states,
            quality_states=quality_states,
            transit_states=transit_states,
            damage_states=damage_states,
            expiration_states=expiration_states,
            sequence_from=sequence_from,
            sequence_to=sequence_to,
            opening_quantity_reference=opening_quantity_reference,
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return [InventoryKardexRunningQuantityRow.model_validate(r) for r in results]


@router.get(
    "/kardex/movement-types",
    response_model=list[str],
    summary="List enabled movement types",
)
@require_capability("logistics.inventory_kardex.read")
def kardex_movement_types(
    _user: User = Depends(get_current_user),
):
    from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
        list_supported_movement_types,
    )

    return list(list_supported_movement_types())


@router.get(
    "/kardex/source-types",
    response_model=list[str],
    summary="List enabled source adapter names",
)
@require_capability("logistics.inventory_kardex.read")
def kardex_source_types(
    _user: User = Depends(get_current_user),
):
    from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
        list_enabled_adapters,
    )

    return list(list_enabled_adapters())


@router.get(
    "/kardex/state-transitions",
    response_model=list[dict],
    summary="List legal state transitions",
)
@require_capability("logistics.inventory_kardex.read")
def kardex_state_transitions(
    _user: User = Depends(get_current_user),
):
    from app.modules.logistics.inventory.ledger.domain.policies.state_transition_policy import (
        LEGAL_STATE_TRANSITIONS,
    )

    return [vars(t) for t in LEGAL_STATE_TRANSITIONS]


@router.post(
    "/kardex/exports",
    response_model=InventoryKardexExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Queue a kardex export",
)
@require_capability("logistics.inventory_kardex.export")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def create_kardex_export(
    organization_id: UUID,
    payload: InventoryKardexExportCreate,
    db: Session = Depends(get_db),
    service: InventoryLedgerExportService = Depends(_export_service),
    _user: User = Depends(get_current_user),
):
    try:
        record = service.create(
            organization_id=organization_id,
            requested_by_user_id=getattr(_user, "id"),
            filters=payload.filters.model_dump(exclude_none=True),
            export_format=payload.format,
            timezone_name=payload.timezone,
        )
        run_export_job(db, organization_id=organization_id, job_id=record.id)
        db.refresh(record)
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryKardexExportResponse.model_validate(record)


@router.get(
    "/kardex/exports/{export_id}",
    response_model=InventoryKardexExportResponse,
    summary="Get kardex export job",
)
@require_capability("logistics.inventory_kardex.export")
def get_kardex_export(
    organization_id: UUID,
    export_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryKardexExportJobModel, export_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(status_code=404, detail={"code": "INVENTORY_MOVEMENT_EXPORT_NOT_FOUND"})
    return InventoryKardexExportResponse.model_validate(record)


@router.get(
    "/kardex/exports/{export_id}/download",
    summary="Download kardex export artifact",
)
@require_capability("logistics.inventory_kardex.export")
@require_step_up(StepUpLevel.HIGH)
def download_kardex_export(
    organization_id: UUID,
    export_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryKardexExportJobModel, export_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(status_code=404, detail={"code": "INVENTORY_MOVEMENT_EXPORT_NOT_FOUND"})
    if record.file_path is None or not record.file_path:
        raise HTTPException(status_code=409, detail={"code": "INVENTORY_MOVEMENT_EXPORT_NOT_READY"})
    from fastapi.responses import FileResponse

    record.downloaded_at = datetime.now(timezone.utc)
    db.flush()
    return FileResponse(record.file_path, filename=f"{record.id}.{record.format.lower()}")


# ---------------------------------------------------------------------------
# Partitions / integrity / reconciliation
# ---------------------------------------------------------------------------


@router.get(
    "/ledger/partitions",
    response_model=list[InventoryLedgerPartitionResponse],
    summary="List partitions",
)
@require_capability("logistics.inventory_ledger.read")
def list_partitions(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    from sqlalchemy import select

    records = db.scalars(
        select(InventoryLedgerPartitionModel).where(
            InventoryLedgerPartitionModel.organization_id == organization_id
        )
    ).all()
    return [InventoryLedgerPartitionResponse.model_validate(r) for r in records]


@router.get(
    "/ledger/partitions/{partition_id}",
    response_model=InventoryLedgerPartitionResponse,
    summary="Get a partition",
)
@require_capability("logistics.inventory_ledger.read")
def get_partition(
    organization_id: UUID,
    partition_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryLedgerPartitionModel, partition_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_LEDGER_PARTITION_NOT_FOUND"}
        )
    return InventoryLedgerPartitionResponse.model_validate(record)


@router.get(
    "/ledger/partitions/{partition_id}/integrity",
    response_model=InventoryLedgerVerificationResponse,
    summary="Verify partition integrity",
)
@require_capability("logistics.inventory_ledger.verify")
def get_partition_integrity(
    organization_id: UUID,
    partition_id: UUID,
    db: Session = Depends(get_db),
    integrity: InventoryLedgerIntegrityService = Depends(_integrity_service),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryLedgerPartitionModel, partition_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_LEDGER_PARTITION_NOT_FOUND"}
        )
    result = integrity.verify_partition(
        organization_id=organization_id,
        ledger_partition_key=record.partition_key,
    )
    return InventoryLedgerVerificationResponse.model_validate(result)


@router.post(
    "/ledger/partitions/{partition_id}/verify",
    response_model=InventoryLedgerVerificationResponse,
    summary="Verify partition integrity (synchronous)",
)
@require_capability("logistics.inventory_ledger.verify")
@require_step_up(StepUpLevel.MEDIUM)
def verify_partition(
    organization_id: UUID,
    partition_id: UUID,
    db: Session = Depends(get_db),
    integrity: InventoryLedgerIntegrityService = Depends(_integrity_service),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryLedgerPartitionModel, partition_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_LEDGER_PARTITION_NOT_FOUND"}
        )
    return InventoryLedgerVerificationResponse.model_validate(
        integrity.verify_partition(
            organization_id=organization_id,
            ledger_partition_key=record.partition_key,
        )
    )


@router.post(
    "/ledger/partitions/{partition_id}/checkpoints",
    response_model=InventoryLedgerCheckpointResponse,
    summary="Create a ledger checkpoint",
)
@require_capability("logistics.inventory_ledger.create_checkpoint")
@require_step_up(StepUpLevel.MEDIUM)
@require_csrf
def create_checkpoint(
    organization_id: UUID,
    partition_id: UUID,
    from_sequence: int,
    to_sequence: int,
    db: Session = Depends(get_db),
    service: InventoryLedgerCheckpointService = Depends(_checkpoint_service),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryLedgerPartitionModel, partition_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_LEDGER_PARTITION_NOT_FOUND"}
        )
    try:
        checkpoint = service.create(
            organization_id=organization_id,
            ledger_partition_key=record.partition_key,
            from_sequence=from_sequence,
            to_sequence=to_sequence,
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryLedgerCheckpointResponse.model_validate(checkpoint)


@router.get(
    "/ledger/checkpoints/{checkpoint_id}",
    response_model=InventoryLedgerCheckpointResponse,
    summary="Get a checkpoint",
)
@require_capability("logistics.inventory_ledger.read")
def get_checkpoint(
    organization_id: UUID,
    checkpoint_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryLedgerCheckpointModel, checkpoint_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_MOVEMENT_CHECKPOINT_NOT_FOUND"}
        )
    return InventoryLedgerCheckpointResponse.model_validate(record)


@router.post(
    "/ledger/reconciliation-jobs",
    response_model=InventoryLedgerReconciliationJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run a reconciliation job",
)
@require_capability("logistics.inventory_ledger.reconcile")
@require_step_up(StepUpLevel.HIGH)
@require_csrf
def create_reconciliation(
    organization_id: UUID,
    payload: InventoryLedgerReconciliationJobCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        job = run_reconciliation(
            db,
            organization_id=organization_id,
            scope=payload.scope,
            requested_by_user_id=getattr(_user, "id", None),
        )
    except InventoryLedgerError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        )
    return InventoryLedgerReconciliationJobResponse.model_validate(job)


@router.get(
    "/ledger/reconciliation-jobs/{job_id}",
    response_model=InventoryLedgerReconciliationJobResponse,
    summary="Get a reconciliation job",
)
@require_capability("logistics.inventory_ledger.reconcile")
def get_reconciliation(
    organization_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(InventoryLedgerReconciliationJobModel, job_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail={"code": "INVENTORY_MOVEMENT_RECONCILIATION_JOB_NOT_FOUND"}
        )
    return InventoryLedgerReconciliationJobResponse.model_validate(record)


@router.get(
    "/ledger/reconciliation-jobs/{job_id}/results",
    response_model=list[InventoryLedgerReconciliationResult],
    summary="Get reconciliation results",
)
@require_capability("logistics.inventory_ledger.reconcile")
def get_reconciliation_results(
    organization_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    records = db.scalars(
        __import__("sqlalchemy")
        .select(InventoryLedgerReconciliationResultModel)
        .where(InventoryLedgerReconciliationResultModel.job_id == job_id)
    ).all()
    return [InventoryLedgerReconciliationResult.model_validate(r) for r in records]


# ---------------------------------------------------------------------------
# Future-phase preparation
# ---------------------------------------------------------------------------


@router.get(
    "/movements/{movement_id}/balance-preparation",
    response_model=list[InventoryBalancePreparationResponse],
    summary="Get Phase 045 balance preparation for a movement",
)
@require_capability("logistics.inventory_ledger.read_balance_preparation")
def balance_preparation(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    service: InventoryBalancePreparationService = Depends(_balance_service),
    _user: User = Depends(get_current_user),
):
    entries = service.for_movement(organization_id, movement_id)
    return [InventoryBalancePreparationResponse.model_validate(e) for e in entries]


@router.get(
    "/movements/{movement_id}/traceability-preparation",
    response_model=list[InventoryTraceabilityPreparationResponse],
    summary="Get Phase 046 traceability preparation for a movement",
)
@require_capability("logistics.inventory_ledger.read_traceability_preparation")
def traceability_preparation(
    organization_id: UUID,
    movement_id: UUID,
    db: Session = Depends(get_db),
    service: InventoryTraceabilityPreparationService = Depends(_traceability_service),
    _user: User = Depends(get_current_user),
):
    entries = service.for_movement(organization_id, movement_id)
    return [InventoryTraceabilityPreparationResponse.model_validate(e) for e in entries]


@router.get(
    "/ledger/balance-preparation",
    response_model=list[InventoryBalancePreparationResponse],
    summary="Get Phase 045 balance preparation for the ledger",
)
@require_capability("logistics.inventory_ledger.read_balance_preparation")
def balance_preparation_ledger(
    organization_id: UUID,
    warehouse_id: UUID | None = None,
    product_id: UUID | None = None,
    db: Session = Depends(get_db),
    service: InventoryBalancePreparationService = Depends(_balance_service),
    _user: User = Depends(get_current_user),
):
    entries = service.for_ledger(
        organization_id=organization_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    return [InventoryBalancePreparationResponse.model_validate(e) for e in entries]


@router.get(
    "/ledger/traceability-preparation",
    response_model=list[InventoryTraceabilityPreparationResponse],
    summary="Get Phase 046 traceability preparation for the ledger",
)
@require_capability("logistics.inventory_ledger.read_traceability_preparation")
def traceability_preparation_ledger(
    organization_id: UUID,
    warehouse_id: UUID | None = None,
    product_id: UUID | None = None,
    db: Session = Depends(get_db),
    service: InventoryTraceabilityPreparationService = Depends(_traceability_service),
    _user: User = Depends(get_current_user),
):
    entries = service.for_ledger(
        organization_id=organization_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    return [InventoryTraceabilityPreparationResponse.model_validate(e) for e in entries]
