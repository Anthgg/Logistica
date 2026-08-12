"""Pydantic v2 schemas for Inventory Document contexts and Package Manifests (Phase 017).

Covers: EUB, PUT, MOV, AJI, CNT, ADI, TRA, CRT
Phase dependencies:
  - LocationSnapshot: PENDING_PHASE_022
  - ProductSnapshot: PENDING_PHASE_023
  - StockState: PENDING_PHASE_044 / PENDING_PHASE_045
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Shared sub-schemas
# ---------------------------------------------------------------------------


class LocationSnapshot(BaseModel):
    """Snapshot of a warehouse location. Full model: PENDING_PHASE_022."""

    model_config = ConfigDict(extra="ignore")

    location_code: str
    warehouse_code: str
    zone_code: str | None = None
    aisle_code: str | None = None
    rack_code: str | None = None
    level_code: str | None = None
    position_code: str | None = None
    location_type: str | None = None
    capacity: Decimal | None = Field(default=None, ge=0)
    capacity_unit: str | None = None
    restrictions: list[str] = Field(default_factory=list)
    status: str = "ACTIVE"


class ProductSnapshot(BaseModel):
    """Snapshot of a product. Full catalog: PENDING_PHASE_023."""

    model_config = ConfigDict(extra="ignore")

    sku: str | None = None
    barcode: str | None = None
    description: str
    category: str | None = None
    base_unit: str = "UND"
    tracking_type: str = "NONE"


class InventoryItemLine(BaseModel):
    """Generic inventory line item used across document types."""

    model_config = ConfigDict(extra="ignore")

    line_number: int = 1
    sku: str | None = None
    description: str = "—"
    lot_number: str | None = None
    serial_number: str | None = None
    logistic_unit: str | None = None
    source_location: str | None = None
    destination_location: str | None = None
    source_stock_state: str | None = None
    destination_stock_state: str | None = None
    quantity: Decimal = Field(Decimal("0.00"), ge=0)
    unit: str = "UND"
    reference: str | None = None


class CountLine(BaseModel):
    """Single line in a physical count act."""

    model_config = ConfigDict(extra="ignore")

    location_code: str = "—"
    sku: str | None = None
    description: str = "—"
    lot_number: str | None = None
    expected_quantity: Decimal | None = Field(default=None, ge=0)
    first_count_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    recount_quantity: Decimal | None = Field(default=None, ge=0)
    final_count_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    difference_quantity: Decimal | None = None
    unit: str = "UND"
    status: str = "PENDING"
    observations: str | None = None


class DifferenceLine(BaseModel):
    """Single difference entry in an ADI document."""

    model_config = ConfigDict(extra="ignore")

    sku: str | None = None
    description: str = "—"
    lot_number: str | None = None
    recorded_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    final_count_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    difference_quantity: Decimal = Decimal("0.00")
    unit: str = "UND"
    classification: str = "UNKNOWN_CAUSE"
    unit_value: Decimal | None = Field(default=None, ge=0)
    economic_impact: Decimal | None = None


class TransferComparisonLine(BaseModel):
    """Per-line comparison of dispatched vs received quantities for CRT."""

    model_config = ConfigDict(extra="ignore")

    sku: str | None = None
    description: str = "—"
    lot_number: str | None = None
    dispatched_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    received_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    accepted_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    observed_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    rejected_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    shortage_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    overage_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    unit: str = "UND"

    @model_validator(mode="after")
    def validate_coherence(self) -> TransferComparisonLine:
        total = self.accepted_quantity + self.observed_quantity + self.rejected_quantity
        if total > self.received_quantity + Decimal("0.001"):
            raise ValueError(
                f"accepted+observed+rejected ({total}) cannot exceed received ({self.received_quantity})"
            )
        return self


class CountTeamMember(BaseModel):
    """Member of a physical count team."""

    model_config = ConfigDict(extra="ignore")

    name: str
    role: str = "COUNTER"
    area: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    device: str | None = None


class TransferItemLine(BaseModel):
    """Single item line in a TRA transfer order."""

    model_config = ConfigDict(extra="ignore")

    sku: str | None = None
    description: str = "—"
    lot_number: str | None = None
    logistic_unit: str | None = None
    requested_quantity: Decimal = Field(Decimal("0.00"), gt=0)
    unit: str = "UND"


# ---------------------------------------------------------------------------
# Document-specific context schemas
# ---------------------------------------------------------------------------


class InventoryEubContext(BaseModel):
    """Context for EUB — Location Label. ACTIVE_FOR_PREVIEW (PENDING formal approval)."""

    model_config = ConfigDict(extra="ignore")

    warehouse_name: str
    location_code: str
    location_status: str = "ACTIVE"
    zone_code: str | None = None
    aisle_code: str | None = None
    rack_code: str | None = None
    level_code: str | None = None
    position_code: str | None = None
    location_type: str | None = None
    capacity: Decimal | None = Field(default=None, ge=0)
    capacity_unit: str | None = None
    restrictions: list[str] = Field(default_factory=list)
    label_format: str = "A6"  # A6 | A5 | 100x150 | A4_SHEET
    observations: str | None = None


class InventoryPutContext(BaseModel):
    """Context for PUT — Putaway Order."""

    model_config = ConfigDict(extra="ignore")

    warehouse_name: str
    status: str = "PREVIEW"
    priority: str | None = None
    inbound_note_reference: str | None = None
    reception_reference: str | None = None
    sku: str | None = None
    description: str = "—"
    quantity: Decimal = Field(Decimal("0.00"), ge=0)
    unit: str = "UND"
    lot_number: str | None = None
    serial_number: str | None = None
    logistic_unit_code: str | None = None
    source_location: str | None = None
    suggested_location: str | None = None
    selection_reason: str | None = None
    restrictions: str | None = None
    responsible_user: str | None = None
    observations: str | None = None


class InventoryMovContext(BaseModel):
    """Context for MOV — Warehouse Movement."""

    model_config = ConfigDict(extra="ignore")

    warehouse_name: str
    movement_type: str = "INTERNAL_TRANSFER"
    status: str = "PREVIEW"
    movement_at: str | None = None
    related_operation_reference: str | None = None
    source_location: str | None = None
    destination_location: str | None = None
    source_stock_state: str | None = None
    destination_stock_state: str | None = None
    items: list[InventoryItemLine] = Field(default_factory=list)
    reason_code: str = "—"
    reason_detail: str | None = None
    responsible_user: str | None = None
    approver: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    observations: str | None = None
    # Reversal support
    is_reversal: bool = False
    original_movement_reference: str | None = None
    reversal_reason: str | None = None

    @model_validator(mode="after")
    def validate_items_required(self) -> InventoryMovContext:
        if not self.items:
            raise ValueError("MOV requires at least one item line")
        return self


class InventoryAjiContext(BaseModel):
    """Context for AJI — Inventory Adjustment Act."""

    model_config = ConfigDict(extra="ignore")

    warehouse_name: str
    status: str = "PREVIEW"
    adjustment_type: str = "POSITIVE_ADJUSTMENT"
    approval_status: str = "PREVIEW"
    location_code: str | None = None
    sku: str | None = None
    description: str = "—"
    lot_number: str | None = None
    serial_number: str | None = None
    stock_state: str | None = None
    unit: str = "UND"
    recorded_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    verified_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    adjustment_quantity: Decimal = Decimal("0.00")
    projected_quantity: Decimal | None = None
    # Economic impact — only shown when show_economic_impact=True
    show_economic_impact: bool = False
    unit_value: Decimal | None = Field(default=None, ge=0)
    economic_impact: Decimal | None = None
    reason: str
    root_cause: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    requested_by: str
    reviewer: str | None = None
    approver: str | None = None
    request_date: str | None = None
    observations: str | None = None

    @model_validator(mode="after")
    def validate_adjustment_coherence(self) -> InventoryAjiContext:
        computed = self.verified_quantity - self.recorded_quantity
        if abs(computed - self.adjustment_quantity) > Decimal("0.001"):
            raise ValueError(
                f"adjustment_quantity ({self.adjustment_quantity}) must equal "
                f"verified - recorded ({computed})"
            )
        if not self.reason:
            raise ValueError("AJI requires a non-empty reason")
        return self


class InventoryCntContext(BaseModel):
    """Context for CNT — Physical Count Act.
    blind_count_mode hides expected_quantity from CounterView templates.
    """

    model_config = ConfigDict(extra="ignore")

    warehouse_name: str
    count_type: str = "GENERAL_COUNT"
    status: str = "PREVIEW"
    zone_code: str | None = None
    scheduled_date: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    supervisor: str = "—"
    count_team: list[CountTeamMember] = Field(default_factory=list)
    count_lines: list[CountLine] = Field(default_factory=list)
    has_recount: bool = False
    blind_count_mode: bool = False  # If True, expected_quantity is NOT exposed
    evidence_references: list[str] = Field(default_factory=list)
    observations: str | None = None

    @model_validator(mode="after")
    def validate_team_and_lines(self) -> InventoryCntContext:
        if not self.count_lines:
            raise ValueError("CNT requires at least one count line")
        if not self.supervisor:
            raise ValueError("CNT requires a supervisor")
        return self

    def get_safe_context(self) -> dict[str, Any]:
        """Return context dict. If blind_count_mode, remove expected_quantity from all lines."""
        data = self.model_dump()
        if self.blind_count_mode:
            for line in data.get("count_lines", []):
                line["expected_quantity"] = None
                line["difference_quantity"] = None
        return data


class InventoryAdiContext(BaseModel):
    """Context for ADI — Inventory Difference Act. ACTIVE_FOR_PREVIEW (PENDING formal approval)."""

    model_config = ConfigDict(extra="ignore")

    warehouse_name: str
    count_reference: str = "—"
    investigation_status: str = "OPEN"
    location_code: str | None = None
    responsible_user: str = "—"
    differences: list[DifferenceLine] = Field(default_factory=list)
    show_economic_impact: bool = False
    total_economic_impact: str | None = None
    probable_cause: str | None = None
    investigation_detail: str | None = None
    recommendation: str | None = None
    proposed_adjustment: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    observations: str | None = None

    @model_validator(mode="after")
    def validate_differences_required(self) -> InventoryAdiContext:
        if not self.differences:
            raise ValueError("ADI requires at least one difference entry")
        return self


class InventoryTraContext(BaseModel):
    """Context for TRA — Inter-Warehouse Transfer Order."""

    model_config = ConfigDict(extra="ignore")

    source_warehouse_name: str
    destination_warehouse_name: str
    source_branch_name: str | None = None
    destination_branch_name: str | None = None
    status: str = "PREVIEW"
    priority: str | None = None
    requested_by: str = "—"
    requested_at: str | None = None
    planned_date: str | None = None
    approver: str | None = None
    reason: str
    carrier_name: str | None = None
    vehicle_plate: str | None = None
    route_reference: str | None = None
    items: list[TransferItemLine] = Field(default_factory=list)
    observations: str | None = None

    @model_validator(mode="after")
    def validate_warehouses_different(self) -> InventoryTraContext:
        if self.source_warehouse_name == self.destination_warehouse_name:
            raise ValueError(
                "TRA: source_warehouse_name and destination_warehouse_name must be different"
            )
        if not self.items:
            raise ValueError("TRA requires at least one item line")
        if not self.reason:
            raise ValueError("TRA requires a non-empty reason")
        return self


class InventoryCrtContext(BaseModel):
    """Context for CRT — Transfer Receipt Constancy. ACTIVE_FOR_PREVIEW (PENDING formal approval)."""

    model_config = ConfigDict(extra="ignore")

    source_warehouse_name: str
    destination_warehouse_name: str
    transfer_reference: str = "—"
    receiving_result: str = "PREVIEW"
    dispatched_date: str | None = None
    arrival_date: str | None = None
    reception_start: str | None = None
    reception_end: str | None = None
    received_by: str = "—"
    vehicle_plate: str | None = None
    seal_number: str | None = None
    comparison_items: list[TransferComparisonLine] = Field(default_factory=list)
    differences_summary: str | None = None
    pending_action: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    observations: str | None = None

    @model_validator(mode="after")
    def validate_crt_basics(self) -> InventoryCrtContext:
        if self.source_warehouse_name == self.destination_warehouse_name:
            raise ValueError("CRT: source and destination warehouses must be different")
        if not self.comparison_items:
            raise ValueError("CRT requires at least one comparison item")
        return self


# ---------------------------------------------------------------------------
# Inventory Document Package Manifest
# ---------------------------------------------------------------------------


class InventoryDocumentEntry(BaseModel):
    """Single document entry within a package manifest."""

    model_config = ConfigDict(extra="ignore")

    document_type_code: str
    template_key: str
    template_version: str = "1.0.0"
    required: bool = True
    included: bool = True
    status: str = "READY_FOR_PREVIEW"
    reason_if_missing: str | None = None
    render_status: str = "PENDING"
    filename_suggestion: str | None = None
    content_hash: str | None = None


class InventoryDocumentPackageManifest(BaseModel):
    """Manifest for an inventory document package."""

    model_config = ConfigDict(extra="ignore")

    manifest_version: str = "1.0.0"
    package_mode: str  # LOCATION | PUTAWAY | MOVEMENT | ADJUSTMENT | COUNT | TRANSFER | TRANSFER_RECEIPT
    package_status: str = "READY_FOR_PREVIEW"
    organization_name: str
    branch_name: str
    warehouse_name: str
    source_warehouse_name: str | None = None
    destination_warehouse_name: str | None = None
    related_operation_reference: str | None = None
    document_entries: list[InventoryDocumentEntry] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    package_status_detail: str = "INCOMPLETE"
    generated_at: str | None = None
    generated_by: str | None = None
    preview_mode: bool = True
    warnings: list[str] = Field(default_factory=list)
    correlation_id: str | None = None


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class InventoryQuantityValidator:
    """Validates quantity rules for inventory documents."""

    @staticmethod
    def validate_positive(qty: Decimal, field_name: str) -> None:
        if qty <= 0:
            raise ValueError(f"{field_name} must be greater than zero")

    @staticmethod
    def validate_non_negative(qty: Decimal, field_name: str) -> None:
        if qty < 0:
            raise ValueError(f"{field_name} must be >= 0")

    @staticmethod
    def validate_adjustment(
        recorded: Decimal, verified: Decimal, adjustment: Decimal
    ) -> None:
        computed = verified - recorded
        if abs(computed - adjustment) > Decimal("0.001"):
            raise ValueError(
                f"adjustment_quantity {adjustment} != verified - recorded ({computed})"
            )

    @staticmethod
    def validate_transfer_receipt(line: TransferComparisonLine) -> None:
        total = line.accepted_quantity + line.observed_quantity + line.rejected_quantity
        if total > line.received_quantity + Decimal("0.001"):
            raise ValueError(
                f"accepted+observed+rejected ({total}) > received ({line.received_quantity})"
            )


class InventoryAdjustmentValidator:
    """Computes and validates adjustment quantities."""

    @staticmethod
    def compute_adjustment(recorded: Decimal, verified: Decimal) -> Decimal:
        return verified - recorded

    @staticmethod
    def compute_projected(recorded: Decimal, adjustment: Decimal) -> Decimal:
        return recorded + adjustment


class TransferReceiptValidator:
    """Validates transfer receipt comparison lines."""

    @staticmethod
    def compute_shortage(dispatched: Decimal, received: Decimal) -> Decimal:
        diff = dispatched - received
        return max(diff, Decimal("0"))

    @staticmethod
    def compute_overage(dispatched: Decimal, received: Decimal) -> Decimal:
        diff = received - dispatched
        return max(diff, Decimal("0"))
