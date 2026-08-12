"""Inventory movement posting service (append-only book).

This is the single transactional entry point that turns a
``PostingRequest`` into a POSTED movement. It orchestrates:

* idempotency resolution
* validation
* position resolution
* sequence allocation
* code allocation
* hash computation
* line + source persistence
* outbox + audit emission
* posting request status update
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryMovementLineInvalid,
    InventoryMovementNotFound,
    InventoryMovementPostingFailed,
    InventoryMovementSourceDuplicated,
    InventoryMovementSourceNotFound,
    InventoryPostingRequestNotFound,
)
from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
    compute_line_content_hash,
    compute_movement_hash,
)
from app.modules.logistics.inventory.ledger.domain.services.idempotency_service import (
    InventoryMovementIdempotencyService,
    hash_payload,
)
from app.modules.logistics.inventory.ledger.domain.services.position_service import (
    InventoryPositionService,
)
from app.modules.logistics.inventory.ledger.domain.services.sequence_service import (
    InventoryLedgerSequenceService,
    InventoryMovementCodeService,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    ADAPTER_VERSION,
    CANONICALIZATION_VERSION,
    MOVEMENT_TYPE_FAMILY,
    SCHEMA_VERSION,
    MovementStatus,
    PostingRequestStatus,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryLedgerOutboxEventModel,
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryMovementPostingRequestModel,
    InventoryMovementSourceReferenceModel,
    InventoryPositionModel,
)


@dataclass(frozen=True)
class PostingResult:
    posting_request_id: UUID
    movement_id: UUID
    movement_code: str
    movement_hash: str
    ledger_sequence: int
    duplicate: bool


class InventoryMovementPostingService:
    """Orchestrates the transactional publication of a movement."""

    def __init__(
        self,
        db: Session,
        *,
        validation_service,
        ledger_audit_service=None,
        outbox_publisher=None,
    ) -> None:
        self._db = db
        self._validation = validation_service
        self._positions = InventoryPositionService(db)
        self._sequences = InventoryLedgerSequenceService(db)
        self._codes = InventoryMovementCodeService(db)
        self._idempotency = InventoryMovementIdempotencyService(db)
        self._audit = ledger_audit_service
        self._outbox = outbox_publisher

    # ------------------------------------------------------------------ public
    def create_posting_request(
        self,
        *,
        organization_id: UUID,
        request_key: str,
        source_system: str,
        source_event_type: str,
        source_event_id: str,
        source_event_version: int,
        payload: Mapping[str, Any],
        requested_by_user_id: UUID | None = None,
        requested_by_service: str | None = None,
    ) -> InventoryMovementPostingRequestModel:
        if requested_by_service == "api":
            assert_no_server_derived_fields(payload)
        payload_hash = hash_payload(dict(payload))
        existing = self._find_existing(
            organization_id=organization_id,
            source_system=source_system,
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            source_event_version=source_event_version,
        )
        if existing is not None:
            if existing.payload_hash != payload_hash:
                raise InventoryMovementSourceDuplicated(
                    "Posting request already exists with a different payload.",
                )
            return existing
        record = InventoryMovementPostingRequestModel(
            organization_id=organization_id,
            request_key=request_key,
            source_system=source_system,
            source_module="INVENTORY_LEDGER",
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            source_event_version=source_event_version,
            payload_hash=payload_hash,
            payload=dict(payload),
            status=PostingRequestStatus.RECEIVED.value,
            requested_by_user_id=requested_by_user_id,
            requested_by_service=requested_by_service,
            requested_at=datetime.now(timezone.utc),
        )
        self._db.add(record)
        self._db.flush()
        return record

    def post(
        self,
        *,
        organization_id: UUID,
        posting_request_id: UUID,
        actor_user_id: UUID | None = None,
        actor_service: str | None = None,
    ) -> PostingResult:
        record = self._db.get(InventoryMovementPostingRequestModel, posting_request_id)
        if record is None:
            raise InventoryPostingRequestNotFound(
                f"Posting request {posting_request_id} not found.",
            )
        if record.organization_id != organization_id:
            raise InventoryMovementNotFound(
                "Posting request does not belong to the current organization.",
            )
        if record.status == PostingRequestStatus.POSTED.value and record.resulting_movement_id:
            existing_movement = self._db.get(InventoryMovementModel, record.resulting_movement_id)
            if existing_movement is not None:
                return PostingResult(
                    posting_request_id=record.id,
                    movement_id=existing_movement.id,
                    movement_code=existing_movement.movement_code,
                    movement_hash=existing_movement.movement_hash,
                    ledger_sequence=existing_movement.ledger_sequence,
                    duplicate=True,
                )

        # Idempotency: also resolve through the global IdempotencyRecord.
        self._idempotency.register(
            organization_id=organization_id,
            idempotency_key=record.request_key,
            payload_hash=record.payload_hash,
        )

        record.status = PostingRequestStatus.VALIDATING.value
        self._db.flush()

        try:
            validation = self._validation.validate(
                organization_id=organization_id,
                source_adapter_name=str(record.payload.get("source_adapter_name", "")),
                movement_type=str(record.payload.get("movement_type", "")),
                payload=record.payload,
            )
        except Exception as exc:  # noqa: BLE001 - map any validation error
            record.status = PostingRequestStatus.FAILED.value
            record.failure_code = getattr(exc, "code", "INVENTORY_MOVEMENT_VALIDATION_FAILED")
            record.failure_detail_safe = str(exc)[:500]
            record.completed_at = datetime.now(timezone.utc)
            self._db.flush()
            raise

        record.validation_result = {
            "validation_status": validation.validation_status,
            "blocking_errors": [vars(e) for e in validation.blocking_errors],
            "warnings": [vars(w) for w in validation.warnings],
            "validation_hash": validation.validation_hash,
        }
        if validation.blocking_errors:
            record.status = PostingRequestStatus.FAILED.value
            record.failure_code = validation.blocking_errors[0].code
            record.failure_detail_safe = validation.blocking_errors[0].message[:500]
            record.completed_at = datetime.now(timezone.utc)
            self._db.flush()
            raise InventoryMovementPostingFailed(
                validation.blocking_errors[0].message,
            )
        record.status = PostingRequestStatus.VALID.value
        record.status = PostingRequestStatus.POSTING.value
        self._db.flush()

        try:
            movement = self._persist_movement(
                organization_id=organization_id,
                record=record,
                validation=validation,
                actor_user_id=actor_user_id,
                actor_service=actor_service,
            )
        except Exception as exc:  # noqa: BLE001
            record.status = PostingRequestStatus.FAILED.value
            record.failure_code = getattr(exc, "code", "INVENTORY_MOVEMENT_POSTING_FAILED")
            record.failure_detail_safe = str(exc)[:500]
            record.completed_at = datetime.now(timezone.utc)
            self._db.flush()
            raise

        record.status = PostingRequestStatus.POSTED.value
        record.resulting_movement_id = movement.id
        record.completed_at = datetime.now(timezone.utc)
        self._db.flush()

        self._emit_outbox(movement, validation, record)
        if self._audit is not None:
            try:
                self._audit.record_movement_posted(
                    organization_id=organization_id,
                    movement=movement,
                    actor_user_id=actor_user_id,
                    actor_service=actor_service,
                )
            except Exception:  # noqa: BLE001
                # Audit must not block a posted movement.
                pass

        return PostingResult(
            posting_request_id=record.id,
            movement_id=movement.id,
            movement_code=movement.movement_code,
            movement_hash=movement.movement_hash,
            ledger_sequence=movement.ledger_sequence,
            duplicate=False,
        )

    # ------------------------------------------------------------------ helpers
    def _find_existing(
        self,
        *,
        organization_id: UUID,
        source_system: str,
        source_event_type: str,
        source_event_id: str,
        source_event_version: int,
    ) -> InventoryMovementPostingRequestModel | None:
        stmt = select(InventoryMovementPostingRequestModel).where(
            InventoryMovementPostingRequestModel.organization_id == organization_id,
            InventoryMovementPostingRequestModel.source_system == source_system,
            InventoryMovementPostingRequestModel.source_event_type == source_event_type,
            InventoryMovementPostingRequestModel.source_event_id == source_event_id,
            InventoryMovementPostingRequestModel.source_event_version == source_event_version,
        )
        return self._db.scalars(stmt).first()

    def _persist_movement(
        self,
        *,
        organization_id: UUID,
        record: InventoryMovementPostingRequestModel,
        validation,
        actor_user_id: UUID | None,
        actor_service: str | None,
    ) -> InventoryMovementModel:
        payload = record.payload
        warehouse_id_raw = payload.get("warehouse_id")
        warehouse_id = UUID(str(warehouse_id_raw)) if warehouse_id_raw else None
        branch_id = UUID(str(payload["branch_id"]))
        movement_type = str(payload["movement_type"])
        family = MOVEMENT_TYPE_FAMILY[movement_type]
        occurred_at_raw = payload.get("occurred_at")
        occurred_at = (
            occurred_at_raw
            if isinstance(occurred_at_raw, datetime)
            else datetime.fromisoformat(str(occurred_at_raw))
        )
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        else:
            occurred_at = occurred_at.astimezone(timezone.utc)
        posted_at = datetime.now(timezone.utc)
        fiscal_year = occurred_at.year

        partition_key = self._sequences.build_partition_key(
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            fiscal_year=fiscal_year,
        )
        partition = self._sequences.get_or_create_partition(
            organization_id=organization_id,
            partition_key=partition_key,
            warehouse_id=warehouse_id,
            fiscal_year=fiscal_year,
        )
        sequence = self._sequences.reserve_next_sequence(partition)

        movement_code, normalized = self._codes.build_movement_code(
            organization_id=organization_id,
            site_code=str(payload.get("site_code", "GLB")),
            fiscal_year=fiscal_year,
            correlative=sequence,
            site_code_used=bool(payload.get("site_code_used", True)),
        )
        if self._codes.is_code_taken(
            organization_id=organization_id,
            normalized_movement_code=normalized,
        ):
            raise InventoryMovementPostingFailed(
                f"Movement code {normalized} already exists.",
            )

        # Materialize lines + positions.
        materialized_lines: list[InventoryMovementLineModel] = []
        lines_payload: list[Mapping[str, Any]] = []
        for resolved in validation.resolved_lines:
            source_position = self._resolve_position(organization_id, payload, resolved, "source")
            destination_position = self._resolve_position(
                organization_id, payload, resolved, "destination"
            )
            line_content_hash = compute_line_content_hash(
                line_number=resolved.line_number,
                product_id=resolved.product_id,
                product_version_id=resolved.product_version_id,
                quantity=resolved.quantity,
                unit_id=resolved.unit_id,
                base_quantity=resolved.base_quantity,
                base_unit_id=resolved.base_unit_id,
                source_position_id=source_position.id if source_position else None,
                destination_position_id=destination_position.id if destination_position else None,
                source_external_boundary_kind=resolved.source_external_boundary_kind,
                destination_external_boundary_kind=resolved.destination_external_boundary_kind,
                quantity_direction=resolved.quantity_direction,
            )
            line = InventoryMovementLineModel(
                inventory_movement_id=None,  # assigned after movement insert
                line_number=resolved.line_number,
                product_id=resolved.product_id,
                product_version_id=resolved.product_version_id,
                product_snapshot=dict(resolved.product_snapshot),
                quantity=resolved.quantity,
                unit_id=resolved.unit_id,
                base_quantity=resolved.base_quantity,
                base_unit_id=resolved.base_unit_id,
                conversion_rule_id=resolved.conversion_rule_id,
                conversion_snapshot=resolved.conversion_snapshot,
                source_position_id=source_position.id if source_position else None,
                destination_position_id=destination_position.id if destination_position else None,
                source_position_snapshot=(
                    _position_snapshot(source_position) if source_position else None
                ),
                destination_position_snapshot=(
                    _position_snapshot(destination_position) if destination_position else None
                ),
                source_external_boundary_kind=resolved.source_external_boundary_kind,
                destination_external_boundary_kind=resolved.destination_external_boundary_kind,
                quantity_direction=resolved.quantity_direction,
                reason_code=resolved.reason_code,
                traceability_reference_snapshot=payload.get("traceability_reference_snapshot"),
                cost_reference_snapshot=payload.get("cost_reference_snapshot"),
                metadata_snapshot=resolved.metadata,
                content_hash=line_content_hash,
            )
            materialized_lines.append(line)
            lines_payload.append(
                {
                    "line_number": resolved.line_number,
                    "product_id": str(resolved.product_id),
                    "product_version_id": (
                        str(resolved.product_version_id) if resolved.product_version_id else None
                    ),
                    "quantity": str(resolved.quantity),
                    "unit_id": str(resolved.unit_id),
                    "base_quantity": str(resolved.base_quantity),
                    "base_unit_id": str(resolved.base_unit_id),
                    "source_position_id": (str(source_position.id) if source_position else None),
                    "destination_position_id": (
                        str(destination_position.id) if destination_position else None
                    ),
                    "source_external_boundary_kind": resolved.source_external_boundary_kind,
                    "destination_external_boundary_kind": resolved.destination_external_boundary_kind,
                    "quantity_direction": resolved.quantity_direction,
                    "content_hash": line_content_hash,
                }
            )

        sources_payload: list[Mapping[str, Any]] = self._build_sources_payload(payload)
        previous_hash = partition.last_movement_hash

        movement_hash = compute_movement_hash(
            ledger_partition_key=partition_key,
            ledger_sequence=sequence,
            movement_code=normalized,
            movement_type=movement_type,
            movement_family=family,
            organization_id=organization_id,
            branch_id=branch_id,
            source_event_id=record.source_event_id,
            source_event_version=record.source_event_version,
            occurred_at=occurred_at,
            posted_at=posted_at,
            reason_code=payload.get("reason_code"),
            compensation_for_movement_id=payload.get("compensation_for_movement_id"),
            previous_movement_hash=previous_hash,
            lines=lines_payload,
            sources=sources_payload,
        )

        movement = InventoryMovementModel(
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_scope_id=warehouse_id,
            movement_code=movement_code,
            normalized_movement_code=normalized,
            ledger_partition_key=partition_key,
            ledger_sequence=sequence,
            movement_type=movement_type,
            movement_family=family,
            status=MovementStatus.POSTED.value,
            source_system=record.source_system,
            source_event_type=record.source_event_type,
            source_event_id=record.source_event_id,
            source_event_version=record.source_event_version,
            source_document_type=payload.get("source_document_type"),
            source_document_id=(
                UUID(str(payload["source_document_id"]))
                if payload.get("source_document_id")
                else None
            ),
            source_document_code=payload.get("source_document_code"),
            source_reference_snapshot=payload.get("source_reference_snapshot"),
            posting_date=posted_at.date(),
            occurred_at=occurred_at,
            posted_at=posted_at,
            posted_by_user_id=actor_user_id,
            posted_by_service=actor_service,
            reason_code=payload.get("reason_code"),
            reason_description=payload.get("reason_description"),
            line_count=len(materialized_lines),
            total_base_quantity_reference=sum(
                (line.base_quantity for line in materialized_lines),
                Decimal("0"),
            )
            or None,
            currency_code=payload.get("currency_code"),
            valuation_status=str(payload.get("valuation_status", "NOT_APPLICABLE")),
            previous_movement_hash=previous_hash,
            movement_hash=movement_hash,
            canonicalization_version=CANONICALIZATION_VERSION,
            schema_version=SCHEMA_VERSION,
            compensation_for_movement_id=(
                UUID(str(payload["compensation_for_movement_id"]))
                if payload.get("compensation_for_movement_id")
                else None
            ),
        )
        self._db.add(movement)
        self._db.flush()

        for line in materialized_lines:
            line.inventory_movement_id = movement.id
            self._db.add(line)
        self._db.flush()

        for src in sources_payload:
            source_record = InventoryMovementSourceReferenceModel(
                movement_id=movement.id,
                source_system=str(src["source_system"]),
                source_module=str(src.get("source_module", "INVENTORY_LEDGER")),
                source_event_type=str(src["source_event_type"]),
                source_event_id=str(src["source_event_id"]),
                source_event_version=int(src.get("source_event_version", 1)),
                source_document_type=src.get("source_document_type"),
                source_document_id=(
                    UUID(str(src["source_document_id"])) if src.get("source_document_id") else None
                ),
                source_document_code=src.get("source_document_code"),
                source_entity_type=str(src["source_entity_type"]),
                source_entity_id=UUID(str(src["source_entity_id"])),
                source_hash=str(src["source_hash"]),
                source_occurred_at=(
                    src["source_occurred_at"]
                    if isinstance(src["source_occurred_at"], datetime)
                    else datetime.fromisoformat(str(src["source_occurred_at"]))
                ),
                adapter_name=str(src.get("adapter_name", record.source_system)),
                adapter_version=str(src.get("adapter_version", ADAPTER_VERSION)),
            )
            self._db.add(source_record)
        self._db.flush()

        self._sequences.bind_last_movement(partition, movement)
        return movement

    def _build_sources_payload(self, payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        sources = payload.get("source_references")
        if not isinstance(sources, list) or not sources:
            raise InventoryMovementSourceNotFound(
                "At least one source reference is required.",
            )
        resolved: list[Mapping[str, Any]] = []
        for idx, src in enumerate(sources):
            if not isinstance(src, Mapping):
                raise InventoryMovementSourceNotFound(
                    f"source_references[{idx}] must be a mapping.",
                )
            if "source_event_id" not in src or "source_entity_id" not in src:
                raise InventoryMovementSourceNotFound(
                    f"source_references[{idx}] missing identifiers.",
                )
            resolved.append(
                {
                    "source_system": str(src.get("source_system", "INVENTORY_LEDGER")),
                    "source_module": str(src.get("source_module", "INVENTORY_LEDGER")),
                    "source_event_type": str(src.get("source_event_type", "")),
                    "source_event_id": str(src.get("source_event_id", "")),
                    "source_event_version": int(src.get("source_event_version", 1)),
                    "source_document_type": src.get("source_document_type"),
                    "source_document_id": src.get("source_document_id"),
                    "source_document_code": src.get("source_document_code"),
                    "source_entity_type": str(src.get("source_entity_type", "")),
                    "source_entity_id": str(src.get("source_entity_id", "")),
                    "source_hash": str(src.get("source_hash", "")),
                    "source_occurred_at": src.get("source_occurred_at"),
                    "adapter_name": str(src.get("adapter_name", "INVENTORY_LEDGER")),
                    "adapter_version": str(src.get("adapter_version", ADAPTER_VERSION)),
                }
            )
        return resolved

    def _resolve_position(
        self,
        organization_id: UUID,
        payload: Mapping[str, Any],
        resolved_line,
        side: str,
    ) -> InventoryPositionModel | None:
        if side == "source":
            position_id = resolved_line.source_position_id
        else:
            position_id = resolved_line.destination_position_id
        if position_id is not None:
            position = self._db.get(InventoryPositionModel, position_id)
            if position is None:
                raise InventoryMovementPostingFailed(
                    f"{side} position {position_id} not found.",
                )
            return position
        # External boundary lines do not produce an internal position row.
        return None

    def _emit_outbox(
        self,
        movement: InventoryMovementModel,
        validation,
        record: InventoryMovementPostingRequestModel,
    ) -> None:
        event = InventoryLedgerOutboxEventModel(
            organization_id=movement.organization_id,
            aggregate_type="INVENTORY_MOVEMENT",
            aggregate_id=movement.id,
            event_type="InventoryMovementPosted",
            payload={
                "movement_id": str(movement.id),
                "movement_code": movement.movement_code,
                "movement_type": movement.movement_type,
                "movement_family": movement.movement_family,
                "ledger_sequence": movement.ledger_sequence,
                "ledger_partition_key": movement.ledger_partition_key,
                "source_event_id": movement.source_event_id,
                "validation_hash": validation.validation_hash,
                "posting_request_id": str(record.id),
            },
            correlation_id=record.request_key,
        )
        self._db.add(event)
        self._db.flush()
        if self._outbox is not None:
            try:
                self._outbox.publish(event)
            except Exception:  # noqa: BLE001
                pass


def _position_snapshot(position: InventoryPositionModel) -> dict:
    return {
        "id": str(position.id),
        "warehouse_id": str(position.warehouse_id) if position.warehouse_id else None,
        "warehouse_location_id": (
            str(position.warehouse_location_id) if position.warehouse_location_id else None
        ),
        "boundary_type": position.boundary_type,
        "availability_state": position.availability_state,
        "quality_state": position.quality_state,
        "transit_state": position.transit_state,
        "damage_state": position.damage_state,
        "expiration_state": position.expiration_state,
        "dimension_key": position.dimension_key,
    }


_SERVER_DERIVED_FIELDS = frozenset(
    {
        "base_quantity",
        "conversion_snapshot",
        "signed_quantity",
        "signed_base_quantity",
        "previous_balance",
        "new_balance",
        "movement_hash",
        "previous_movement_hash",
        "posted_by",
        "approved_by",
        "step_up_passed",
        "risk_level",
        "biometric_score",
        "dimension_key",
    }
)


def _find_forbidden_client_fields(value: Any, path: str = "payload") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            current = f"{path}.{key}"
            if str(key) in _SERVER_DERIVED_FIELDS:
                found.append(current)
            found.extend(_find_forbidden_client_fields(nested, current))
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            found.extend(_find_forbidden_client_fields(nested, f"{path}[{index}]"))
    return found


def assert_no_server_derived_fields(payload: Mapping[str, Any]) -> None:
    forbidden = _find_forbidden_client_fields(payload)
    if forbidden:
        raise InventoryMovementLineInvalid(
            "Client payload contains server-derived fields: " + ", ".join(forbidden)
        )
