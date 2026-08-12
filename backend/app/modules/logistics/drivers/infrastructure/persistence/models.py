"""SQLAlchemy ORM models for Phase 029 — Driver Master Data."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class DriverModel(Base):
    __tablename__ = "drivers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    driver_code = Column(String(30), nullable=False)
    normalized_driver_code = Column(String(30), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    paternal_last_name = Column(String(100), nullable=False)
    maternal_last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=True)
    nationality_country_code = Column(String(3), nullable=False, default="PE")

    primary_identity_document_id = Column(PG_UUID(as_uuid=True), nullable=True)
    primary_license_id = Column(PG_UUID(as_uuid=True), nullable=True)
    current_carrier_assignment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    primary_contact_id = Column(PG_UUID(as_uuid=True), nullable=True)
    current_photo_id = Column(PG_UUID(as_uuid=True), nullable=True)

    lifecycle_status = Column(String(20), nullable=False, default="DRAFT", index=True)
    compliance_status = Column(String(30), nullable=False, default="NOT_EVALUATED", index=True)
    eligibility_status = Column(String(30), nullable=False, default="NOT_EVALUATED", index=True)
    active_version_id = Column(PG_UUID(as_uuid=True), nullable=True)

    user_account_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_link_status = Column(String(20), nullable=False, default="NOT_LINKED")

    notes = Column(Text, nullable=True)
    row_version = Column(Integer, nullable=False, default=1)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)

    suspended_at = Column(DateTime(timezone=True), nullable=True)
    suspended_by = Column(PG_UUID(as_uuid=True), nullable=True)
    suspension_reason = Column(Text, nullable=True)

    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_by = Column(PG_UUID(as_uuid=True), nullable=True)
    block_reason = Column(Text, nullable=True)

    retired_at = Column(DateTime(timezone=True), nullable=True)
    retired_by = Column(PG_UUID(as_uuid=True), nullable=True)
    retirement_reason = Column(Text, nullable=True)

    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(PG_UUID(as_uuid=True), nullable=True)
    archive_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_driver_code", name="uq_drivers_org_code"),
    )

    identity_documents = relationship("DriverIdentityDocumentModel", back_populates="driver", cascade="all, delete-orphan")
    licenses = relationship("DriverLicenseModel", back_populates="driver", cascade="all, delete-orphan")
    carrier_assignments = relationship("DriverCarrierAssignmentModel", back_populates="driver", cascade="all, delete-orphan")
    contacts = relationship("DriverContactModel", back_populates="driver", cascade="all, delete-orphan")
    emergency_contacts = relationship("DriverEmergencyContactModel", back_populates="driver", cascade="all, delete-orphan")
    photos = relationship("DriverPhotoModel", back_populates="driver", cascade="all, delete-orphan")
    documents = relationship("DriverDocumentModel", back_populates="driver", cascade="all, delete-orphan")
    operational_restrictions = relationship("DriverOperationalRestrictionModel", back_populates="driver", cascade="all, delete-orphan")
    versions = relationship("DriverVersionModel", back_populates="driver", cascade="all, delete-orphan")


class DriverVersionModel(Base):
    __tablename__ = "driver_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")

    identity_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))
    license_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))
    categories_snapshot = Column(JSONB, nullable=False, server_default=text("'[]'"))
    carrier_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))
    contact_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))
    photo_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))
    restrictions_snapshot = Column(JSONB, nullable=False, server_default=text("'[]'"))
    compliance_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))
    eligibility_snapshot = Column(JSONB, nullable=False, server_default=text("'{}'"))

    content_hash = Column(String(64), nullable=False)
    effective_from = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("driver_id", "version", name="uq_driver_versions_num"),
    )

    driver = relationship("DriverModel", back_populates="versions")


class DriverIdentityDocumentModel(Base):
    __tablename__ = "driver_identity_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(20), nullable=False, default="DNI")
    country_code = Column(String(3), nullable=False, default="PE")
    value = Column(String(50), nullable=False)
    normalized_value = Column(String(50), nullable=False, index=True)
    masked_value = Column(String(50), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=True)

    verification_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    verification_source = Column(String(50), nullable=True)

    issued_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)

    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "document_type", "normalized_value", name="uq_driver_id_docs_org_val"),
    )

    driver = relationship("DriverModel", back_populates="identity_documents")


class DriverLicenseModel(Base):
    __tablename__ = "driver_licenses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code = Column(String(3), nullable=False, default="PE")
    issuing_authority = Column(String(100), nullable=False, default="MTC")
    license_number = Column(String(50), nullable=False)
    normalized_license_number = Column(String(50), nullable=False, index=True)
    masked_license_number = Column(String(50), nullable=False)

    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    verification_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    verification_source = Column(String(50), nullable=True)

    issued_at = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=False, index=True)

    revoked_at = Column(DateTime(timezone=True), nullable=True)
    suspension_start = Column(Date, nullable=True)
    suspension_end = Column(Date, nullable=True)
    primary_license = Column(Boolean, nullable=False, default=True)

    file_reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    row_version = Column(Integer, nullable=False, default=1)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "issuing_authority", "normalized_license_number", name="uq_driver_licenses_org_auth_num"),
    )

    driver = relationship("DriverModel", back_populates="licenses")
    category_assignments = relationship("DriverLicenseCategoryAssignmentModel", back_populates="license", cascade="all, delete-orphan")
    license_restrictions = relationship("DriverLicenseRestrictionModel", back_populates="license", cascade="all, delete-orphan")


class DriverLicenseCategoryModel(Base):
    __tablename__ = "driver_license_categories"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    country_code = Column(String(3), nullable=False, default="PE")
    jurisdiction_code = Column(String(10), nullable=True)
    code = Column(String(20), nullable=False)
    normalized_code = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category_group = Column(String(50), nullable=True)
    minimum_age = Column(Integer, nullable=True)
    hierarchy_level = Column(Integer, nullable=False, default=1)

    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    system_defined = Column(Boolean, nullable=False, default=True)
    version = Column(String(20), nullable=False, default="1.0.0")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    legal_reference = Column(String(200), nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("country_code", "normalized_code", name="uq_driver_license_cats_country_code"),
    )


class DriverLicenseCategoryAssignmentModel(Base):
    __tablename__ = "driver_license_category_assignments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_license_id = Column(PG_UUID(as_uuid=True), ForeignKey("driver_licenses.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(PG_UUID(as_uuid=True), ForeignKey("driver_license_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    valid_from = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=False, index=True)
    restrictions_snapshot = Column(JSONB, nullable=False, server_default=text("'[]'"))
    source_type = Column(String(30), nullable=False, default="MANUAL_ENTRY")

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    license = relationship("DriverLicenseModel", back_populates="category_assignments")
    category = relationship("DriverLicenseCategoryModel")


class DriverLicenseRestrictionModel(Base):
    __tablename__ = "driver_license_restrictions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_license_id = Column(PG_UUID(as_uuid=True), ForeignKey("driver_licenses.id", ondelete="CASCADE"), nullable=False, index=True)
    restriction_code = Column(String(30), nullable=False)
    restriction_type = Column(String(40), nullable=False, default="LICENSE_ANNOTATION")
    description = Column(String(250), nullable=False)
    source_type = Column(String(30), nullable=False, default="LICENSE_ANNOTATION")
    severity = Column(String(20), nullable=False, default="MEDIUM")
    blocking = Column(Boolean, nullable=False, default=False)
    valid_from = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    license = relationship("DriverLicenseModel", back_populates="license_restrictions")


class DriverLicenseVehicleTypeRuleModel(Base):
    __tablename__ = "driver_license_vehicle_type_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    jurisdiction_code = Column(String(10), nullable=False, default="PE")
    license_category_id = Column(PG_UUID(as_uuid=True), ForeignKey("driver_license_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False, index=True)
    body_type = Column(String(50), nullable=True)
    allowed = Column(Boolean, nullable=False, default=True)
    requires_additional_certificate = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    legal_reference = Column(String(200), nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    category = relationship("DriverLicenseCategoryModel")


class DriverCarrierAssignmentModel(Base):
    __tablename__ = "driver_carrier_assignments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_business_partner_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="RESTRICT"), nullable=False, index=True)
    carrier_role_id = Column(PG_UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    assignment_type = Column(String(30), nullable=False, default="INTERNAL")
    employment_reference = Column(String(100), nullable=True)

    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="CURRENT", index=True)
    authorization_reference = Column(String(100), nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    ended_by = Column(PG_UUID(as_uuid=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    end_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    driver = relationship("DriverModel", back_populates="carrier_assignments")
    carrier = relationship("BusinessPartnerModel")
    carrier_role = relationship("BusinessPartnerRoleModel")


class DriverContactModel(Base):
    __tablename__ = "driver_contacts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type = Column(String(20), nullable=False, default="PERSONAL")
    email = Column(String(150), nullable=True)
    phone = Column(String(30), nullable=True)
    mobile_phone = Column(String(30), nullable=True)
    country_calling_code = Column(String(5), nullable=True, default="+51")
    address_line = Column(String(250), nullable=True)
    district = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    country_code = Column(String(3), nullable=False, default="PE")
    preferred_channel = Column(String(20), nullable=True, default="PHONE")

    is_primary = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    driver = relationship("DriverModel", back_populates="contacts")


class DriverEmergencyContactModel(Base):
    __tablename__ = "driver_emergency_contacts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    relationship_label = Column(String(50), nullable=False)
    phone = Column(String(30), nullable=False)
    alternate_phone = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)

    consent_status = Column(String(20), nullable=False, default="GRANTED")
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    driver = relationship("DriverModel", back_populates="emergency_contacts")


class DriverPhotoModel(Base):
    __tablename__ = "driver_photos"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_type = Column(String(30), nullable=False, default="PROFILE")
    file_reference_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    is_current = Column(Boolean, nullable=False, default=True)

    captured_at = Column(DateTime(timezone=True), nullable=True)
    captured_by = Column(PG_UUID(as_uuid=True), nullable=True)
    source_type = Column(String(30), nullable=False, default="INTERNAL_CAPTURE")

    content_hash = Column(String(64), nullable=True)
    mime_type = Column(String(50), nullable=True, default="image/jpeg")
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=True)

    retention_policy = Column(String(50), nullable=False, default="STANDARD_5_YEARS")
    consent_reference = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)

    driver = relationship("DriverModel", back_populates="photos")


class DriverDocumentModel(Base):
    __tablename__ = "driver_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    document_number = Column(String(50), nullable=True)
    issuer = Column(String(150), nullable=True)

    issued_at = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True, index=True)

    verification_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    file_reference_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_type = Column(String(30), nullable=False, default="MANUAL_UPLOAD")
    source_reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    driver = relationship("DriverModel", back_populates="documents")


class DriverDocumentRequirementModel(Base):
    __tablename__ = "driver_document_requirements"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    carrier_category_scope = Column(String(50), nullable=True)
    vehicle_type_scope = Column(String(50), nullable=True)
    operation_type_scope = Column(String(50), nullable=True)

    document_type = Column(String(50), nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    blocking = Column(Boolean, nullable=False, default=True)
    requires_expiration = Column(Boolean, nullable=False, default=True)
    warning_days_before_expiration = Column(Integer, nullable=False, default=30)
    minimum_verification_status = Column(String(30), nullable=False, default="METADATA_REVIEWED")

    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DriverOperationalRestrictionModel(Base):
    __tablename__ = "driver_operational_restrictions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    restriction_type = Column(String(40), nullable=False, default="MANUAL_BLOCK")
    source_type = Column(String(30), nullable=False, default="ADMINISTRATIVE")
    severity = Column(String(20), nullable=False, default="CRITICAL")
    blocking = Column(Boolean, nullable=False, default=True)

    description = Column(String(250), nullable=False)
    reason = Column(Text, nullable=False)

    valid_from = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    revoked_by = Column(PG_UUID(as_uuid=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    driver = relationship("DriverModel", back_populates="operational_restrictions")


class DriverUserAccountLinkModel(Base):
    __tablename__ = "driver_user_account_links"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)

    status = Column(String(20), nullable=False, default="LINKED", index=True)
    linked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    linked_by = Column(PG_UUID(as_uuid=True), nullable=True)

    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(PG_UUID(as_uuid=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("driver_id", "user_id", name="uq_driver_user_link"),
    )
