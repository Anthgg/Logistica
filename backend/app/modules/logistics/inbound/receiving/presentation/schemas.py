from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

DecimalQuantity = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
JsonObject = dict[str, JsonValue]


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_float(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("Use una cadena decimal; float no está permitido")
        return value


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InboundReceiptCreate(CommandModel):
    unloading_operation_id: UUID
    receipt_type: Literal["PURCHASE_ORDER_RECEIPT", "MULTI_PURCHASE_ORDER_RECEIPT", "AUTHORIZED_EXCEPTION", "LEGACY_IMPORT"] = "PURCHASE_ORDER_RECEIPT"
    scan_mode_policy: JsonObject = Field(default_factory=dict)


class InboundReceiptFromUnloadingCreate(InboundReceiptCreate):
    pass


class InboundReceiptResponse(ORMResponse):
    id: UUID; organization_id: UUID; branch_id: UUID; warehouse_id: UUID
    receipt_code: str; unloading_operation_id: UUID; dock_assignment_id: UUID; gate_check_in_id: UUID
    status: str; receipt_type: str; active_revision_id: UUID | None; current_revision_number: int
    total_expected_lines: int; total_received_lines: int; total_unresolved_scans: int; total_validation_errors: int; total_difference_candidates: int
    started_at: datetime | None; completed_at: datetime | None; completion_classification: str | None; content_hash: str | None; row_version: int


class InboundReceiptSummary(BaseModel):
    id: UUID; receipt_code: str; cpv_code: str | None; cit_code: str | None; purchase_order_codes: list[str]
    supplier_summary: JsonObject; warehouse_summary: JsonObject; dock_summary: JsonObject
    status: str; completion_classification: str | None; expected_line_count: int; received_line_count: int
    progress_percentage: Decimal; unresolved_scan_count: int; validation_error_count: int; difference_candidate_count: int
    started_at: datetime | None; completed_at: datetime | None; operator_summary: JsonObject | None
    integrity_status: str; capabilities: list[str]


class InboundReceiptDetail(InboundReceiptResponse):
    supplier_snapshot: JsonObject; carrier_snapshot: JsonObject | None; scan_mode_policy: JsonObject


class InboundReceiptListResponse(BaseModel):
    items: list[InboundReceiptSummary]; page: int; page_size: int; total: int


class InboundReceiptCapabilities(BaseModel):
    receipt_id: UUID; actions: list[str]


class ReasonRequest(CommandModel):
    reason: str = Field(min_length=3, max_length=1000)
    reason_code: str = Field(default="OTHER", min_length=2, max_length=60)
    row_version: int | None = Field(default=None, ge=1)


class InboundReceiptCompletionRequest(CommandModel):
    row_version: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=1000)


class InboundReceiptCompletionResponse(BaseModel):
    receipt_id: UUID; status: str; completion_classification: str; completed_at: datetime; content_hash: str; phase_040_ready: bool


class InboundReceiptExpectedLineResponse(ORMResponse):
    id: UUID; receipt_revision_id: UUID; purchase_order_id: UUID; purchase_order_line_id: UUID; product_id: UUID | None; line_number: int; sku_snapshot: str | None; product_name_snapshot: str
    ordered_quantity: Decimal; ordered_unit_id: UUID; ordered_base_quantity: Decimal; shipped_quantity: Decimal | None; shipped_base_quantity: Decimal | None; maximum_receivable_quantity: Decimal; status: str


class InboundReceivedLineResponse(ORMResponse):
    id: UUID; receipt_revision_id: UUID; expected_line_id: UUID | None; product_id: UUID | None; resolution_status: str; received_quantity: Decimal; received_unit_id: UUID; received_base_quantity: Decimal; validation_status: str; comparison_status: str; row_version: int


class ApplyReceivedQuantityRequest(CommandModel):
    quantity: DecimalQuantity; unit_id: UUID; scan_session_id: UUID | None = None
    lot_value: str | None = Field(default=None, max_length=160); serial_values: list[str] = Field(default_factory=list, max_length=500)
    manufacturing_date: date | None = None; expiration_date: date | None = None; condition: str | None = Field(default=None, max_length=50); row_version: int = Field(ge=1)


class InboundScanSessionCreate(CommandModel):
    scanner_type: Literal["KEYBOARD_WEDGE", "CAMERA", "MOBILE_CAMERA", "HANDHELD_TERMINAL", "APPROVED_HARDWARE_SDK", "MANUAL_ENTRY", "BATCH_IMPORT_AUTHORIZED"]
    station_id: UUID | None = None; device_reference: str | None = Field(default=None, max_length=200); client_session_reference: str | None = Field(default=None, max_length=120)


class InboundScanSessionResponse(ORMResponse):
    id: UUID; organization_id: UUID; inbound_receipt_id: UUID; receipt_revision_id: UUID; warehouse_id: UUID; scanner_type: str; status: str; operator_user_id: UUID; started_at: datetime; last_activity_at: datetime; completed_at: datetime | None; row_version: int


class InboundScanEventCreate(CommandModel):
    scan_session_id: UUID; client_scan_id: str = Field(min_length=1, max_length=120); client_sequence: int | None = Field(default=None, ge=0)
    raw_code: str = Field(min_length=1, max_length=512); symbology: str | None = Field(default=None, max_length=40)
    requested_quantity: DecimalQuantity = Decimal("1"); requested_unit_id: UUID | None = None
    scan_source: Literal["KEYBOARD_WEDGE", "CAMERA", "MOBILE_CAMERA", "HANDHELD_TERMINAL", "APPROVED_HARDWARE_SDK", "MANUAL_ENTRY", "BATCH_IMPORT_AUTHORIZED"]
    client_captured_at: datetime | None = None


class InboundScanEventBatchCreate(CommandModel):
    events: list[InboundScanEventCreate] = Field(min_length=1, max_length=500)


class InboundScanEventResponse(ORMResponse):
    id: UUID; inbound_receipt_id: UUID; scan_session_id: UUID; client_scan_id: str; server_sequence: int; normalized_code: str; code_hash: str; symbology: str; parse_status: str; resolution_status: str; resolved_product_id: UUID | None; resolved_expected_line_id: UUID | None; requested_quantity: Decimal; accepted_quantity: Decimal; accepted_base_quantity: Decimal; received_at: datetime; status: str


class InboundScanCompensationRequest(CommandModel):
    reason_code: Literal["DUPLICATE_SCAN", "WRONG_PRODUCT_SELECTED", "WRONG_QUANTITY", "WRONG_UNIT", "WRONG_LOT", "WRONG_SERIAL", "OPERATOR_ERROR", "SYSTEM_ERROR", "OTHER"]
    reason: str = Field(min_length=3, max_length=1000)


class ResolveInboundCodeRequest(CommandModel):
    raw_code: str = Field(min_length=1, max_length=512); symbology: str | None = Field(default=None, max_length=40)


class ResolveInboundCodeResponse(BaseModel):
    normalized_code: str; code_hash: str; parse_status: str; symbology: str; resolution_status: str; product_id: UUID | None; expected_line_id: UUID | None; candidate_product_ids: list[UUID] = Field(default_factory=list); parsed_elements: JsonObject


class ResolveUnresolvedScanRequest(CommandModel):
    product_id: UUID | None = None; expected_line_id: UUID | None = None; reason: str = Field(min_length=3, max_length=1000)


class InboundLotObservationCreate(CommandModel):
    lot_value: str = Field(min_length=1, max_length=160); quantity: DecimalQuantity; unit_id: UUID; manufacturing_date: date | None = None; expiration_date: date | None = None; source: str = Field(max_length=40)


class InboundLotObservationResponse(ORMResponse):
    id: UUID; inbound_receipt_id: UUID; received_line_id: UUID; product_id: UUID; normalized_lot_value: str; lot_hash: str; quantity: Decimal; base_quantity: Decimal; manufacturing_date: date | None; expiration_date: date | None; validation_status: str; captured_at: datetime


class InboundSerialObservationCreate(CommandModel):
    serial_value: str = Field(min_length=1, max_length=200); source: str = Field(max_length=40)


class InboundSerialObservationBatchCreate(CommandModel):
    serials: list[InboundSerialObservationCreate] = Field(min_length=1, max_length=500)


class InboundSerialObservationResponse(ORMResponse):
    id: UUID; inbound_receipt_id: UUID; received_line_id: UUID; product_id: UUID; normalized_serial_value: str; serial_hash: str; validation_status: str; duplicate_status: str; captured_at: datetime


class InboundExpirationObservationCreate(CommandModel):
    manufacturing_date: date | None = None; expiration_date: date; source: str = Field(max_length=40)

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.manufacturing_date and self.expiration_date < self.manufacturing_date:
            raise ValueError("expiration_date no puede ser anterior a manufacturing_date")
        return self


class InboundExpirationObservationResponse(ORMResponse):
    id: UUID; inbound_receipt_id: UUID; received_line_id: UUID; product_id: UUID; manufacturing_date: date | None; expiration_date: date; validation_status: str; captured_at: datetime


class ReceptionDifferenceCandidateResponse(ORMResponse):
    id: UUID; inbound_receipt_id: UUID; candidate_type: str; severity: str; expected_value: JsonObject | None; observed_value: JsonObject | None; variance_quantity: Decimal | None; status: str; detected_at: datetime


class InboundReceiptValidationResponse(BaseModel):
    validation_status: str; blocking_errors: list[str]; warnings: list[str]; unresolved_scans: int; incomplete_lines: int; over_received_lines: int; under_received_lines: int; identifier_errors: int; expiration_errors: int; difference_candidates: int; completion_options: list[str]; server_time: datetime; validation_hash: str


class InboundReceiptProgressResponse(BaseModel):
    receipt_id: UUID; expected_line_count: int; started_line_count: int; completed_line_count: int; ordered_base_total: Decimal; shipped_base_total: Decimal | None; received_base_total: Decimal; unresolved_scan_count: int; validation_error_count: int; warning_count: int; difference_candidate_count: int; scan_event_count: int; compensated_scan_count: int; progress_percentage: Decimal; data_quality_status: str; calculated_at: datetime; projection_version: int


class InboundReceiptComparisonResponse(BaseModel):
    receipt_id: UUID; lines: list[JsonObject]; completion_classification: str | None


class ReceptionDifferencePreparationResponse(BaseModel):
    inbound_receipt_id: UUID; receipt_code: str; receipt_revision_id: UUID; warehouse_id: UUID; supplier_summary: JsonObject; carrier_summary: JsonObject | None; unloading_operation_id: UUID; purchase_order_references: list[JsonObject]; expected_lines: list[JsonObject]; received_lines: list[JsonObject]; comparison_results: list[JsonObject]; candidates: list[JsonObject]; validation_summary: JsonObject; completion_snapshot_hash: str | None; future_capabilities: list[str]


class InboundReceiptIntegrityResponse(BaseModel):
    receipt_id: UUID; status: str; hashes: dict[str, str]; calculated_content_hash: str; stored_content_hash: str | None; canonicalization_version: str = "1"
