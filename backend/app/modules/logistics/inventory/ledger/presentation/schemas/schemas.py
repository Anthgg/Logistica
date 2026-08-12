"""Phase 044 — Pydantic v2 schemas for the inventory ledger HTTP layer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    ADAPTER_VERSION,
    CANONICALIZATION_VERSION,
    HASH_ALGORITHM,
    SCHEMA_VERSION,
)


class _BaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
        from_attributes=True,
    )


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------

class InventoryMovementCapabilities(_BaseModel):
    can_read: bool = False
    can_read_sensitive: bool = False
    can_read_sources: bool = False
    can_read_snapshot: bool = False
    can_read_history: bool = False
    can_read_integrity: bool = False
    can_publish_event: bool = False
    can_request_compensation: bool = False
    can_review_compensation: bool = False
    can_approve_compensation: bool = False
    can_execute_compensation: bool = False
    can_verify: bool = False
    can_create_checkpoint: bool = False
    can_reconcile: bool = False
    can_export: bool = False
    can_read_balance_preparation: bool = False
    can_read_traceability_preparation: bool = False


# ---------------------------------------------------------------------------
# Lines / sources / positions
# ---------------------------------------------------------------------------

class InventoryMovementLineResponse(_BaseModel):
    id: UUID
    line_number: int
    product_id: UUID
    product_version_id: UUID | None = None
    product_snapshot: dict[str, Any] = Field(default_factory=dict)
    quantity: Decimal
    unit_id: UUID
    base_quantity: Decimal
    base_unit_id: UUID
    conversion_rule_id: UUID | None = None
    conversion_snapshot: dict[str, Any] | None = None
    source_position_id: UUID | None = None
    destination_position_id: UUID | None = None
    source_position_snapshot: dict[str, Any] | None = None
    destination_position_snapshot: dict[str, Any] | None = None
    source_external_boundary_kind: str | None = None
    destination_external_boundary_kind: str | None = None
    quantity_direction: str
    reason_code: str | None = None
    traceability_reference_snapshot: dict[str, Any] | None = None
    cost_reference_snapshot: dict[str, Any] | None = None
    metadata_snapshot: dict[str, Any] | None = None
    content_hash: str


class InventoryMovementSourceResponse(_BaseModel):
    id: UUID
    source_system: str
    source_module: str
    source_event_type: str
    source_event_id: str
    source_event_version: int
    source_document_type: str | None = None
    source_document_id: UUID | None = None
    source_document_code: str | None = None
    source_entity_type: str
    source_entity_id: UUID
    source_hash: str
    source_occurred_at: datetime
    adapter_name: str
    adapter_version: str


class InventoryPositionResponse(_BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID | None = None
    warehouse_location_id: UUID | None = None
    boundary_type: str
    product_id: UUID
    product_version_id: UUID | None = None
    availability_state: str
    quality_state: str
    transit_state: str
    damage_state: str
    expiration_state: str
    dimension_key: str


# ---------------------------------------------------------------------------
# Movements
# ---------------------------------------------------------------------------

class InventoryMovementResponse(_BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_scope_id: UUID | None = None
    movement_code: str
    normalized_movement_code: str
    ledger_partition_key: str
    ledger_sequence: int
    movement_type: str
    movement_family: str
    status: str
    occurred_at: datetime
    posted_at: datetime
    reason_code: str | None = None
    reason_description: str | None = None
    line_count: int
    total_base_quantity_reference: Decimal | None = None
    currency_code: str | None = None
    valuation_status: str
    previous_movement_hash: str | None = None
    movement_hash: str
    canonicalization_version: str
    schema_version: str
    compensation_for_movement_id: UUID | None = None
    compensated_by_movement_id: UUID | None = None


class InventoryMovementSummary(_BaseModel):
    id: UUID
    movement_code: str
    ledger_sequence: int
    movement_family: str
    movement_type: str
    status: str
    occurred_at: datetime
    posted_at: datetime
    warehouse_summary: dict[str, Any] | None = None
    product_count: int
    line_count: int
    source_summary: dict[str, Any] | None = None
    source_document_summary: dict[str, Any] | None = None
    reason_code: str | None = None
    compensation_status: str | None = None
    integrity_status: str
    previous_hash_partial: str | None = None
    movement_hash_partial: str
    capabilities: InventoryMovementCapabilities = Field(default_factory=InventoryMovementCapabilities)


class InventoryMovementListResponse(_BaseModel):
    items: list[InventoryMovementSummary]
    total: int
    page: int
    page_size: int


class InventoryMovementIntegrityResponse(_BaseModel):
    verification_status: str
    first_hash: str | None = None
    last_hash: str | None = None
    last_sequence: int | None = None
    algorithm_version: str = CANONICALIZATION_VERSION
    hash_algorithm: str = HASH_ALGORITHM


class InventoryMovementSnapshotResponse(_BaseModel):
    movement: InventoryMovementResponse
    lines: list[InventoryMovementLineResponse]
    sources: list[InventoryMovementSourceResponse]
    positions: list[InventoryPositionResponse]
    compensation: InventoryMovementResponse | None = None
    captured_at: datetime
    content_hash: str


class InventoryMovementDetail(_BaseModel):
    movement: InventoryMovementResponse
    lines: list[InventoryMovementLineResponse]
    sources: list[InventoryMovementSourceResponse]
    positions: list[InventoryPositionResponse]
    compensation: InventoryMovementResponse | None = None
    capabilities: InventoryMovementCapabilities
    balance_preparation_summary: dict[str, Any] | None = None
    traceability_preparation_summary: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Posting requests
# ---------------------------------------------------------------------------

class InventoryMovementPostingRequestCreate(_BaseModel):
    request_key: str
    source_system: str
    source_event_type: str
    source_event_id: str
    source_event_version: int = 1
    payload: dict[str, Any]


class InventoryMovementPostingRequestResponse(_BaseModel):
    id: UUID
    request_key: str
    source_system: str
    source_event_type: str
    source_event_id: str
    source_event_version: int
    payload_hash: str
    status: str
    validation_result: dict[str, Any] | None = None
    resulting_movement_id: UUID | None = None
    failure_code: str | None = None
    failure_detail_safe: str | None = None
    requested_at: datetime
    completed_at: datetime | None = None


class PreparedInventoryEventValidationResponse(_BaseModel):
    validation_status: str
    blocking_errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    movement_type: str | None = None
    movement_family: str | None = None
    source_hash: str | None = None
    payload_hash: str | None = None
    server_time: datetime
    validation_hash: str | None = None
    posting_options: dict[str, Any] = Field(default_factory=dict)


class PreparedInventoryEventPostingRequest(_BaseModel):
    posting_request_id: UUID


# ---------------------------------------------------------------------------
# Compensation
# ---------------------------------------------------------------------------

class InventoryMovementCompensationRequestCreate(_BaseModel):
    reason_code: str
    reason: str
    evidence_file_ids: list[UUID] = Field(default_factory=list)


class InventoryMovementCompensationRequestResponse(_BaseModel):
    id: UUID
    organization_id: UUID
    original_movement_id: UUID
    reason_code: str
    reason: str
    evidence_file_ids: list[str]
    requested_by: UUID
    requested_at: datetime
    status: str
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejected_by: UUID | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    resulting_movement_id: UUID | None = None
    risk_level: str
    separation_of_duties_check: dict[str, Any] | None = None


class InventoryMovementCompensationDecisionRequest(_BaseModel):
    rejection_reason: str | None = None


# ---------------------------------------------------------------------------
# Kardex
# ---------------------------------------------------------------------------

class InventoryKardexQuery(_BaseModel):
    search: str | None = None
    movement_code: str | None = None
    ledger_sequence_from: int | None = None
    ledger_sequence_to: int | None = None
    movement_family: str | None = None
    movement_type: str | None = None
    status: str | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    product_id: UUID | None = None
    product_version_id: UUID | None = None
    sku: str | None = None
    source_system: str | None = None
    source_event_type: str | None = None
    source_event_id: str | None = None
    source_document_type: str | None = None
    source_document_code: str | None = None
    availability_state_from: str | None = None
    availability_state_to: str | None = None
    quality_state_from: str | None = None
    quality_state_to: str | None = None
    transit_state_from: str | None = None
    transit_state_to: str | None = None
    damage_state_from: str | None = None
    damage_state_to: str | None = None
    expiration_state_from: str | None = None
    expiration_state_to: str | None = None
    compensated: bool | None = None
    integrity_status: str | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    posted_from: datetime | None = None
    posted_to: datetime | None = None
    posted_by: UUID | None = None
    correlation_id: str | None = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "ledger_sequence"
    sort_direction: str = "DESC"


class InventoryKardexRow(_BaseModel):
    movement_id: UUID
    movement_code: str
    ledger_sequence: int
    movement_type: str
    movement_family: str
    status: str
    occurred_at: datetime
    posted_at: datetime
    warehouse_id: UUID | None = None
    product_id: UUID
    product_version_id: UUID | None = None
    quantity: Decimal
    base_quantity: Decimal
    unit_id: UUID
    base_unit_id: UUID
    source_position_id: UUID | None = None
    destination_position_id: UUID | None = None
    source_position_snapshot: dict[str, Any] | None = None
    destination_position_snapshot: dict[str, Any] | None = None
    source_document_code: str | None = None
    reason_code: str | None = None
    source_event_id: str
    movement_hash_partial: str
    compensation_status: str | None = None
    line_number: int | None = None
    signed_quantity_display: Decimal | None = None
    signed_base_quantity_display: Decimal | None = None
    quantity_direction: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class InventoryKardexResponse(_BaseModel):
    items: list[InventoryKardexRow]
    total: int
    page: int
    page_size: int
    filters: dict[str, Any] = Field(default_factory=dict)


class InventoryKardexRunningQuantityQuery(_BaseModel):
    warehouse_id: UUID
    product_id: UUID
    base_unit_id: UUID
    position_id: UUID | None = None
    availability_states: list[str] | None = None
    quality_states: list[str] | None = None
    transit_states: list[str] | None = None
    damage_states: list[str] | None = None
    expiration_states: list[str] | None = None
    sequence_from: int | None = None
    sequence_to: int | None = None
    opening_quantity_reference: Decimal = Decimal("0")


class InventoryKardexRunningQuantityRow(_BaseModel):
    ledger_sequence: int
    movement_id: str
    movement_code: str
    line_number: int
    signed_delta: Decimal
    running_quantity_reference: Decimal
    data_quality_status: str
    calculation_scope: str


class InventoryKardexExportCreate(_BaseModel):
    filters: InventoryKardexQuery
    format: str = "CSV"
    timezone: str = "UTC"


class InventoryKardexExportResponse(_BaseModel):
    id: UUID
    format: str
    status: str
    row_count: int
    file_path: str | None = None
    manifest_hash: str | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    expires_at: datetime | None = None
    download_url: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Ledger partition / checkpoint / verification
# ---------------------------------------------------------------------------

class InventoryLedgerPartitionResponse(_BaseModel):
    id: UUID
    organization_id: UUID
    partition_key: str
    warehouse_id: UUID | None = None
    fiscal_year: int | None = None
    current_sequence: int
    last_movement_id: UUID | None = None
    last_movement_hash: str | None = None


class InventoryLedgerCheckpointResponse(_BaseModel):
    id: UUID
    organization_id: UUID
    ledger_partition_key: str
    from_sequence: int
    to_sequence: int
    movement_count: int
    first_hash: str | None = None
    last_hash: str | None = None
    manifest_hash: str
    verification_status: str
    verified_at: datetime | None = None
    algorithm_version: str = CANONICALIZATION_VERSION


class InventoryLedgerVerificationRequest(_BaseModel):
    ledger_partition_key: str
    from_sequence: int | None = None
    to_sequence: int | None = None


class InventoryLedgerVerificationResponse(_BaseModel):
    verification_status: str
    last_sequence: int | None = None
    first_hash: str | None = None
    last_hash: str | None = None
    algorithm_version: str = CANONICALIZATION_VERSION


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

class InventoryLedgerReconciliationJobCreate(_BaseModel):
    scope: dict[str, Any] = Field(default_factory=dict)


class InventoryLedgerReconciliationJobResponse(_BaseModel):
    id: UUID
    organization_id: UUID
    scope: dict[str, Any]
    status: str
    triggered_by: str
    requested_by_user_id: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_events_seen: int
    total_movements_seen: int
    issue_count: int
    summary: dict[str, Any] | None = None


class InventoryLedgerReconciliationResult(_BaseModel):
    id: UUID
    job_id: UUID
    result_code: str
    source_system: str | None = None
    source_event_type: str | None = None
    source_event_id: str | None = None
    source_entity_type: str | None = None
    source_entity_id: UUID | None = None
    movement_id: UUID | None = None
    movement_code: str | None = None
    severity: str
    description: str
    detected_at: datetime


# ---------------------------------------------------------------------------
# Preparation responses (Phase 045 and 046 consumers)
# ---------------------------------------------------------------------------

class InventoryBalancePreparationResponse(_BaseModel):
    movement_id: UUID
    movement_line_id: UUID
    ledger_sequence: int
    organization_id: UUID
    warehouse_id: UUID | None = None
    position_id: UUID | None = None
    product_id: UUID
    product_version_id: UUID | None = None
    unit_id: UUID
    base_unit_id: UUID
    entry_base_quantity: Decimal
    exit_base_quantity: Decimal
    signed_delta_for_position: Decimal
    availability_state: str
    quality_state: str
    transit_state: str
    damage_state: str
    expiration_state: str
    occurred_at: datetime
    posted_at: datetime
    movement_hash: str
    source_hash: str
    compensation_status: str
    balance_materialization_key: str


class InventoryTraceabilityPreparationResponse(_BaseModel):
    movement_id: UUID
    movement_line_id: UUID
    product_id: UUID
    product_version_id: UUID | None = None
    source_position: dict[str, Any] | None = None
    destination_position: dict[str, Any] | None = None
    traceability_reference_type: str | None = None
    observed_lot_references: list[dict[str, Any]] = Field(default_factory=list)
    observed_serial_references: list[dict[str, Any]] = Field(default_factory=list)
    expiration_observations: list[dict[str, Any]] = Field(default_factory=list)
    packaging_snapshot: dict[str, Any] | None = None
    handling_unit_reference_hash: str | None = None
    quantity: Decimal
    unit: UUID
    movement_hash: str
