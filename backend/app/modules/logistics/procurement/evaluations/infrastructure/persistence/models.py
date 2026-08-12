"""SQLAlchemy 2 ORM Models for Supplier Evaluation (Phase 033)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Dialect-agnostic JSON type
JSONType = JSONB().with_variant(Text, "sqlite")


class SupplierEvaluationTemplateModel(Base):
    __tablename__ = "supplier_evaluation_templates"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERAL")
    category_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    purchase_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="SAME_CURRENCY_REQUIRED")
    award_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="BEST_OVERALL_SCORE")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    versions = relationship("SupplierEvaluationTemplateVersionModel", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_code", name="uq_eval_template_org_code"),
    )


class SupplierEvaluationTemplateVersionModel(Base):
    __tablename__ = "supplier_evaluation_template_versions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supplier_evaluation_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    score_scale_min: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    score_scale_max: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("100.0000"))
    passing_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    minimum_supplier_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    missing_data_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="ZERO_SCORE")
    tie_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="HIGHER_TECHNICAL_SCORE")
    award_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="BEST_OVERALL_SCORE")
    currency_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="SAME_CURRENCY_REQUIRED")
    rounding_scale: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    rounding_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="HALF_UP")
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    validated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    template = relationship("SupplierEvaluationTemplateModel", back_populates="versions")
    criteria = relationship("EvaluationCriterionDefinitionModel", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("template_id", "version_number", name="uq_eval_version_number"),
    )


class EvaluationCriterionDefinitionModel(Base):
    __tablename__ = "evaluation_criterion_definitions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_version_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("supplier_evaluation_template_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterion_group: Mapped[str] = mapped_column(String(50), nullable=False)
    scoring_method: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disqualifying: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    minimum_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    maximum_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("100.0000"))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="AUTOMATIC")
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_override_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    missing_data_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    normalization_parameters: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    version = relationship("SupplierEvaluationTemplateVersionModel", back_populates="criteria")


class EvaluationRubricModel(Base):
    __tablename__ = "evaluation_rubrics"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scale_min: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    scale_max: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("100.0000"))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    levels = relationship("EvaluationRubricLevelModel", back_populates="rubric", cascade="all, delete-orphan")


class EvaluationRubricLevelModel(Base):
    __tablename__ = "evaluation_rubric_levels"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rubric_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("evaluation_rubrics.id", ondelete="CASCADE"), nullable=False, index=True)
    level_code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    evidence_requirement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    rubric = relationship("EvaluationRubricModel", back_populates="levels")


class QuotationEvaluationModel(Base):
    __tablename__ = "quotation_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    quotation_round_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    evaluation_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    template_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    template_version_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    evaluation_scope: Mapped[str] = mapped_column(String(50), nullable=False, default="WHOLE_RESPONSE")
    award_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="BEST_OVERALL_SCORE")
    comparison_currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    currency_conversion_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="SAME_CURRENCY_REQUIRED")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    calculated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    decision_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_recorded_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    active_run_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    active_decision_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    source_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("quotation_round_id", "evaluation_number", name="uq_eval_round_number"),
    )


class QuotationEvaluationCandidateModel(Base):
    __tablename__ = "quotation_evaluation_candidates"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_business_partner_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    invitation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    response_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    response_revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supplier_snapshot: Mapped[Any] = mapped_column(JSONType, nullable=False)
    response_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    eligibility_status: Mapped[str] = mapped_column(String(50), nullable=False, default="ELIGIBLE")
    eligibility_reasons: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    disqualification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_DISQUALIFIED")
    disqualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    late_response: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    completeness_status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLETE")
    technical_compliance_status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLIANT")
    document_compliance_status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLIANT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class QuotationEvaluationRunModel(Base):
    __tablename__ = "quotation_evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    template_version_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLETED")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ranked_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("evaluation_id", "run_number", name="uq_eval_run_number"),
    )


class QuotationCriterionScoreModel(Base):
    __tablename__ = "quotation_criterion_scores"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    criterion_definition_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    criterion_code: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    normalized_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    weight_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    weighted_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    scoring_method: Mapped[str] = mapped_column(String(50), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="AUTOMATIC")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_file_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    evidence_record_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    calculation_details: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manually_entered_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    manually_entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    override_of_score_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "candidate_id", "criterion_definition_id", name="uq_eval_run_cand_crit"),
    )


class ManualEvaluationScoreModel(Base):
    __tablename__ = "manual_evaluation_scores"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    criterion_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    raw_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    normalized_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    rubric_level_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_file_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    evidence_record_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    entered_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SUBMITTED")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_score_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


class EvaluationScoreOverrideModel(Base):
    __tablename__ = "evaluation_score_overrides"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    criterion_score_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    original_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    proposed_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="REQUESTED")
    requested_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QuotationLineEvaluationModel(Base):
    __tablename__ = "quotation_line_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    quotation_request_line_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    response_line_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    eligibility_status: Mapped[str] = mapped_column(String(50), nullable=False, default="ELIGIBLE")
    coverage_ratio: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("1.0000"))
    comparable_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    comparable_unit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    comparable_unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    comparable_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    price_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    delivery_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    technical_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    compliance_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    total_weighted_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tie_group_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    warnings: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    disqualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class QuotationCandidateEvaluationSummaryModel(Base):
    __tablename__ = "quotation_candidate_evaluation_summaries"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    eligible_line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_percentage: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("100.0000"))
    comparable_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    price_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    delivery_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    technical_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    compliance_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    commercial_terms_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    weighted_total_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tie_group_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    disqualified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    warnings: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "candidate_id", name="uq_eval_summary_cand"),
    )


class TechnicalComplianceAssessmentModel(Base):
    __tablename__ = "technical_compliance_assessments"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    request_line_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    response_line_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    compliance_status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLIANT")
    mandatory_requirements_met: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mandatory_requirements_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    optional_requirements_met: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    optional_requirements_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deviation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_deviation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("100.0000"))
    assessed_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    evidence_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SupplierQualitySnapshotModel(Base):
    __tablename__ = "supplier_quality_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, default="LOGISTICS_QUALITY_REGISTRY")
    source_period: Mapped[str] = mapped_column(String(50), nullable=False, default="LAST_12_MONTHS")
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, default="ACCEPTANCE_RATE")
    metric_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("100.0000"))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="VERIFIED")
    evidence_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SupplierRiskSnapshotModel(Base):
    __tablename__ = "supplier_risk_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    source_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    supplier_status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    block_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_BLOCKED")
    compliance_risk: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    document_risk: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    delivery_history_risk: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    quality_history_risk: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    operational_risk: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    source_references: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    evidence_references: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    total_risk_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    risk_model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class EvaluationExchangeRateSnapshotModel(Base):
    __tablename__ = "evaluation_exchange_rate_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    rate: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, default="SUNAT_OFFICIAL")
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    source_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    captured_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(50), nullable=False, default="APPROVED")
    approved_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class EvaluationConflictOfInterestDeclarationModel(Base):
    __tablename__ = "evaluation_conflict_of_interest_declarations"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    evaluator_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    declaration_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NO_CONFLICT")
    declared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    relationship_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(50), nullable=False, default="RESOLVED")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class QuotationEvaluationDecisionModel(Base):
    __tablename__ = "quotation_evaluation_decisions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    decision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    decision_type: Mapped[str] = mapped_column(String(50), nullable=False, default="RECOMMEND_SINGLE_SUPPLIER")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="RECORDED")
    procurement_approval_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING_PHASE_035")
    selected_candidate_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    selected_response_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    tie_resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    exceptions: Mapped[Any | None] = mapped_column(JSONType, nullable=True)
    total_selected_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    decision_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    supersedes_decision_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    superseded_by_decision_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    decision_lines = relationship("QuotationEvaluationDecisionLineModel", back_populates="decision", cascade="all, delete-orphan")


class QuotationEvaluationDecisionLineModel(Base):
    __tablename__ = "quotation_evaluation_decision_lines"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotation_evaluation_decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    quotation_request_line_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    selected_candidate_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    selected_response_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    selected_response_line_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    selected_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    selected_unit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    comparable_base_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    selected_unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    selected_currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    selected_line_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SELECTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    decision = relationship("QuotationEvaluationDecisionModel", back_populates="decision_lines")


class EvaluationExportJobModel(Base):
    __tablename__ = "evaluation_export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    export_format: Mapped[str] = mapped_column(String(10), nullable=False, default="PDF")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLETED")
    file_asset_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
