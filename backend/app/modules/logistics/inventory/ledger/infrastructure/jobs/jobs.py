"""Persistent jobs for the inventory ledger.

These jobs are designed to be invoked by the project's existing job
runner. They are stateless w.r.t. timers; the runner is responsible
for scheduling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.application.services.integrity_service import (
    InventoryLedgerCheckpointService,
    InventoryLedgerExportService,
    InventoryLedgerReconciliationService,
)
from app.modules.logistics.inventory.ledger.application.services.posting_service import (
    InventoryMovementPostingService,
)
from app.modules.logistics.inventory.ledger.application.services.preparation_services import (
    InventoryBalancePreparationService,
    InventoryTraceabilityPreparationService,
)
from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
    SourceBackedAvailabilityProvider,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    PostingRequestStatus,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryKardexExportJobModel,
    InventoryLedgerOutboxEventModel,
    InventoryMovementModel,
    InventoryMovementPostingRequestModel,
    InventoryMovementSourceReferenceModel,
)
from app.modules.logistics.inventory.ledger.infrastructure.source_adapters.adapters import (
    build_default_registry,
)

# ---------------------------------------------------------------------------
# Ingest Phase 042 quality events
# ---------------------------------------------------------------------------


def ingest_quality_events(
    db: Session,
    *,
    organization_id: UUID,
    actor_user_id: UUID | None = None,
) -> dict[str, int]:
    """Materialize pending Phase 042 quality events into MOV.

    The job scans the Phase 042 disposition events that have not yet
    been materialized into the ledger (detected by absence of a source
    reference pointing to the disposition event) and submits them
    through the corresponding adapter.
    """

    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import (
        QualityDispositionEventModel,
    )

    events = db.scalars(
        select(QualityDispositionEventModel).where(
            QualityDispositionEventModel.organization_id == organization_id
        )
    ).all()
    availability = SourceBackedAvailabilityProvider(db)
    from app.modules.logistics.inventory.ledger.application.services.validation_service import (
        InventoryMovementValidationService,
    )

    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(db, validation_service=validation)

    processed = 0
    skipped = 0
    failed = 0
    for event in events:
        existing = db.scalars(
            select(InventoryMovementSourceReferenceModel).where(
                InventoryMovementSourceReferenceModel.source_event_id == str(event.id)
            )
        ).first()
        if existing is not None:
            skipped += 1
            continue
        adapter = _pick_quality_adapter(event.event_type)
        if adapter is None:
            skipped += 1
            continue
        try:
            prepared = adapter.build(
                organization_id=organization_id,
                payload=_quality_payload(db, event),
            )
            record = posting.create_posting_request(
                organization_id=organization_id,
                request_key=str(event.id),
                source_system="QUALITY",
                source_event_type=prepared.movement_type,
                source_event_id=str(event.id),
                source_event_version=1,
                payload=prepared.lines[0]
                | {
                    "movement_type": prepared.movement_type,
                    "movement_family": prepared.movement_family,
                    "source_adapter_name": adapter.adapter_name,
                    "occurred_at": event.event_at,
                    "branch_id": str(_branch_id(db, event)),
                    "warehouse_id": str(event.warehouse_id),
                    "source_hash": event.event_hash,
                    "payload_hash": prepared.payload_hash,
                    "source_references": [
                        {
                            "source_system": "QUALITY",
                            "source_event_type": adapter.adapter_name,
                            "source_event_id": str(event.id),
                            "source_event_version": 1,
                            "source_entity_type": "QualityDispositionEvent",
                            "source_entity_id": str(event.id),
                            "source_hash": event.event_hash,
                            "source_occurred_at": event.event_at.isoformat(),
                        }
                    ],
                    "lines": prepared.lines,
                },
            )
            posting.post(
                organization_id=organization_id,
                posting_request_id=record.id,
                actor_user_id=actor_user_id,
                actor_service="inventory-ledger-quality-job",
            )
            processed += 1
        except Exception:  # noqa: BLE001
            failed += 1
    return {"processed": processed, "skipped": skipped, "failed": failed}


def _pick_quality_adapter(event_type: str):
    registry = build_default_registry()
    mapping = {
        "QUARANTINE_REQUIRED": registry["QUALITY_QUARANTINE_APPLIED"],
        "QUARANTINE_OPENED": registry["QUALITY_QUARANTINE_APPLIED"],
        "RELEASE_EXECUTED": registry["QUARANTINE_RELEASED"],
        "PARTIAL_RELEASE_EXECUTED": registry["QUARANTINE_RELEASED"],
        "REJECTION_EXECUTED": registry["QUALITY_REJECTED"],
        "PARTIAL_REJECTION_EXECUTED": registry["QUALITY_REJECTED"],
        "ALLOCATION_SPLIT": registry["DISPOSITION_SPLIT"],
    }
    return mapping.get(event_type)


def _quality_payload(db: Session, event) -> Mapping[str, Any]:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import (
        InboundInventoryDispositionAllocationModel,
    )

    allocation = db.get(InboundInventoryDispositionAllocationModel, event.allocation_id)
    if allocation is None:
        raise ValueError(f"Quality allocation {event.allocation_id} was not found.")
    source_position_id, destination_position_id = _quality_positions(db, event, allocation)
    return {
        "source_event_id": str(event.id),
        "source_event_version": 1,
        "source_hash": event.event_hash,
        "source_occurred_at": event.event_at,
        "source_entity_type": "QualityDispositionEvent",
        "source_entity_id": str(event.id),
        "occurred_at": event.event_at,
        "product_id": str(allocation.product_id),
        "product_version_id": (
            str(allocation.product_version_id) if allocation.product_version_id else None
        ),
        "product_snapshot": {
            "sku": allocation.sku_snapshot,
            "name": allocation.product_name_snapshot,
        },
        "quantity": str(event.quantity or allocation.quantity),
        "base_quantity": str(event.base_quantity or allocation.base_quantity),
        "unit_id": str(event.unit_id or allocation.unit_id),
        "base_unit_id": str(allocation.unit_id),
        "source_position_id": str(source_position_id),
        "destination_position_id": str(destination_position_id),
    }


def _branch_id(db: Session, event) -> UUID:
    from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import (
        QualityQuarantineCaseModel,
    )

    case = db.get(QualityQuarantineCaseModel, event.quarantine_case_id)
    if case is None:
        raise ValueError(f"Quarantine case {event.quarantine_case_id} was not found.")
    return case.branch_id


def _quality_positions(db: Session, event, allocation) -> tuple[UUID, UUID]:
    from app.modules.logistics.inventory.ledger.domain.services.position_service import (
        InventoryPositionService,
        PositionDimension,
    )
    from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
        AvailabilityState,
        BoundaryType,
        DamageState,
        ExpirationState,
        QualityState,
        TransitState,
    )

    state_map = {
        "QUARANTINE": QualityState.QUARANTINE,
        "APPROVED": QualityState.APPROVED,
        "RELEASED": QualityState.APPROVED,
        "REJECTED": QualityState.REJECTED,
        "NOT_ASSESSED": QualityState.NOT_ASSESSED,
    }

    def quality_state(raw: str | None) -> QualityState:
        upper = str(raw or "UNKNOWN").upper()
        return next(
            (value for key, value in state_map.items() if key in upper), QualityState.UNKNOWN
        )

    service = InventoryPositionService(db)

    def resolve(raw_state: str | None):
        quality = quality_state(raw_state)
        quarantined = quality == QualityState.QUARANTINE
        return service.resolve(
            PositionDimension(
                organization_id=allocation.organization_id,
                branch_id=allocation.branch_id,
                warehouse_id=allocation.warehouse_id,
                warehouse_location_id=(
                    allocation.physical_quarantine_location_id if quarantined else None
                ),
                boundary_type=(
                    BoundaryType.INTERNAL_QUARANTINE
                    if quarantined
                    else BoundaryType.INTERNAL_STAGING
                ),
                product_id=allocation.product_id,
                product_version_id=allocation.product_version_id,
                ownership_type="OWNED",
                owner_business_partner_id=None,
                availability_state=(
                    AvailabilityState.BLOCKED
                    if quarantined or quality == QualityState.REJECTED
                    else AvailabilityState.PENDING_PUTAWAY
                ),
                quality_state=quality,
                transit_state=TransitState.INBOUND_STAGING,
                damage_state=DamageState.NORMAL,
                expiration_state=ExpirationState.UNKNOWN,
            )
        )

    source = resolve(event.previous_status or allocation.quality_status)
    destination = resolve(event.new_status or allocation.quality_status)
    if source.id == destination.id:
        raise ValueError("Quality event does not describe a position-state transition.")
    return source.id, destination.id


# ---------------------------------------------------------------------------
# Ingest Phase 043 putaway placements
# ---------------------------------------------------------------------------


def ingest_putaway_events(
    db: Session,
    *,
    organization_id: UUID,
    actor_user_id: UUID | None = None,
) -> dict[str, int]:
    from app.modules.logistics.inventory.putaway.infrastructure.persistence.models import (
        OperationalInventoryPlacementModel,
    )

    placements = db.scalars(
        select(OperationalInventoryPlacementModel).where(
            OperationalInventoryPlacementModel.organization_id == organization_id
        )
    ).all()
    registry = build_default_registry()
    adapter = registry["PUTAWAY_COMPLETED"]
    availability = SourceBackedAvailabilityProvider(db)
    from app.modules.logistics.inventory.ledger.application.services.validation_service import (
        InventoryMovementValidationService,
    )

    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(db, validation_service=validation)

    processed = 0
    skipped = 0
    failed = 0
    for placement in placements:
        existing = db.scalars(
            select(InventoryMovementSourceReferenceModel).where(
                InventoryMovementSourceReferenceModel.source_event_id == str(placement.id)
            )
        ).first()
        if existing is not None:
            skipped += 1
            continue
        try:
            source_position_id, destination_position_id, branch_id = _putaway_positions(
                db, placement
            )
            payload = {
                "movement_type": "PUTAWAY_COMPLETED",
                "movement_family": "INBOUND",
                "source_adapter_name": adapter.adapter_name,
                "branch_id": str(branch_id),
                "warehouse_id": str(placement.warehouse_id),
                "source_hash": placement.content_hash or "",
                "payload_hash": placement.content_hash or "",
                "occurred_at": placement.placed_at,
                "source_event_id": str(placement.id),
                "source_event_version": 1,
                "source_references": [
                    {
                        "source_system": "PUTAWAY",
                        "source_event_type": "PUTAWAY_COMPLETED",
                        "source_event_id": str(placement.id),
                        "source_event_version": 1,
                        "source_entity_type": "OperationalInventoryPlacement",
                        "source_entity_id": str(placement.id),
                        "source_hash": placement.content_hash or "",
                        "source_occurred_at": placement.placed_at.isoformat(),
                    }
                ],
                "destinations": [
                    {
                        "product_id": str(placement.product_id),
                        "product_version_id": str(placement.product_version_id)
                        if placement.product_version_id
                        else None,
                        "quantity": str(placement.quantity),
                        "unit_id": str(placement.unit_id),
                        "base_quantity": str(placement.base_quantity),
                        "base_unit_id": str(placement.unit_id),
                        "source_position_id": str(source_position_id),
                        "destination_position_id": str(destination_position_id),
                    }
                ],
                "lines": [
                    {
                        "line_number": 1,
                        "product_id": str(placement.product_id),
                        "product_version_id": str(placement.product_version_id)
                        if placement.product_version_id
                        else None,
                        "quantity": str(placement.quantity),
                        "unit_id": str(placement.unit_id),
                        "base_quantity": str(placement.base_quantity),
                        "base_unit_id": str(placement.unit_id),
                        "source_position_id": str(source_position_id),
                        "destination_position_id": str(destination_position_id),
                        "quantity_direction": "TRANSFER",
                    }
                ],
            }
            record = posting.create_posting_request(
                organization_id=organization_id,
                request_key=str(placement.id),
                source_system="PUTAWAY",
                source_event_type="PUTAWAY_COMPLETED",
                source_event_id=str(placement.id),
                source_event_version=1,
                payload=payload,
            )
            posting.post(
                organization_id=organization_id,
                posting_request_id=record.id,
                actor_user_id=actor_user_id,
                actor_service="inventory-ledger-putaway-job",
            )
            processed += 1
        except Exception:  # noqa: BLE001
            failed += 1
    return {"processed": processed, "skipped": skipped, "failed": failed}


def _putaway_positions(db: Session, placement) -> tuple[UUID, UUID, UUID]:
    from app.models.warehouse import Warehouse
    from app.modules.logistics.inventory.ledger.domain.services.position_service import (
        InventoryPositionService,
        PositionDimension,
    )
    from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
        AvailabilityState,
        BoundaryType,
        DamageState,
        ExpirationState,
        QualityState,
        TransitState,
    )

    warehouse = db.get(Warehouse, placement.warehouse_id)
    if warehouse is None or warehouse.branch_id is None:
        raise ValueError(f"Warehouse {placement.warehouse_id} has no branch scope.")
    service = InventoryPositionService(db)
    common = {
        "organization_id": placement.organization_id,
        "branch_id": warehouse.branch_id,
        "warehouse_id": placement.warehouse_id,
        "product_id": placement.product_id,
        "product_version_id": placement.product_version_id,
        "ownership_type": "OWNED",
        "owner_business_partner_id": None,
        "quality_state": QualityState.APPROVED,
        "damage_state": DamageState.NORMAL,
        "expiration_state": ExpirationState.UNKNOWN,
    }
    source = service.resolve(
        PositionDimension(
            **common,
            warehouse_location_id=None,
            boundary_type=BoundaryType.INTERNAL_STAGING,
            availability_state=AvailabilityState.PENDING_PUTAWAY,
            transit_state=TransitState.INBOUND_STAGING,
        )
    )
    destination = service.resolve(
        PositionDimension(
            **common,
            warehouse_location_id=placement.location_id,
            boundary_type=BoundaryType.INTERNAL_LOCATION,
            availability_state=AvailabilityState.AVAILABLE,
            transit_state=TransitState.NOT_IN_TRANSIT,
        )
    )
    return source.id, destination.id, warehouse.branch_id


# ---------------------------------------------------------------------------
# Periodic ledger maintenance
# ---------------------------------------------------------------------------


def detect_missing_movements(db: Session, *, organization_id: UUID) -> list[str]:
    """Return ids of source events that have not yet produced a movement.

    The detection is best-effort: only references belonging to the
    organization are considered. The intent is to surface events that
    have a posting request but no movement yet.
    """

    rows = db.execute(
        select(InventoryMovementPostingRequestModel.source_event_id).where(
            InventoryMovementPostingRequestModel.organization_id == organization_id,
            InventoryMovementPostingRequestModel.resulting_movement_id.is_(None),
            InventoryMovementPostingRequestModel.status != PostingRequestStatus.DUPLICATE.value,
        )
    ).all()
    return sorted({str(row[0]) for row in rows})


def process_outbox(db: Session, *, organization_id: UUID, batch: int = 100) -> int:
    """Mark pending outbox events as published.

    In production the actual delivery is performed by the project's
    transport layer. This job exists to mark ``PENDING`` events and is
    idempotent.
    """

    pending = db.scalars(
        select(InventoryLedgerOutboxEventModel)
        .where(
            InventoryLedgerOutboxEventModel.organization_id == organization_id,
            InventoryLedgerOutboxEventModel.status == "PENDING",
        )
        .order_by(InventoryLedgerOutboxEventModel.created_at.asc())
        .limit(batch)
    ).all()
    now = datetime.now(timezone.utc)
    for event in pending:
        event.status = "PUBLISHED"
        event.published_at = now
        event.attempts += 1
    db.flush()
    return len(pending)


def verify_chain(db: Session, *, organization_id: UUID, ledger_partition_key: str) -> dict:
    from app.modules.logistics.inventory.ledger.application.services.integrity_service import (
        InventoryLedgerIntegrityService,
    )

    return InventoryLedgerIntegrityService(db).verify_partition(
        organization_id=organization_id,
        ledger_partition_key=ledger_partition_key,
    )


def create_checkpoint(
    db: Session,
    *,
    organization_id: UUID,
    ledger_partition_key: str,
    from_sequence: int,
    to_sequence: int,
):
    return InventoryLedgerCheckpointService(db).create(
        organization_id=organization_id,
        ledger_partition_key=ledger_partition_key,
        from_sequence=from_sequence,
        to_sequence=to_sequence,
    )


def run_reconciliation(
    db: Session,
    *,
    organization_id: UUID,
    scope: Mapping[str, Any] | None = None,
    requested_by_user_id: UUID | None = None,
):
    return InventoryLedgerReconciliationService(db).run(
        organization_id=organization_id,
        scope=scope or {},
        requested_by_user_id=requested_by_user_id,
    )


def prepare_balance_and_traceability(db: Session, *, organization_id: UUID) -> dict[str, int]:
    balance = InventoryBalancePreparationService(db)
    traceability = InventoryTraceabilityPreparationService(db)
    balance_entries = balance.for_ledger(organization_id=organization_id)
    trace_entries = traceability.for_ledger(organization_id=organization_id)
    return {
        "balance_entries": len(balance_entries),
        "traceability_entries": len(trace_entries),
    }


def process_pending_posting_requests(db: Session, *, organization_id: UUID, batch: int = 50) -> int:
    pending = db.scalars(
        select(InventoryMovementPostingRequestModel)
        .where(
            InventoryMovementPostingRequestModel.organization_id == organization_id,
            InventoryMovementPostingRequestModel.status.in_(
                [
                    PostingRequestStatus.RECEIVED.value,
                    PostingRequestStatus.VALID.value,
                    PostingRequestStatus.VALIDATING.value,
                ]
            ),
        )
        .order_by(InventoryMovementPostingRequestModel.requested_at.asc())
        .limit(batch)
    ).all()
    availability = SourceBackedAvailabilityProvider(db)
    from app.modules.logistics.inventory.ledger.application.services.validation_service import (
        InventoryMovementValidationService,
    )

    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(db, validation_service=validation)
    processed = 0
    for request in pending:
        try:
            posting.post(
                organization_id=organization_id,
                posting_request_id=request.id,
            )
            processed += 1
        except Exception:  # noqa: BLE001
            continue
    return processed


def retry_failed_posting(db: Session, *, organization_id: UUID, request_id: UUID) -> int:
    record = db.get(InventoryMovementPostingRequestModel, request_id)
    if record is None or record.organization_id != organization_id:
        return 0
    if record.status != PostingRequestStatus.FAILED.value:
        return 0
    record.status = PostingRequestStatus.RECEIVED.value
    record.failure_code = None
    record.failure_detail_safe = None
    record.completed_at = None
    db.flush()
    availability = SourceBackedAvailabilityProvider(db)
    from app.modules.logistics.inventory.ledger.application.services.validation_service import (
        InventoryMovementValidationService,
    )

    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(db, validation_service=validation)
    try:
        posting.post(organization_id=organization_id, posting_request_id=record.id)
        return 1
    except Exception:  # noqa: BLE001
        return 0


def materialize_quality_events(db: Session, *, organization_id: UUID):
    return ingest_quality_events(db, organization_id=organization_id)


def materialize_putaway_events(db: Session, *, organization_id: UUID):
    return ingest_putaway_events(db, organization_id=organization_id)


def run_export_job(db: Session, *, organization_id: UUID, job_id: UUID) -> int:
    job = db.get(InventoryKardexExportJobModel, job_id)
    if job is None or job.organization_id != organization_id:
        return 0
    if job.status != "QUEUED":
        return 0
    InventoryLedgerExportService(db).materialize(job)
    return 1


def detect_duplicate_posting_requests(db: Session, *, organization_id: UUID) -> list[UUID]:
    """Return ids of duplicate posting requests (status DUPLICATE) that need cleanup."""

    return [
        row[0]
        for row in db.execute(
            select(InventoryMovementPostingRequestModel.id).where(
                InventoryMovementPostingRequestModel.organization_id == organization_id,
                InventoryMovementPostingRequestModel.status == PostingRequestStatus.DUPLICATE.value,
            )
        ).all()
    ]


def detect_sequence_gaps(
    db: Session, *, organization_id: UUID, ledger_partition_key: str
) -> list[int]:
    movements = db.scalars(
        select(InventoryMovementModel)
        .where(
            InventoryMovementModel.organization_id == organization_id,
            InventoryMovementModel.ledger_partition_key == ledger_partition_key,
        )
        .order_by(InventoryMovementModel.ledger_sequence.asc())
    ).all()
    gaps: list[int] = []
    last = 0
    for movement in movements:
        if movement.ledger_sequence != last + 1 and last != 0:
            gaps.append(last + 1)
        last = movement.ledger_sequence
    return gaps
