from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

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


class ReasonRequest(CommandModel):
    reason: str = Field(min_length=3, max_length=1000)
    reason_code: str = Field(default="OTHER", min_length=2, max_length=60)


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Case ──────────────────────────────────────────────────────────────────────


class ReceptionDifferenceCaseCreate(CommandModel):
    inbound_receipt_id: UUID
    source_type: Literal["RECEIPT_CANDIDATES", "QUALITY_INSPECTION", "MANUAL_ENTRY", "SYSTEM_GENERATED"]
    description: str | None = Field(default=None, max_length=2000)


class ReceptionDifferenceCaseFromReceiptCreate(CommandModel):
    inbound_receipt_id: UUID
    receipt_revision_id: UUID | None = None
    source_type: Literal["RECEIPT_CANDIDATES", "QUALITY_INSPECTION", "MANUAL_ENTRY", "SYSTEM_GENERATED"]


class ReceptionDifferenceCaseUpdate(CommandModel):
    severity: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, max_length=2000)


class ReceptionDifferenceCaseResponse(ORMResponse):
    id: UUID; organization_id: UUID; branch_id: UUID; warehouse_id: UUID
    case_code: str; normalized_case_code: str
    inbound_receipt_id: UUID; inbound_receipt_revision_id: UUID
    unloading_operation_id: UUID | None; gate_check_in_id: UUID | None
    appointment_id: UUID | None; arrival_notice_id: UUID | None
    supplier_business_partner_id: UUID | None; supplier_snapshot: JsonObject
    carrier_business_partner_id: UUID | None; carrier_snapshot: JsonObject | None
    status: str; source_type: str; severity: str
    item_count: int; open_item_count: int; critical_item_count: int; evidence_count: int
    proposed_responsible_party_type: str | None; proposed_responsible_party_id: UUID | None
    responsibility_status: str
    active_revision_id: UUID | None; current_revision_number: int
    document_instance_id: UUID | None
    submitted_at: datetime | None; submitted_by: UUID | None
    reviewed_at: datetime | None; reviewed_by: UUID | None
    approved_at: datetime | None; approved_by: UUID | None
    issued_at: datetime | None; issued_by: UUID | None
    acknowledged_at: datetime | None; disputed_at: datetime | None
    closed_at: datetime | None; cancelled_at: datetime | None; cancellation_reason: str | None
    content_hash: str | None
    created_by: UUID; created_at: datetime; updated_at: datetime; row_version: int


class ReceptionDifferenceCaseSummary(BaseModel):
    id: UUID; case_code: str; inbound_receipt_id: UUID
    status: str; source_type: str; severity: str
    item_count: int; open_item_count: int; critical_item_count: int
    evidence_count: int; responsibility_status: str
    created_at: datetime; updated_at: datetime


class ReceptionDifferenceCaseDetail(ReceptionDifferenceCaseResponse):
    case_revisions: list[JsonObject]
    items: list[JsonObject]
    evidence_links: list[JsonObject]
    responsible_parties: list[JsonObject]
    reviews: list[JsonObject]
    approvals: list[JsonObject]
    acknowledgements: list[JsonObject]
    metrics: JsonObject | None


class ReceptionDifferenceCaseListResponse(BaseModel):
    items: list[ReceptionDifferenceCaseSummary]; page: int; page_size: int; total: int


class ReceptionDifferenceCaseCapabilities(BaseModel):
    case_id: UUID; actions: list[str]


class ReceptionDifferenceValidationResponse(BaseModel):
    case_id: UUID; is_valid: bool; blocking_errors: list[str]; warnings: list[str]
    missing_items: int; missing_evidence: int; pending_reviews: int
    pending_approvals: int; pending_acknowledgements: int
    can_submit: bool; can_approve: bool; can_issue: bool; can_cancel: bool
    validated_at: datetime; validation_hash: str


# ── Item ──────────────────────────────────────────────────────────────────────


class ReceptionDifferenceItemCreate(CommandModel):
    difference_type: str = Field(max_length=60)
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    product_id: UUID | None = None
    severity: str | None = Field(default=None, max_length=20)
    expected_quantity: str | None = None
    observed_quantity: str | None = None
    expected_unit_id: UUID | None = None
    observed_unit_id: UUID | None = None
    source_candidate_id: UUID | None = None
    purchase_order_id: UUID | None = None
    purchase_order_line_id: UUID | None = None
    expected_line_id: UUID | None = None
    received_line_id: UUID | None = None


class ReceptionDifferenceItemUpdate(CommandModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    severity: str | None = Field(default=None, max_length=20)


class ReceptionDifferenceItemResponse(ORMResponse):
    id: UUID; difference_case_id: UUID; case_revision_id: UUID; item_number: int
    source_candidate_id: UUID | None
    difference_type: str; category: str; severity: str; status: str
    purchase_order_id: UUID | None; purchase_order_line_id: UUID | None
    expected_line_id: UUID | None; received_line_id: UUID | None
    product_id: UUID | None; product_version_id: UUID | None
    sku_snapshot: str | None; product_name_snapshot: str | None
    expected_quantity: Decimal | None; expected_unit_id: UUID | None; expected_base_quantity: Decimal | None
    observed_quantity: Decimal | None; observed_unit_id: UUID | None; observed_base_quantity: Decimal | None
    difference_quantity: Decimal | None; difference_unit_id: UUID | None; difference_base_quantity: Decimal | None
    lot_observation_id: UUID | None; serial_observation_id: UUID | None; expiration_observation_id: UUID | None
    transport_document_id: UUID | None; gate_seal_inspection_id: UUID | None
    unloading_seal_opening_event_id: UUID | None
    title: str; description: str | None
    detection_source: str; detected_at: datetime
    detected_by_user_id: UUID | None; detected_by_service: str | None
    requires_evidence: bool; requires_responsibility: bool; requires_quality_review: bool
    future_quarantine_recommended: bool; future_claim_recommended: bool
    created_at: datetime; updated_at: datetime; row_version: int


class ReceptionDifferenceFormalizeCandidatesRequest(CommandModel):
    candidate_ids: list[UUID] = Field(min_length=1)
    case_id: UUID | None = None


# ── Damage ────────────────────────────────────────────────────────────────────


class ReceptionDamageDetailCreate(CommandModel):
    damage_scope: str = Field(max_length=40)
    damage_type: str = Field(max_length=40)
    affected_quantity: str | None = None
    unit_id: UUID | None = None
    packaging_level: str | None = Field(default=None, max_length=40)
    visual_description: str | None = Field(default=None, max_length=2000)
    functional_impact_declared: str | None = Field(default=None, max_length=2000)
    safety_concern: bool = False
    contamination_concern: bool = False
    temperature_concern: bool = False


# ── Evidence ──────────────────────────────────────────────────────────────────


class ReceptionDifferenceEvidenceLinkCreate(CommandModel):
    file_asset_id: UUID
    evidence_type: str = Field(max_length=40)
    difference_item_id: UUID | None = None
    description: str | None = Field(default=None, max_length=2000)
    classification: str | None = Field(default=None, max_length=40)
    captured_at: datetime | None = None


class ReceptionDifferenceEvidenceResponse(ORMResponse):
    id: UUID; difference_case_id: UUID; difference_item_id: UUID | None
    evidence_record_id: UUID | None; file_asset_id: UUID; file_version_id: UUID | None
    evidence_type: str; source_type: str; classification: str
    description: str | None; captured_at: datetime | None
    linked_at: datetime; linked_by: UUID
    content_hash: str | None; status: str
    created_at: datetime


# ── Responsible Party ─────────────────────────────────────────────────────────


class ReceptionDifferenceResponsiblePartyCreate(CommandModel):
    party_type: str = Field(max_length=40)
    business_partner_id: UUID | None = None
    user_id: UUID | None = None
    organization_unit_id: UUID | None = None
    responsibility_role: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=2000)
    allocation_percentage: str | None = None


class ReceptionDifferenceResponsiblePartyUpdate(CommandModel):
    responsibility_role: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=2000)
    allocation_percentage: str | None = None


class ReceptionDifferenceResponsibilityResponse(ORMResponse):
    id: UUID; difference_case_id: UUID; difference_item_id: UUID | None
    party_type: str; business_partner_id: UUID | None
    user_id: UUID | None; organization_unit_id: UUID | None
    responsible_snapshot: JsonObject
    responsibility_role: str; responsibility_status: str
    proposed_by: UUID; proposed_at: datetime
    reviewed_by: UUID | None; reviewed_at: datetime | None
    acknowledged_by: UUID | None; acknowledged_at: datetime | None
    disputed_by: UUID | None; disputed_at: datetime | None; dispute_reason: str | None
    allocation_percentage: Decimal | None; notes: str | None
    created_at: datetime


class ReceptionDifferenceResponsibilityReviewRequest(CommandModel):
    review_notes: str | None = Field(default=None, max_length=2000)


class ReceptionDifferenceResponsibilityDisputeRequest(CommandModel):
    dispute_reason: str = Field(min_length=3, max_length=2000)


# ── Review ────────────────────────────────────────────────────────────────────


class ReceptionDifferenceReviewCreate(CommandModel):
    review_type: str = Field(max_length=40)
    reviewer_user_id: UUID | None = None


class ReceptionDifferenceReviewCompleteRequest(CommandModel):
    findings: str | None = Field(default=None, max_length=2000)
    blocking_issues: list[str] | None = None
    requested_changes: list[str] | None = None
    recommendation: str | None = Field(default=None, max_length=2000)


class ReceptionDifferenceApprovalDecisionRequest(CommandModel):
    decision: Literal["APPROVE_FOR_ISSUE", "REQUEST_CHANGES", "REJECT_CASE", "REQUIRE_ADDITIONAL_REVIEW"]
    reason: str | None = Field(default=None, max_length=2000)


# ── Acknowledgement ───────────────────────────────────────────────────────────


class ReceptionDifferenceAcknowledgementCreate(CommandModel):
    party_type: str = Field(max_length=40)
    business_partner_id: UUID | None = None
    acknowledgement_type: str = Field(max_length=40)
    statement: str | None = Field(default=None, max_length=2000)
    source_channel: str | None = Field(default=None, max_length=40)


# ── Document / Package ────────────────────────────────────────────────────────


class ReceptionDifferenceDocumentResponse(BaseModel):
    case_id: UUID; document_instance_id: UUID; status: str
    issued_at: datetime; content_hash: str


class ReceptionDifferencePackageResponse(ORMResponse):
    id: UUID; case_id: UUID; status: str; file_asset_id: UUID | None; created_at: datetime


# ── Quality / Future ──────────────────────────────────────────────────────────


class QualityInspectionPreparationResponse(BaseModel):
    case_id: UUID
    items: list[JsonObject]
    products: list[JsonObject]
    categories: list[str]
    severity: str
    recommended_controls: list[str]


class FutureQuarantineRecommendationResponse(BaseModel):
    item_id: UUID
    product: JsonObject
    quantity: Decimal | None
    unit: JsonObject | None
    reason: str
    severity: str
    evidence: list[JsonObject]


class FutureClaimPreparationResponse(BaseModel):
    case_id: UUID
    supplier: JsonObject | None
    carrier: JsonObject | None
    responsible_parties: list[JsonObject]
    difference_types: list[str]
    evidence: list[JsonObject]
    acknowledgements: list[JsonObject]


# ── Integrity ─────────────────────────────────────────────────────────────────


class ReceptionDifferenceIntegrityResponse(BaseModel):
    case_id: UUID; status: str
    calculated_content_hash: str; stored_content_hash: str
