"""Phase 041 persistence. Quality inspection plans, versions, scopes, controls, tolerances, sampling, certificates, conditions, reference files."""

from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.database.base import Base

QTY = {"precision": 38, "scale": 18}


class QualityInspectionPlanModel(Base):
    __tablename__ = "quality_inspection_plans"
    __table_args__ = (
        UniqueConstraint("organization_id", "plan_code", name="uq_qip_org_code"),
        Index("ix_qip_org", "organization_id"),
        Index("ix_qip_family", "plan_family"),
        Index("ix_qip_status", "status"),
        Index("ix_qip_active_version", "active_version_id"),
        Index("ix_qip_updated", "updated_at"),
        CheckConstraint("row_version >= 1", name="ck_qip_row_version"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    plan_code = Column(String(80), nullable=False)
    plan_name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    plan_family = Column(String(40), nullable=False)
    status = Column(String(30), nullable=False, default="DRAFT")
    current_version_number = Column(Integer, nullable=False, default=0)
    active_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    is_global = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSONB, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class QualityInspectionPlanVersionModel(Base):
    __tablename__ = "quality_inspection_plan_versions"
    __table_args__ = (
        UniqueConstraint("plan_id", "version_number", name="uq_qip_version_number"),
        Index("ix_qip_ver_plan", "plan_id"),
        Index("ix_qip_ver_status", "status"),
        Index("ix_qip_ver_number", "version_number"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False)
    version_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="DRAFT")
    change_summary = Column(Text, nullable=True)
    plan_snapshot = Column(JSONB, nullable=True)
    content_hash = Column(String(64), nullable=True)
    validation_errors = Column(JSONB, nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    activated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)
    retired_by = Column(PG_UUID(as_uuid=True), nullable=True)
    scheduled_activation_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class QualityPlanScopeModel(Base):
    __tablename__ = "quality_plan_scopes"
    __table_args__ = (
        UniqueConstraint("plan_id", "scope_type", "scope_product_id", "scope_category_id", "scope_warehouse_id", "scope_branch_id", name="uq_qip_scope_unique"),
        Index("ix_qip_scope_plan", "plan_id"),
        Index("ix_qip_scope_product", "scope_product_id"),
        Index("ix_qip_scope_category", "scope_category_id"),
        Index("ix_qip_scope_warehouse", "scope_warehouse_id"),
        Index("ix_qip_scope_branch", "scope_branch_id"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False)
    version_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plan_versions.id", ondelete="RESTRICT"), nullable=False)
    scope_type = Column(String(30), nullable=False)
    scope_product_id = Column(PG_UUID(as_uuid=True), nullable=True)
    scope_product_name = Column(String(300), nullable=True)
    scope_category_id = Column(PG_UUID(as_uuid=True), nullable=True)
    scope_category_name = Column(String(200), nullable=True)
    scope_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    scope_warehouse_name = Column(String(200), nullable=True)
    scope_branch_id = Column(PG_UUID(as_uuid=True), nullable=True)
    scope_branch_name = Column(String(200), nullable=True)
    resolution_specificity = Column(String(40), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QualityControlDefinitionModel(Base):
    __tablename__ = "quality_control_definitions"
    __table_args__ = (
        Index("ix_qcd_plan", "plan_id"),
        Index("ix_qcd_version", "version_id"),
        Index("ix_qcd_type", "control_type"),
        Index("ix_qcd_scope", "scope_id"),
        CheckConstraint("display_order >= 0", name="ck_qcd_display_order"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False)
    version_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plan_versions.id", ondelete="RESTRICT"), nullable=False)
    scope_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_plan_scopes.id", ondelete="SET NULL"), nullable=True)
    control_type = Column(String(60), nullable=False)
    control_code = Column(String(80), nullable=False)
    control_name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    is_blocking = Column(Boolean, nullable=False, default=False)
    applies_to_all_units = Column(Boolean, nullable=False, default=False)
    applies_to_sample = Column(Boolean, nullable=False, default=True)
    configuration_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class QualityToleranceDefinitionModel(Base):
    __tablename__ = "quality_tolerance_definitions"
    __table_args__ = (
        Index("ix_qtd_control", "control_id"),
        Index("ix_qtd_type", "tolerance_type"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    control_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False)
    tolerance_type = Column(String(40), nullable=False)
    min_value = Column(Numeric(**QTY), nullable=True)
    max_value = Column(Numeric(**QTY), nullable=True)
    target_value = Column(Numeric(**QTY), nullable=True)
    absolute_deviation = Column(Numeric(**QTY), nullable=True)
    percentage_deviation = Column(Numeric(**QTY), nullable=True)
    valid_options = Column(JSONB, nullable=True)
    default_value = Column(JSONB, nullable=True)
    unit_code = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QualitySamplingPlanModel(Base):
    __tablename__ = "quality_sampling_plans"
    __table_args__ = (
        Index("ix_qsp_control", "control_id"),
        Index("ix_qsp_type", "sampling_type"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    control_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False)
    sampling_type = Column(String(40), nullable=False)
    fixed_count = Column(Integer, nullable=True)
    percentage = Column(Numeric(**QTY), nullable=True)
    minimum_count = Column(Integer, nullable=True)
    package_level = Column(String(40), nullable=True)
    lot_level = Column(String(40), nullable=True)
    custom_formula = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QualityCertificateRequirementModel(Base):
    __tablename__ = "quality_certificate_requirements"
    __table_args__ = (
        Index("ix_qcr_control", "control_id"),
        Index("ix_qcr_type", "certificate_type"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    control_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False)
    certificate_type = Column(String(60), nullable=False)
    document_type_id = Column(PG_UUID(as_uuid=True), nullable=True)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    validity_days = Column(Integer, nullable=True)
    requires_signature = Column(Boolean, nullable=False, default=False)
    metadata_schema = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QualityControlApplicabilityConditionModel(Base):
    __tablename__ = "quality_control_applicability_conditions"
    __table_args__ = (
        Index("ix_qcac_control", "control_id"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    control_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False)
    condition_type = Column(String(40), nullable=False)
    condition_field = Column(String(120), nullable=False)
    condition_operator = Column(String(20), nullable=False)
    condition_value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class QualityPlanReferenceFileModel(Base):
    __tablename__ = "quality_plan_reference_files"
    __table_args__ = (
        Index("ix_qprf_plan", "plan_id"),
        Index("ix_qprf_version", "version_id"),
        Index("ix_qprf_file", "file_asset_id"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False)
    version_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plan_versions.id", ondelete="SET NULL"), nullable=True)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=False)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    reference_type = Column(String(40), nullable=False, default="MANUAL")
    description = Column(Text, nullable=True)
    linked_by = Column(PG_UUID(as_uuid=True), nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content_hash = Column(String(64), nullable=True)


class QualityPlanUsageProjectionModel(Base):
    __tablename__ = "quality_plan_usage_projection"
    plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("quality_inspection_plans.id", ondelete="CASCADE"), primary_key=True)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False)
    total_scopes = Column(Integer, nullable=False, default=0)
    total_controls = Column(Integer, nullable=False, default=0)
    mandatory_controls = Column(Integer, nullable=False, default=0)
    blocking_controls = Column(Integer, nullable=False, default=0)
    total_tolerances = Column(Integer, nullable=False, default=0)
    total_sampling_plans = Column(Integer, nullable=False, default=0)
    total_certificate_requirements = Column(Integer, nullable=False, default=0)
    total_reference_files = Column(Integer, nullable=False, default=0)
    resolved_for_products = Column(Integer, nullable=False, default=0)
    resolved_for_categories = Column(Integer, nullable=False, default=0)
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


PHASE_041_TABLES = (
    "quality_inspection_plans",
    "quality_inspection_plan_versions",
    "quality_plan_scopes",
    "quality_control_definitions",
    "quality_tolerance_definitions",
    "quality_sampling_plans",
    "quality_certificate_requirements",
    "quality_control_applicability_conditions",
    "quality_plan_reference_files",
    "quality_plan_usage_projection",
)
