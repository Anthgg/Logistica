"""Phase 044 — Inventory ledger ORM models (append-only book).

Contains the following tables:

1.  inventory_ledger_partitions
2.  inventory_positions
3.  inventory_external_boundaries
4.  inventory_movement_posting_requests
5.  inventory_movements
6.  inventory_movement_lines
7.  inventory_movement_source_references
8.  inventory_movement_compensation_requests
9.  inventory_ledger_checkpoints
10. inventory_ledger_reconciliation_jobs
11. inventory_ledger_reconciliation_results
12. inventory_kardex_export_jobs
13. inventory_ledger_outbox_events

The book is append-only: a posted movement is immutable. Any correction
must be performed through a compensation movement, never by editing or
deleting the original record.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _uuid() -> UUID:
    return uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. Inventory Ledger Partition
# ---------------------------------------------------------------------------


class InventoryLedgerPartitionModel(Base):
    __tablename__ = "inventory_ledger_partitions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    partition_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    fiscal_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_movement_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    last_movement_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "partition_key", name="uq_inventory_ledger_partition_key"
        ),
        CheckConstraint(
            "current_sequence >= 0", name="ck_inventory_ledger_partition_sequence_nonnegative"
        ),
    )


# ---------------------------------------------------------------------------
# 2. Inventory Position (dimension, no quantity)
# ---------------------------------------------------------------------------


class InventoryPositionModel(Base):
    __tablename__ = "inventory_positions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    branch_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    warehouse_location_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    boundary_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    product_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    ownership_type: Mapped[str] = mapped_column(String(30), nullable=False, default="OWNED")
    owner_business_partner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    availability_state: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")
    quality_state: Mapped[str] = mapped_column(String(30), nullable=False, default="UNKNOWN")
    transit_state: Mapped[str] = mapped_column(String(30), nullable=False, default="NOT_IN_TRANSIT")
    damage_state: Mapped[str] = mapped_column(String(30), nullable=False, default="NORMAL")
    expiration_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NOT_APPLICABLE"
    )
    tracking_reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tracking_reference_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    handling_unit_reference_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dimension_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "dimension_key", name="uq_inventory_position_dimension_key"
        ),
    )


# ---------------------------------------------------------------------------
# 3. Inventory External Boundary
# ---------------------------------------------------------------------------


class InventoryExternalBoundaryModel(Base):
    __tablename__ = "inventory_external_boundaries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    boundary_kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_partner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "normalized_code", name="uq_inventory_external_boundary_code"
        ),
    )


# ---------------------------------------------------------------------------
# 4. Posting Request (draft / idempotency carrier)
# ---------------------------------------------------------------------------


class InventoryMovementPostingRequestModel(Base):
    __tablename__ = "inventory_movement_posting_requests"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    request_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(60), nullable=False)
    source_module: Mapped[str] = mapped_column(
        String(60), nullable=False, default="INVENTORY_LEDGER"
    )
    source_event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(120), nullable=False)
    source_event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="RECEIVED", index=True)
    validation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resulting_movement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_detail_safe: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    requested_by_service: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_system",
            "source_event_type",
            "source_event_id",
            "source_event_version",
            name="uq_inventory_posting_request_source_event",
        ),
    )


# ---------------------------------------------------------------------------
# 5. Inventory Movement (header of the append-only book)
# ---------------------------------------------------------------------------


class InventoryMovementModel(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    branch_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_scope_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    movement_code: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_movement_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    ledger_partition_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    ledger_sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    movement_family: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="POSTED", index=True)
    source_system: Mapped[str] = mapped_column(String(60), nullable=False)
    source_event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_document_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    source_document_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    source_reference_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    posting_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
    posted_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    posted_by_service: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    reason_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_base_quantity_reference: Mapped[Decimal | None] = mapped_column(
        Numeric(38, 18), nullable=True
    )
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    valuation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NOT_APPLICABLE"
    )
    previous_movement_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    movement_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    canonicalization_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0.0"
    )
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    compensation_for_movement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    compensated_by_movement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "normalized_movement_code", name="uq_inventory_movement_code"
        ),
        UniqueConstraint(
            "ledger_partition_key",
            "ledger_sequence",
            name="uq_inventory_movement_partition_sequence",
        ),
        CheckConstraint("ledger_sequence >= 1", name="ck_inventory_movement_sequence_positive"),
        CheckConstraint("line_count >= 0", name="ck_inventory_movement_line_count_nonnegative"),
    )


# ---------------------------------------------------------------------------
# 6. Inventory Movement Line
# ---------------------------------------------------------------------------


class InventoryMovementLineModel(Base):
    __tablename__ = "inventory_movement_lines"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    inventory_movement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_movements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    product_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    product_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    base_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    base_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    conversion_rule_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    conversion_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_position_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_positions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    destination_position_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_positions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    source_position_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    destination_position_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_external_boundary_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_external_boundaries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    destination_external_boundary_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_external_boundaries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    source_external_boundary_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)
    destination_external_boundary_kind: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )
    quantity_direction: Mapped[str] = mapped_column(String(30), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    traceability_reference_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cost_reference_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "inventory_movement_id", "line_number", name="uq_inventory_movement_line_number"
        ),
        CheckConstraint("quantity > 0", name="ck_inventory_movement_line_quantity_positive"),
        CheckConstraint(
            "base_quantity > 0", name="ck_inventory_movement_line_base_quantity_positive"
        ),
        CheckConstraint(
            "(source_position_id IS NOT NULL AND source_external_boundary_id IS NULL AND source_external_boundary_kind IS NULL) OR "
            "(source_position_id IS NULL AND (source_external_boundary_id IS NOT NULL OR source_external_boundary_kind IS NOT NULL))",
            name="ck_inventory_movement_line_source_boundary",
        ),
        CheckConstraint(
            "(destination_position_id IS NOT NULL AND destination_external_boundary_id IS NULL AND destination_external_boundary_kind IS NULL) OR "
            "(destination_position_id IS NULL AND (destination_external_boundary_id IS NOT NULL OR destination_external_boundary_kind IS NOT NULL))",
            name="ck_inventory_movement_line_destination_boundary",
        ),
    )


# ---------------------------------------------------------------------------
# 7. Inventory Movement Source Reference
# ---------------------------------------------------------------------------


class InventoryMovementSourceReferenceModel(Base):
    __tablename__ = "inventory_movement_source_references"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    movement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_movements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_system: Mapped[str] = mapped_column(String(60), nullable=False)
    source_module: Mapped[str] = mapped_column(String(60), nullable=False)
    source_event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_document_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    source_document_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source_entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    adapter_name: Mapped[str] = mapped_column(String(80), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index(
            "ix_inventory_movement_source_event",
            "source_system",
            "source_event_type",
            "source_event_id",
        ),
    )


# ---------------------------------------------------------------------------
# 8. Compensation Request
# ---------------------------------------------------------------------------


class InventoryMovementCompensationRequestModel(Base):
    __tablename__ = "inventory_movement_compensation_requests"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    original_movement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_movements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reason_code: Mapped[str] = mapped_column(String(60), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_file_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    requested_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED", index=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    resulting_movement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="HIGH")
    separation_of_duties_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("row_version >= 1", name="ck_inventory_compensation_request_row_version"),
    )


# ---------------------------------------------------------------------------
# 9. Checkpoint
# ---------------------------------------------------------------------------


class InventoryLedgerCheckpointModel(Base):
    __tablename__ = "inventory_ledger_checkpoints"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    ledger_partition_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    from_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    to_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VERIFYING", index=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_service: Mapped[str | None] = mapped_column(String(100), nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "ledger_partition_key",
            "from_sequence",
            "to_sequence",
            name="uq_inventory_ledger_checkpoint_range",
        ),
        CheckConstraint("from_sequence >= 1", name="ck_inventory_ledger_checkpoint_from_seq"),
        CheckConstraint(
            "to_sequence >= from_sequence", name="ck_inventory_ledger_checkpoint_range_order"
        ),
        CheckConstraint("movement_count >= 0", name="ck_inventory_ledger_checkpoint_count_nonneg"),
    )


# ---------------------------------------------------------------------------
# 10. Reconciliation Job
# ---------------------------------------------------------------------------


class InventoryLedgerReconciliationJobModel(Base):
    __tablename__ = "inventory_ledger_reconciliation_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    scope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED", index=True)
    triggered_by: Mapped[str] = mapped_column(String(30), nullable=False, default="SCHEDULED")
    requested_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_events_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_movements_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


# ---------------------------------------------------------------------------
# 11. Reconciliation Result
# ---------------------------------------------------------------------------


class InventoryLedgerReconciliationResultModel(Base):
    __tablename__ = "inventory_ledger_reconciliation_results"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_ledger_reconciliation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    result_code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    source_system: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_event_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_entity_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_entity_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    movement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    movement_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


# ---------------------------------------------------------------------------
# 12. Kardex Export Job
# ---------------------------------------------------------------------------


class InventoryKardexExportJobModel(Base):
    __tablename__ = "inventory_kardex_export_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    requested_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="CSV")
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, default="UTC")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED", index=True)
    initial_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    manifest_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    warnings: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    integrity_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


# ---------------------------------------------------------------------------
# 13. Inventory Ledger Outbox (transactional)
# ---------------------------------------------------------------------------


class InventoryLedgerOutboxEventModel(Base):
    __tablename__ = "inventory_ledger_outbox_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    aggregate_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    event_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


# ---------------------------------------------------------------------------
# Tuple for Alembic
# ---------------------------------------------------------------------------

PHASE_044_TABLES = (
    "inventory_ledger_partitions",
    "inventory_positions",
    "inventory_external_boundaries",
    "inventory_movement_posting_requests",
    "inventory_movements",
    "inventory_movement_lines",
    "inventory_movement_source_references",
    "inventory_movement_compensation_requests",
    "inventory_ledger_checkpoints",
    "inventory_ledger_reconciliation_jobs",
    "inventory_ledger_reconciliation_results",
    "inventory_kardex_export_jobs",
    "inventory_ledger_outbox_events",
)
