"""Pydantic v2 DTOs for Supplier Evaluation (Phase 033)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CriterionDefinitionCreate(BaseModel):
    criterion_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    criterion_group: str = Field(default="PRICE")
    scoring_method: str = Field(default="LOWER_IS_BETTER")
    weight: str = Field(..., description="Weight decimal percentage (e.g. '35.0000')")
    order_index: int = Field(default=1, ge=1)
    mandatory: bool = False
    disqualifying: bool = False
    minimum_score: Optional[str] = None
    maximum_score: str = "100.0000"
    source_type: str = "AUTOMATIC"
    evidence_required: bool = False
    manual_override_allowed: bool = True
    missing_data_policy: Optional[str] = "ZERO_SCORE"


class CriterionDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_version_id: UUID
    criterion_code: str
    name: str
    description: Optional[str] = None
    criterion_group: str
    scoring_method: str
    weight: Decimal
    order_index: int
    mandatory: bool
    disqualifying: bool
    minimum_score: Optional[Decimal] = None
    maximum_score: Decimal
    source_type: str
    evidence_required: bool
    manual_override_allowed: bool
    status: str


class TemplateVersionCreate(BaseModel):
    score_scale_min: str = "0.0000"
    score_scale_max: str = "100.0000"
    passing_score: Optional[str] = "60.0000"
    missing_data_policy: str = "ZERO_SCORE"
    tie_policy: str = "HIGHER_TECHNICAL_SCORE"
    award_policy: str = "BEST_OVERALL_SCORE"
    currency_policy: str = "SAME_CURRENCY_REQUIRED"
    criteria: List[CriterionDefinitionCreate]


class TemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    version_number: int
    status: str
    score_scale_min: Decimal
    score_scale_max: Decimal
    passing_score: Optional[Decimal] = None
    missing_data_policy: str
    tie_policy: str
    award_policy: str
    currency_policy: str
    engine_version: str
    content_hash: str
    effective_from: datetime
    criteria: List[CriterionDefinitionResponse] = []


class EvaluationTemplateCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    scope_type: str = "GENERAL"
    category_id: Optional[UUID] = None
    product_type: Optional[str] = None
    purchase_type: Optional[str] = None
    currency_policy: str = "SAME_CURRENCY_REQUIRED"
    award_policy: str = "BEST_OVERALL_SCORE"
    initial_version: Optional[TemplateVersionCreate] = None


class EvaluationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    scope_type: str
    status: str
    active_version_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class QuotationEvaluationCreate(BaseModel):
    quotation_round_id: UUID
    template_id: UUID
    evaluation_scope: str = "WHOLE_RESPONSE"
    award_policy: str = "BEST_OVERALL_SCORE"
    comparison_currency_code: str = "PEN"
    currency_conversion_policy: str = "SAME_CURRENCY_REQUIRED"


class CandidateSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: UUID
    supplier_business_partner_id: UUID
    eligible_line_count: int
    total_line_count: int
    coverage_percentage: Decimal
    comparable_total: Decimal
    currency_code: str
    price_score: Decimal
    delivery_score: Decimal
    technical_score: Decimal
    quality_score: Decimal
    compliance_score: Decimal
    commercial_terms_score: Decimal
    risk_score: Decimal
    weighted_total_score: Decimal
    rank: int
    disqualified: bool


class QuotationEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    quotation_round_id: UUID
    evaluation_number: int
    template_id: UUID
    template_version_id: UUID
    status: str
    evaluation_scope: str
    award_policy: str
    comparison_currency_code: Optional[str] = None
    active_run_id: Optional[UUID] = None
    active_decision_id: Optional[UUID] = None
    source_snapshot_hash: str
    created_at: datetime
    updated_at: datetime


class ManualScoreCreate(BaseModel):
    candidate_id: UUID
    criterion_id: UUID
    raw_score: str = Field(..., description="Decimal score e.g. '85.5000'")
    rubric_level_id: Optional[UUID] = None
    reason: str = Field(..., min_length=5)
    evidence_file_id: Optional[UUID] = None
    evidence_record_id: Optional[UUID] = None


class DecisionLineCreate(BaseModel):
    quotation_request_line_id: UUID
    selected_candidate_id: UUID
    selected_response_id: UUID
    selected_response_line_id: UUID
    selected_quantity: str
    selected_unit_id: UUID
    comparable_base_quantity: str
    selected_unit_price: str
    selected_currency_code: str = "PEN"
    selected_line_total: str
    rationale: str = Field(..., min_length=3)


class EvaluationDecisionCreate(BaseModel):
    decision_type: str = Field(default="RECOMMEND_SINGLE_SUPPLIER")
    selected_candidate_id: Optional[UUID] = None
    selected_response_id: Optional[UUID] = None
    rationale: str = Field(..., min_length=10)
    tie_resolution_reason: Optional[str] = None
    exceptions: Optional[Any] = None
    total_selected_amount: Optional[str] = None
    currency_code: Optional[str] = "PEN"
    decision_lines: Optional[List[DecisionLineCreate]] = None


class EvaluationDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_id: UUID
    evaluation_run_id: UUID
    decision_number: int
    decision_type: str
    status: str
    procurement_approval_status: str
    selected_candidate_id: Optional[UUID] = None
    selected_response_id: Optional[UUID] = None
    rationale: str
    total_selected_amount: Optional[Decimal] = None
    currency_code: Optional[str] = None
    decision_snapshot_hash: str
    recorded_at: datetime
