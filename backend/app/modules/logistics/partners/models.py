"""SQLAlchemy ORM models for Phase 025 — Business Partners Master Data."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class BusinessPartnerModel(Base):
    __tablename__ = "business_partners"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    partner_code = Column(String(30), nullable=False)
    normalized_partner_code = Column(String(30), nullable=False, index=True)
    legal_name = Column(String(200), nullable=False, index=True)
    trade_name = Column(String(200), nullable=True)
    person_type = Column(String(20), nullable=False, default="LEGAL_ENTITY")
    country_code = Column(String(3), nullable=False, default="PE")
    status = Column(String(20), nullable=False, default="DRAFT")
    lifecycle_status = Column(String(20), nullable=False, default="ACTIVE")
    risk_status = Column(String(20), nullable=False, default="NOT_EVALUATED")
    compliance_status = Column(String(20), nullable=False, default="NOT_EVALUATED")
    active_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    row_version = Column(Integer, nullable=False, default=1)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    archived_by = Column(PG_UUID(as_uuid=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    roles = relationship("BusinessPartnerRoleModel", back_populates="partner", cascade="all, delete-orphan")
    identifiers = relationship("BusinessPartnerIdentifierModel", back_populates="partner", cascade="all, delete-orphan")
    addresses = relationship("BusinessPartnerAddressModel", back_populates="partner", cascade="all, delete-orphan")
    contacts = relationship("BusinessPartnerContactModel", back_populates="partner", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_partner_code", name="uq_partners_org_norm_code"),
    )


class BusinessPartnerVersionModel(Base):
    __tablename__ = "business_partner_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    legal_name = Column(String(200), nullable=False)
    trade_name = Column(String(200), nullable=True)
    person_type = Column(String(20), nullable=False)
    snapshot_data = Column(JSONB, nullable=False)
    content_hash = Column(String(64), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("business_partner_id", "version", name="uq_partner_versions_partner_ver"),
    )


class BusinessPartnerAliasModel(Base):
    __tablename__ = "business_partner_aliases"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    alias_type = Column(String(30), nullable=False)
    previous_value = Column(String(200), nullable=False)
    current_value = Column(String(200), nullable=False)
    reason = Column(Text, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BusinessPartnerRoleModel(Base):
    __tablename__ = "business_partner_roles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    role_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    valid_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    partner = relationship("BusinessPartnerModel", back_populates="roles")
    supplier_profile = relationship("SupplierProfileModel", uselist=False, back_populates="role", cascade="all, delete-orphan")
    customer_profile = relationship("CustomerProfileModel", uselist=False, back_populates="role", cascade="all, delete-orphan")
    carrier_profile = relationship("CarrierProfileModel", uselist=False, back_populates="role", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("business_partner_id", "role_type", name="uq_partner_roles_partner_role"),
    )


class SupplierProfileModel(Base):
    __tablename__ = "supplier_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_role_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    supplier_category = Column(String(50), nullable=True)
    supplies_goods = Column(Boolean, nullable=False, default=True)
    supplies_services = Column(Boolean, nullable=False, default=False)
    quality_inspection_required = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    role = relationship("BusinessPartnerRoleModel", back_populates="supplier_profile")


class CustomerProfileModel(Base):
    __tablename__ = "customer_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_role_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    customer_type = Column(String(50), nullable=False, default="STANDARD")
    requires_delivery_appointment = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    role = relationship("BusinessPartnerRoleModel", back_populates="customer_profile")


class CarrierProfileModel(Base):
    __tablename__ = "carrier_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_role_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    transport_mode = Column(String(30), nullable=False, default="ROAD")
    own_fleet = Column(Boolean, nullable=False, default=True)
    third_party_fleet = Column(Boolean, nullable=False, default=False)
    refrigerated_transport = Column(Boolean, nullable=False, default=False)
    hazardous_authorized = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    role = relationship("BusinessPartnerRoleModel", back_populates="carrier_profile")


class BusinessPartnerIdentifierModel(Base):
    __tablename__ = "business_partner_identifiers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    identifier_type = Column(String(30), nullable=False)
    country_code = Column(String(3), nullable=False, default="PE")
    value = Column(String(50), nullable=False)
    normalized_value = Column(String(50), nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=True)
    verification_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    partner = relationship("BusinessPartnerModel", back_populates="identifiers")

    __table_args__ = (
        UniqueConstraint("organization_id", "identifier_type", "normalized_value", name="uq_partner_identifiers_org_type_val"),
    )


class BusinessPartnerAddressModel(Base):
    __tablename__ = "business_partner_addresses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type = Column(String(30), nullable=False, default="FISCAL")
    label = Column(String(100), nullable=True)
    address_line_1 = Column(String(200), nullable=False)
    address_line_2 = Column(String(200), nullable=True)
    district = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country_code = Column(String(3), nullable=False, default="PE")
    is_primary = Column(Boolean, nullable=False, default=True)
    is_delivery_address = Column(Boolean, nullable=False, default=False)
    is_billing_address = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    partner = relationship("BusinessPartnerModel", back_populates="addresses")


class BusinessPartnerContactModel(Base):
    __tablename__ = "business_partner_contacts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type = Column(String(30), nullable=False, default="GENERAL")
    full_name = Column(String(150), nullable=False)
    position_title = Column(String(100), nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    partner = relationship("BusinessPartnerModel", back_populates="contacts")


class BusinessPartnerOperationalSettingsModel(Base):
    __tablename__ = "business_partner_operational_settings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, unique=True)
    default_currency_code = Column(String(3), nullable=False, default="PEN")
    default_language = Column(String(10), nullable=False, default="es")
    default_timezone = Column(String(50), nullable=False, default="America/Lima")
    requires_appointment = Column(Boolean, nullable=False, default=False)
    receiving_hours_notes = Column(Text, nullable=True)
    delivery_hours_notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class BusinessPartnerEvaluationTemplateModel(Base):
    __tablename__ = "business_partner_evaluation_templates"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    role_type = Column(String(30), nullable=False)
    code = Column(String(30), nullable=False)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False, default="1.0.0")
    criteria_schema = Column(JSONB, nullable=False)
    score_scale = Column(Numeric(5, 2), nullable=False, default=Decimal("100.00"))
    passing_score = Column(Numeric(5, 2), nullable=False, default=Decimal("70.00"))
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "code", "version", name="uq_eval_templates_org_code_ver"),
    )


class BusinessPartnerEvaluationModel(Base):
    __tablename__ = "business_partner_evaluations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    role_type = Column(String(30), nullable=False)
    evaluation_type = Column(String(30), nullable=False, default="PERIODIC")
    total_score = Column(Numeric(5, 2), nullable=False)
    risk_level = Column(String(20), nullable=False, default="LOW")
    status = Column(String(20), nullable=False, default="APPROVED")
    summary = Column(Text, nullable=True)
    evaluator_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    criteria = relationship("BusinessPartnerEvaluationCriterionModel", back_populates="evaluation", cascade="all, delete-orphan")


class BusinessPartnerEvaluationCriterionModel(Base):
    __tablename__ = "business_partner_evaluation_criteria"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partner_evaluations.id", ondelete="CASCADE"), nullable=False)
    criterion_code = Column(String(50), nullable=False)
    criterion_name = Column(String(100), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    weighted_score = Column(Numeric(5, 2), nullable=False)
    observations = Column(Text, nullable=True)

    evaluation = relationship("BusinessPartnerEvaluationModel", back_populates="criteria")


class BusinessPartnerDocumentRequirementModel(Base):
    __tablename__ = "business_partner_document_requirements"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    role_type = Column(String(30), nullable=False)
    document_type = Column(String(50), nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    blocking = Column(Boolean, nullable=False, default=False)
    requires_expiration = Column(Boolean, nullable=False, default=True)
    warning_days_before_expiration = Column(Integer, nullable=False, default=30)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "role_type", "document_type", name="uq_doc_reqs_org_role_doctype"),
    )


class BusinessPartnerDocumentModel(Base):
    __tablename__ = "business_partner_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    role_type = Column(String(30), nullable=True)
    document_type = Column(String(50), nullable=False)
    document_number = Column(String(50), nullable=True)
    issuer = Column(String(100), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    verification_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    status = Column(String(20), nullable=False, default="ACTIVE")
    file_reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    verified_by = Column(PG_UUID(as_uuid=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
