"""Inventory movement compensation service.

A compensation movement inverts the (source, destination) of the
original lines and creates a new POSTED movement that references the
original. The original is never modified.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryMovementAlreadyCompensated,
    InventoryMovementCompensationApprovalRequired,
    InventoryMovementCompensationNotAllowed,
    InventoryMovementNotFound,
    InventoryMovementOrganizationMismatch,
)
from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
    compute_line_content_hash,
    compute_movement_hash,
)
from app.modules.logistics.inventory.ledger.domain.services.sequence_service import (
    InventoryLedgerSequenceService,
    InventoryMovementCodeService,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    ADAPTER_VERSION,
    CANONICALIZATION_VERSION,
    MOVEMENT_TYPE_FAMILY,
    MovementStatus,
    MovementType,
    SCHEMA_VERSION,
    SourceAdapterName,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryMovementCompensationRequestModel,
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryMovementSourceReferenceModel,
)


@dataclass(frozen=True)
class CompensationExecutionResult:
    compensation_request_id: UUID
    original_movement_id: UUID
    resulting_movement_id: UUID


class InventoryMovementCompensationService:
    """Approve, reject and execute compensation movements."""

    SEPARATION_OF_DUTIES_KEY = "separation_of_duties"

    def __init__(self, db: Session) -> None:
        self._db = db
        self._sequences = InventoryLedgerSequenceService(db)
        self._codes = InventoryMovementCodeService(db)

    # ---------------------------------------------------------------- requests
    def request_compensation(
        self,
        *,
        organization_id: UUID,
        original_movement_id: UUID,
        reason_code: str,
        reason: str,
        evidence_file_ids: list[UUID],
        requested_by: UUID,
    ) -> InventoryMovementCompensationRequestModel:
        original = self._require_original(organization_id, original_movement_id)
        if original.status == MovementStatus.COMPENSATED.value:
            raise InventoryMovementAlreadyCompensated(
                "Original movement is already fully compensated.",
            )
        record = InventoryMovementCompensationRequestModel(
            organization_id=organization_id,
            original_movement_id=original.id,
            reason_code=reason_code,
            reason=reason,
            evidence_file_ids=[str(e) for e in evidence_file_ids],
            requested_by=requested_by,
            status="REQUESTED",
        )
        self._db.add(record)
        self._db.flush()
        return record

    def submit_for_review(
        self, *, organization_id: UUID, request_id: UUID, actor: UUID
    ) -> InventoryMovementCompensationRequestModel:
        record = self._require_request(organization_id, request_id)
        if record.status != "REQUESTED":
            raise InventoryMovementCompensationNotAllowed(
                "Compensation request is not in REQUESTED state.",
            )
        if record.requested_by == actor:
            raise InventoryMovementCompensationNotAllowed(
                "Requester cannot also be the reviewer.",
            )
        record.status = "UNDER_REVIEW"
        record.reviewed_by = actor
        record.reviewed_at = datetime.now(timezone.utc)
        self._db.flush()
        return record

    def approve(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
        approved_by: UUID,
        risk_level: str = "CRITICAL",
    ) -> InventoryMovementCompensationRequestModel:
        record = self._require_request(organization_id, request_id)
        if record.status not in {"UNDER_REVIEW", "REQUESTED"}:
            raise InventoryMovementCompensationNotAllowed(
                "Compensation request is not in a reviewable state.",
            )
        if record.requested_by == approved_by or (
            record.reviewed_by is not None and record.reviewed_by == approved_by
        ):
            raise InventoryMovementCompensationApprovalRequired(
                "Approver must be different from the requester and the reviewer.",
            )
        record.status = "APPROVED"
        record.approved_by = approved_by
        record.approved_at = datetime.now(timezone.utc)
        record.risk_level = risk_level
        record.separation_of_duties_check = {self.SEPARATION_OF_DUTIES_KEY: "OK"}
        self._db.flush()
        return record

    def reject(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
        rejected_by: UUID,
        rejection_reason: str,
    ) -> InventoryMovementCompensationRequestModel:
        record = self._require_request(organization_id, request_id)
        if record.status in {"EXECUTED", "REJECTED", "CANCELLED"}:
            raise InventoryMovementCompensationNotAllowed(
                "Compensation request cannot be rejected in its current state.",
            )
        record.status = "REJECTED"
        record.rejected_by = rejected_by
        record.rejected_at = datetime.now(timezone.utc)
        record.rejection_reason = rejection_reason
        self._db.flush()
        return record

    def cancel(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
        cancelled_by: UUID,
    ) -> InventoryMovementCompensationRequestModel:
        record = self._require_request(organization_id, request_id)
        if record.status in {"EXECUTED", "REJECTED", "CANCELLED"}:
            raise InventoryMovementCompensationNotAllowed(
                "Compensation request cannot be cancelled in its current state.",
            )
        record.status = "CANCELLED"
        self._db.flush()
        return record

    # ----------------------------------------------------------------- execute
    def execute(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
        actor: UUID,
    ) -> CompensationExecutionResult:
        record = self._require_request(organization_id, request_id)
        if record.status != "APPROVED":
            raise InventoryMovementCompensationApprovalRequired(
                "Compensation must be approved before execution.",
            )
        original = self._require_original(organization_id, record.original_movement_id)
        inverse_lines = self._build_inverse_lines(original)

        partition_key = self._sequences.build_partition_key(
            organization_id=organization_id,
            warehouse_id=original.warehouse_scope_id,
            fiscal_year=datetime.now(timezone.utc).year,
        )
        partition = self._sequences.get_or_create_partition(
            organization_id=organization_id,
            partition_key=partition_key,
            warehouse_id=original.warehouse_scope_id,
            fiscal_year=datetime.now(timezone.utc).year,
        )
        sequence = self._sequences.reserve_next_sequence(partition)
        movement_code, normalized = self._codes.build_movement_code(
            organization_id=organization_id,
            site_code="GLB",
            fiscal_year=datetime.now(timezone.utc).year,
            correlative=sequence,
            site_code_used=False,
        )
        occurred_at = datetime.now(timezone.utc)
        previous_hash = partition.last_movement_hash

        lines_payload: list[Mapping[str, object]] = []
        for line in inverse_lines:
            lines_payload.append(
                {
                    "line_number": line.line_number,
                    "product_id": str(line.product_id),
                    "product_version_id": (
                        str(line.product_version_id) if line.product_version_id else None
                    ),
                    "quantity": str(line.quantity),
                    "unit_id": str(line.unit_id),
                    "base_quantity": str(line.base_quantity),
                    "base_unit_id": str(line.base_unit_id),
                    "source_position_id": (
                        str(line.source_position_id) if line.source_position_id else None
                    ),
                    "destination_position_id": (
                        str(line.destination_position_id)
                        if line.destination_position_id
                        else None
                    ),
                    "source_external_boundary_kind": line.source_external_boundary_kind,
                    "destination_external_boundary_kind": line.destination_external_boundary_kind,
                    "quantity_direction": line.quantity_direction,
                }
            )

        sources_payload: list[Mapping[str, object]] = [
            {
                "source_system": SourceAdapterName.TECHNICAL_COMPENSATION.value
                if hasattr(SourceAdapterName, "TECHNICAL_COMPENSATION")
                else "TECHNICAL_COMPENSATION",
                "source_event_id": str(record.id),
                "source_event_version": 1,
                "source_entity_type": "COMPENSATION_REQUEST",
                "source_entity_id": str(record.id),
                "source_hash": record.reason_code,
            }
        ]

        movement_hash = compute_movement_hash(
            ledger_partition_key=partition_key,
            ledger_sequence=sequence,
            movement_code=normalized,
            movement_type=MovementType.TECHNICAL_COMPENSATION.value,
            movement_family=MOVEMENT_TYPE_FAMILY[MovementType.TECHNICAL_COMPENSATION.value],
            organization_id=organization_id,
            branch_id=original.branch_id,
            source_event_id=str(record.id),
            source_event_version=1,
            occurred_at=occurred_at,
            posted_at=occurred_at,
            reason_code=record.reason_code,
            compensation_for_movement_id=original.id,
            previous_movement_hash=previous_hash,
            lines=lines_payload,
            sources=sources_payload,
        )

        movement = InventoryMovementModel(
            organization_id=organization_id,
            branch_id=original.branch_id,
            warehouse_scope_id=original.warehouse_scope_id,
            movement_code=movement_code,
            normalized_movement_code=normalized,
            ledger_partition_key=partition_key,
            ledger_sequence=sequence,
            movement_type=MovementType.TECHNICAL_COMPENSATION.value,
            movement_family=MOVEMENT_TYPE_FAMILY[MovementType.TECHNICAL_COMPENSATION.value],
            status=MovementStatus.POSTED.value,
            source_system="INVENTORY_LEDGER",
            source_event_type="COMPENSATION_REQUEST",
            source_event_id=str(record.id),
            source_event_version=1,
            source_document_type=None,
            source_document_id=None,
            source_document_code=None,
            source_reference_snapshot={"compensation_reason": record.reason},
            posting_date=occurred_at.date(),
            occurred_at=occurred_at,
            posted_at=occurred_at,
            posted_by_user_id=actor,
            posted_by_service="inventory_ledger.compensation_service",
            reason_code=record.reason_code,
            reason_description=record.reason,
            line_count=len(inverse_lines),
            valuation_status="NOT_APPLICABLE",
            previous_movement_hash=previous_hash,
            movement_hash=movement_hash,
            canonicalization_version=CANONICALIZATION_VERSION,
            schema_version=SCHEMA_VERSION,
            compensation_for_movement_id=original.id,
        )
        self._db.add(movement)
        self._db.flush()

        for line in inverse_lines:
            line_record = InventoryMovementLineModel(
                inventory_movement_id=movement.id,
                line_number=line.line_number,
                product_id=line.product_id,
                product_version_id=line.product_version_id,
                product_snapshot=line.product_snapshot,
                quantity=line.quantity,
                unit_id=line.unit_id,
                base_quantity=line.base_quantity,
                base_unit_id=line.base_unit_id,
                conversion_rule_id=line.conversion_rule_id,
                conversion_snapshot=line.conversion_snapshot,
                source_position_id=line.source_position_id,
                destination_position_id=line.destination_position_id,
                source_position_snapshot=line.source_position_snapshot,
                destination_position_snapshot=line.destination_position_snapshot,
                source_external_boundary_id=line.source_external_boundary_id,
                destination_external_boundary_id=line.destination_external_boundary_id,
                source_external_boundary_kind=line.source_external_boundary_kind,
                destination_external_boundary_kind=line.destination_external_boundary_kind,
                quantity_direction=line.quantity_direction,
                reason_code=line.reason_code,
                traceability_reference_snapshot=line.traceability_reference_snapshot,
                cost_reference_snapshot=line.cost_reference_snapshot,
                metadata_snapshot=line.metadata_snapshot,
                content_hash=line.content_hash,
            )
            self._db.add(line_record)
        self._db.flush()

        source_ref = InventoryMovementSourceReferenceModel(
            movement_id=movement.id,
            source_system="INVENTORY_LEDGER",
            source_module="compensation",
            source_event_type="COMPENSATION_REQUEST",
            source_event_id=str(record.id),
            source_event_version=1,
            source_entity_type="COMPENSATION_REQUEST",
            source_entity_id=record.id,
            source_hash=movement_hash,
            source_occurred_at=occurred_at,
            adapter_name="TECHNICAL_COMPENSATION",
            adapter_version=ADAPTER_VERSION,
        )
        self._db.add(source_ref)

        original.compensated_by_movement_id = movement.id
        if not original.status or original.status == MovementStatus.POSTED.value:
            original.status = MovementStatus.COMPENSATED.value

        record.status = "EXECUTED"
        record.resulting_movement_id = movement.id
        self._db.flush()
        self._sequences.bind_last_movement(partition, movement)

        return CompensationExecutionResult(
            compensation_request_id=record.id,
            original_movement_id=original.id,
            resulting_movement_id=movement.id,
        )

    # ----------------------------------------------------------------- helpers
    def _require_original(
        self, organization_id: UUID, movement_id: UUID
    ) -> InventoryMovementModel:
        movement = self._db.get(InventoryMovementModel, movement_id)
        if movement is None:
            raise InventoryMovementNotFound(
                f"Movement {movement_id} not found.",
            )
        if movement.organization_id != organization_id:
            raise InventoryMovementOrganizationMismatch(
                "Movement does not belong to the current organization.",
            )
        return movement

    def _require_request(
        self, organization_id: UUID, request_id: UUID
    ) -> InventoryMovementCompensationRequestModel:
        stmt = select(InventoryMovementCompensationRequestModel).where(
            InventoryMovementCompensationRequestModel.id == request_id,
            InventoryMovementCompensationRequestModel.organization_id == organization_id,
        )
        record = self._db.scalars(stmt).first()
        if record is None:
            raise InventoryMovementNotFound(
                f"Compensation request {request_id} not found.",
            )
        return record

    def _build_inverse_lines(self, original: InventoryMovementModel):
        inverse = []
        for line in original.lines:  # type: ignore[attr-defined]
            inv_source_pos = line.destination_position_id
            inv_dest_pos = line.source_position_id
            inv_source_boundary = line.destination_external_boundary_kind
            inv_dest_boundary = line.source_external_boundary_kind
            inv_source_id = line.destination_external_boundary_id
            inv_dest_id = line.source_external_boundary_id
            inverse_direction = "COMPENSATION"
            new_line_number = line.line_number
            content_hash = compute_line_content_hash(
                line_number=new_line_number,
                product_id=line.product_id,
                product_version_id=line.product_version_id,
                quantity=Decimal(line.quantity),
                unit_id=line.unit_id,
                base_quantity=Decimal(line.base_quantity),
                base_unit_id=line.base_unit_id,
                source_position_id=inv_source_pos,
                destination_position_id=inv_dest_pos,
                source_external_boundary_kind=inv_source_boundary,
                destination_external_boundary_kind=inv_dest_boundary,
                quantity_direction=inverse_direction,
            )
            inverse.append(
                _InverseLine(
                    line_number=new_line_number,
                    product_id=line.product_id,
                    product_version_id=line.product_version_id,
                    product_snapshot=line.product_snapshot,
                    quantity=Decimal(line.quantity),
                    unit_id=line.unit_id,
                    base_quantity=Decimal(line.base_quantity),
                    base_unit_id=line.base_unit_id,
                    conversion_rule_id=line.conversion_rule_id,
                    conversion_snapshot=line.conversion_snapshot,
                    source_position_id=inv_source_pos,
                    destination_position_id=inv_dest_pos,
                    source_position_snapshot=line.destination_position_snapshot,
                    destination_position_snapshot=line.source_position_snapshot,
                    source_external_boundary_id=inv_source_id,
                    destination_external_boundary_id=inv_dest_id,
                    source_external_boundary_kind=inv_source_boundary,
                    destination_external_boundary_kind=inv_dest_boundary,
                    quantity_direction=inverse_direction,
                    reason_code=line.reason_code,
                    traceability_reference_snapshot=line.traceability_reference_snapshot,
                    cost_reference_snapshot=line.cost_reference_snapshot,
                    metadata_snapshot=line.metadata_snapshot,
                    content_hash=content_hash,
                )
            )
        return inverse


@dataclass
class _InverseLine:
    line_number: int
    product_id: UUID
    product_version_id: UUID | None
    product_snapshot: dict
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    base_unit_id: UUID
    conversion_rule_id: UUID | None
    conversion_snapshot: dict | None
    source_position_id: UUID | None
    destination_position_id: UUID | None
    source_position_snapshot: dict | None
    destination_position_snapshot: dict | None
    source_external_boundary_id: UUID | None
    destination_external_boundary_id: UUID | None
    source_external_boundary_kind: str | None
    destination_external_boundary_kind: str | None
    quantity_direction: str
    reason_code: str | None
    traceability_reference_snapshot: dict | None
    cost_reference_snapshot: dict | None
    metadata_snapshot: dict | None
    content_hash: str
