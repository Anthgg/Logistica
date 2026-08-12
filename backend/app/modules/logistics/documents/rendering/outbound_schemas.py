"""Pydantic v2 schemas for Outbound Document contexts and Package Manifests (Phase 018).

Covers: PED, ODS, PICK, PACK
Phase dependencies:
  - ProductSnapshot: PENDING_PHASE_023
  - UnitConversion: PENDING_PHASE_024
  - DestinationSnapshot: PENDING_PHASE_025 / PENDING_PHASE_026 / PENDING_PHASE_062
  - LotSerialSnapshot: PENDING_PHASE_046
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# 1. Snapshots
# ---------------------------------------------------------------------------


class DestinationSnapshot(BaseModel):
    """Destination snapshot (PENDING_PHASE_025 / PENDING_PHASE_026 / PENDING_PHASE_062)."""

    model_config = ConfigDict(extra="ignore")

    destination_type: str = "CUSTOMER"  # INTERNAL_AREA | CUSTOMER | PROJECT | BRANCH | WAREHOUSE | WORKSITE | RETURN_DESTINATION | OTHER
    business_partner_id: str | None = None
    name: str
    address: str
    district: str | None = None
    province: str | None = None
    department: str | None = None
    country: str = "PE"
    coordinates: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None  # Will be masked/hidden if sensitive read is False
    delivery_window: str | None = None
    instructions: str | None = None
    verification_state: str = "PENDING"


class ProductSnapshot(BaseModel):
    """Product catalog snapshot (PENDING_PHASE_023)."""

    model_config = ConfigDict(extra="ignore")

    product_id: str | None = None
    sku: str | None = None
    barcode: str | None = None
    description: str
    base_unit: str = "UND"
    tracking_type: str = "NONE"  # NONE | LOT | SERIAL | BOTH


class Dimensions(BaseModel):
    """Dimensions of a package (PENDING_PHASE_024 / PENDING_PHASE_046)."""

    model_config = ConfigDict(extra="ignore")

    length: Decimal = Field(..., gt=0)
    width: Decimal = Field(..., gt=0)
    height: Decimal = Field(..., gt=0)
    unit: str = "cm"  # cm | m | in


class Weight(BaseModel):
    """Weight of a package/unit (PENDING_PHASE_024 / PENDING_PHASE_046)."""

    model_config = ConfigDict(extra="ignore")

    value: Decimal = Field(..., gt=0)
    unit: str = "kg"  # kg | lb | g


class Volume(BaseModel):
    """Volume of a package (PENDING_PHASE_024 / PENDING_PHASE_046)."""

    model_config = ConfigDict(extra="ignore")

    value: Decimal = Field(..., gt=0)
    unit: str = "m3"  # m3 | L | ft3


# ---------------------------------------------------------------------------
# 2. Document lines and validators
# ---------------------------------------------------------------------------


class OutboundLineSnapshot(BaseModel):
    """Outbound document line representing quantities across the lifecycle."""

    model_config = ConfigDict(extra="ignore")

    line_number: int = 1
    product_snapshot: ProductSnapshot
    requested_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    approved_quantity: Decimal | None = Field(default=None, ge=0)
    allocated_quantity: Decimal | None = Field(default=None, ge=0)
    picked_quantity: Decimal | None = Field(default=None, ge=0)
    packed_quantity: Decimal | None = Field(default=None, ge=0)
    loaded_quantity: Decimal | None = Field(default=None, ge=0)
    unit: str = "UND"
    lot_number: str | None = None
    serial_numbers: list[str] = Field(default_factory=list)
    logistic_unit_codes: list[str] = Field(default_factory=list)
    stock_state: str | None = None
    preferred_lot: str | None = None
    minimum_expiration_date: str | None = None
    substitution_allowed: bool = False
    observations: str | None = None

    @model_validator(mode="after")
    def validate_quantities_coherence(self) -> OutboundLineSnapshot:
        # Validate that each step does not exceed the previous one
        req = self.requested_quantity
        app = self.approved_quantity if self.approved_quantity is not None else req
        alc = self.allocated_quantity if self.allocated_quantity is not None else app
        pik = self.picked_quantity if self.picked_quantity is not None else alc
        pak = self.packed_quantity if self.packed_quantity is not None else pik
        lod = self.loaded_quantity if self.loaded_quantity is not None else pak

        # Run checks
        if app > req:
            # Note: prompt says approved <= requested unless exception, we enforce <= here as baseline
            raise ValueError(f"Line {self.line_number}: approved_quantity ({app}) cannot exceed requested ({req})")
        if alc > app:
            raise ValueError(f"Line {self.line_number}: allocated_quantity ({alc}) cannot exceed approved ({app})")
        if pik > alc:
            raise ValueError(f"Line {self.line_number}: picked_quantity ({pik}) cannot exceed allocated ({alc})")
        if pak > pik:
            raise ValueError(f"Line {self.line_number}: packed_quantity ({pak}) cannot exceed picked ({pik})")
        if lod > pak:
            raise ValueError(f"Line {self.line_number}: loaded_quantity ({lod}) cannot exceed packed ({pak})")
        return self


# ---------------------------------------------------------------------------
# 3. Packing Unit
# ---------------------------------------------------------------------------


class PackingUnit(BaseModel):
    """Packing unit details (BOX, PALLET, Case, Container) for PACK / MAN documents."""

    model_config = ConfigDict(extra="ignore")

    logistic_unit_code: str
    logistic_unit_type: str = "BOX"  # ITEM | BOX | CASE | PALLET | CONTAINER | OTHER
    parent_unit_code: str | None = None
    package_number: int | None = None
    label_reference: str | None = None
    dimensions: Dimensions | None = None
    net_weight: Weight | None = None
    gross_weight: Weight | None = None
    volume: Volume | None = None
    internal_seal: str | None = None
    items: list[OutboundLineSnapshot] = Field(default_factory=list)
    destination_name: str | None = None
    evidence_references: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_weights(self) -> PackingUnit:
        if self.net_weight and self.gross_weight:
            if self.gross_weight.value < self.net_weight.value:
                raise ValueError("gross_weight cannot be less than net_weight")
            if self.gross_weight.unit != self.net_weight.unit:
                raise ValueError("gross_weight and net_weight must use the same unit")
        return self


# ---------------------------------------------------------------------------
# 4. Context schemas for PED, ODS, PICK, PACK
# ---------------------------------------------------------------------------


class OutboundDocumentContext(BaseModel):
    """Base Outbound Context containing general metadata."""

    model_config = ConfigDict(extra="ignore")

    document_type_code: str
    document_code: str | None = None
    document_status: str = "PREVIEW"
    template_version: str = "1.0.0"
    organization_name: str = "PROYECTO T1 LOGÍSTICA S.A.C."
    branch_name: str = "SEDE LIMA PRINCIPAL"
    warehouse: str
    destination_snapshot: DestinationSnapshot
    customer_or_requester_snapshot: DestinationSnapshot | None = None
    related_request_reference: str | None = None
    related_outbound_order_reference: str | None = None
    related_picking_reference: str | None = None
    related_packing_reference: str | None = None
    related_dispatch_reference: str | None = None
    generated_at: str | None = None
    issued_at: str | None = None
    required_at: str | None = None
    priority: str = "NORMAL"  # NORMAL | URGENT
    locale: str = "es"
    timezone: str = "America/Lima"
    responsible_users: list[str] = Field(default_factory=list)
    approval_chain: list[dict[str, Any]] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    observations: str | None = None
    QR_data: str | None = None
    signature_data: dict[str, Any] | None = None
    preview_mode: bool = True
    correlation_id: str | None = None


class OutboundPedContext(BaseModel):
    """Context schema for PED (Pedido de Salida)."""

    model_config = ConfigDict(extra="ignore")

    request_type: str = "INTERNAL_REQUEST"  # INTERNAL_REQUEST | CUSTOMER_ORDER | PROJECT_SUPPLY | BRANCH_REPLENISHMENT | WAREHOUSE_TRANSFER | RETURN_DISPATCH | OTHER
    requested_at: str | None = None
    requested_by: str
    destination_snapshot: DestinationSnapshot
    required_at: str
    priority: str = "NORMAL"
    warehouse: str
    items: list[OutboundLineSnapshot] = Field(default_factory=list)
    reason: str
    observations: str | None = None
    related_request_reference: str | None = None
    reviewer: str | None = None
    approver: str | None = None

    @model_validator(mode="after")
    def validate_ped_basics(self) -> OutboundPedContext:
        if not self.items:
            raise ValueError("PED requires at least one item line")
        if not self.reason:
            raise ValueError("PED requires a non-empty reason")
        for line in self.items:
            if line.requested_quantity <= 0:
                raise ValueError("Item quantity must be greater than zero")
        return self


class OutboundOdsContext(BaseModel):
    """Context schema for ODS (Orden de Salida)."""

    model_config = ConfigDict(extra="ignore")

    request_reference: str
    authorized_at: str | None = None
    authorized_by: str
    warehouse: str
    destination: DestinationSnapshot
    items: list[OutboundLineSnapshot] = Field(default_factory=list)
    release_status: str = "NOT_EVALUATED"  # NOT_EVALUATED | PENDING_STEP_UP | APPROVED_FOR_RELEASE | RELEASE_DENIED | EXPIRED | NOT_APPLICABLE
    responsible_users: list[str] = Field(default_factory=list)
    priority: str = "NORMAL"
    step_up_status: str | None = None
    policy_reference: str | None = None
    completed_at: str | None = None
    result: str | None = None
    observations: str | None = None

    @model_validator(mode="after")
    def validate_ods_basics(self) -> OutboundOdsContext:
        if not self.items:
            raise ValueError("ODS requires at least one item line")
        if not self.authorized_by:
            raise ValueError("ODS requires an authorizer")
        for line in self.items:
            app_qty = line.approved_quantity if line.approved_quantity is not None else line.requested_quantity
            if app_qty <= 0:
                raise ValueError("Approved quantity must be greater than zero")
        return self


class PickingLine(BaseModel):
    """Single line in a picking list."""

    model_config = ConfigDict(extra="ignore")

    sequence_order: int
    location_snapshot: dict[str, Any]
    product_snapshot: ProductSnapshot
    lot_number: str | None = None
    serial_numbers: list[str] = Field(default_factory=list)
    requested_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    assigned_quantity: Decimal | None = Field(default=None, ge=0)
    picked_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    shortage_quantity: Decimal | None = Field(default=None, ge=0)
    unit: str = "UND"
    scan_status: str = "NOT_STARTED"  # NOT_STARTED | LOCATION_SCANNED | PRODUCT_SCANNED | LOT_SCANNED | QUANTITY_CONFIRMED | COMPLETED | EXCEPTION
    exception_code: str | None = None  # STOCK_NOT_FOUND | LOCATION_EMPTY | etc.
    observations: str | None = None


class OutboundPickingContext(BaseModel):
    """Context schema for PICK (Lista de Picking)."""

    model_config = ConfigDict(extra="ignore")

    outbound_order_reference: str
    warehouse: str
    picking_method: str = "SINGLE_ORDER"  # SINGLE_ORDER | BATCH | WAVE | ZONE | CLUSTER | OTHER
    assigned_to: str
    picking_lines: list[PickingLine] = Field(default_factory=list)
    status: str = "PREVIEW"
    zone_code: str | None = None
    assigned_at: str | None = None
    supervisor: str = "—"
    observations: str | None = None

    # Calculated properties from picking lines (PickingProgressCalculator)
    total_lines: int = 0
    completed_lines: int = 0
    total_requested_quantity: Decimal = Decimal("0.00")
    total_picked_quantity: Decimal = Decimal("0.00")
    progress_percentage: Decimal = Decimal("0.0")
    lines_with_exception: int = 0
    shortage_quantity: Decimal = Decimal("0.00")

    @model_validator(mode="after")
    def calculate_progress(self) -> OutboundPickingContext:
        if not self.picking_lines:
            raise ValueError("PICK requires at least one picking line")

        # Run calculations
        self.total_lines = len(self.picking_lines)
        self.completed_lines = sum(1 for line in self.picking_lines if line.scan_status == "COMPLETED")
        self.lines_with_exception = sum(1 for line in self.picking_lines if line.exception_code is not None)

        self.total_requested_quantity = sum(line.requested_quantity for line in self.picking_lines)
        self.total_picked_quantity = sum(line.picked_quantity for line in self.picking_lines)

        self.shortage_quantity = sum(
            (line.requested_quantity - line.picked_quantity)
            for line in self.picking_lines
            if line.requested_quantity > line.picked_quantity
        )

        if self.total_requested_quantity > 0:
            pct = (self.total_picked_quantity / self.total_requested_quantity) * Decimal("100.0")
            self.progress_percentage = pct.quantize(Decimal("0.1"))
        else:
            self.progress_percentage = Decimal("0.0")

        return self


class OutboundPackContext(BaseModel):
    """Context schema for PACK (Packing List)."""

    model_config = ConfigDict(extra="ignore")

    outbound_order_reference: str
    warehouse: str
    destination: DestinationSnapshot
    packing_units: list[PackingUnit] = Field(default_factory=list)
    packed_by: str
    packing_status: str = "PREVIEW"
    started_at: str | None = None
    ended_at: str | None = None
    observations: str | None = None

    @model_validator(mode="after")
    def validate_packing_basics(self) -> OutboundPackContext:
        if not self.packing_units:
            raise ValueError("PACK requires at least one packing unit")
        # Run hierarchy check to prevent cycles
        PackageHierarchyValidator.validate_hierarchy(self.packing_units)
        return self


# ---------------------------------------------------------------------------
# 5. Hierarchy and quantities validators
# ---------------------------------------------------------------------------


class PackageHierarchyValidator:
    """Validator to detect cycles and validate unique parents in Packing Units."""

    @staticmethod
    def validate_hierarchy(units: list[PackingUnit]) -> None:
        codes = [u.logistic_unit_code for u in units]
        # Check uniqueness
        if len(codes) != len(set(codes)):
            raise ValueError("logistic_unit_code must be unique within the package")

        # Map to find parents
        parent_map: dict[str, str | None] = {u.logistic_unit_code: u.parent_unit_code for u in units}

        for code in parent_map:
            # Traverse up to find cycles
            visited = set()
            curr = code
            while curr is not None:
                if curr in visited:
                    raise ValueError(f"Cycle detected in packing hierarchy involving unit: {curr}")
                visited.add(curr)
                if curr not in parent_map:
                    # Parent is not declared in the list — that is fine, it's external or root
                    break
                curr = parent_map[curr]


class OutboundQuantityValidator:
    """Validator for verifying outbound quantity lifecycle rules."""

    @staticmethod
    def validate_non_negative(qty: Decimal, name: str) -> None:
        if qty < 0:
            raise ValueError(f"{name} cannot be negative")

    @staticmethod
    def validate_approved(requested: Decimal, approved: Decimal) -> None:
        if approved > requested:
            raise ValueError(f"approved ({approved}) cannot exceed requested ({requested})")
