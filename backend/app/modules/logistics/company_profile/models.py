"""SQLAlchemy models for Company Profile and institutional settings (Phase 021)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class OrganizationProfileModel(Base):
    """Institutional extension model for Organization (Phase 021)."""

    __tablename__ = "organization_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    legal_name: Mapped[str] = mapped_column(String(256), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False, unique=True, index=True)

    legal_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    economic_activity: Mapped[str | None] = mapped_column(String(256), nullable=True)
    website: Mapped[str | None] = mapped_column(String(256), nullable=True)
    primary_email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    primary_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    country_code: Mapped[str] = mapped_column(String(2), default="PE", server_default=text("'PE'"), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="es-PE", server_default=text("'es-PE'"), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Lima", server_default=text("'America/Lima'"), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), default="PEN", server_default=text("'PEN'"), nullable=False)
    document_language: Mapped[str] = mapped_column(String(10), default="es", server_default=text("'es'"), nullable=False)

    profile_status: Mapped[str] = mapped_column(String(32), default="DRAFT", server_default=text("'DRAFT'"), nullable=False)
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_profile_versions.id", ondelete="SET NULL", use_alter=True, name="fk_org_profile_active_version"), nullable=True
    )

    verification_status: Mapped[str] = mapped_column(String(32), default="FORMAT_VALID", server_default=text("'FORMAT_VALID'"), nullable=False)
    verification_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    versions: Mapped[list["OrganizationProfileVersionModel"]] = relationship(
        "OrganizationProfileVersionModel",
        back_populates="profile",
        cascade="all, delete-orphan",
        foreign_keys="OrganizationProfileVersionModel.organization_profile_id",
    )


class OrganizationProfileVersionModel(Base):
    """Immutable version payload contract for an OrganizationProfile (Phase 021)."""

    __tablename__ = "organization_profile_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", server_default=text("'DRAFT'"), nullable=False)

    legal_name: Mapped[str] = mapped_column(String(256), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False)

    institutional_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    profile: Mapped["OrganizationProfileModel"] = relationship(
        "OrganizationProfileModel",
        back_populates="versions",
        foreign_keys=[organization_profile_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_profile_id", "version", name="uq_org_profile_ver"),
    )


class OrganizationAddressModel(Base):
    """Institutional physical/legal address per organization and branch (Phase 021)."""

    __tablename__ = "organization_addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="SET NULL"), nullable=True
    )
    address_type: Mapped[str] = mapped_column(String(32), nullable=False)  # LEGAL, FISCAL, COMMERCIAL, OPERATIONS, BILLING, etc.
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    address_line: Mapped[str] = mapped_column(String(512), nullable=False)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), default="PE", server_default=text("'PE'"), nullable=False)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    is_document_address: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="FORMAT_VALID", server_default=text("'FORMAT_VALID'"), nullable=False)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class OrganizationContactModel(Base):
    """Institutional contact person/department (Phase 021)."""

    __tablename__ = "organization_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="SET NULL"), nullable=True
    )
    contact_type: Mapped[str] = mapped_column(String(32), nullable=False)  # GENERAL, COMMERCIAL, PURCHASES, RECEPTION, etc.
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    position: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extension: Mapped[str | None] = mapped_column(String(16), nullable=True)
    website: Mapped[str | None] = mapped_column(String(256), nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    show_in_documents: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    document_families: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class OrganizationAssetModel(Base):
    """Institutional image assets (Logos, Visual Signatures, Stamps) (Phase 021)."""

    __tablename__ = "organization_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)  # PRIMARY_LOGO, MONOCHROME_LOGO, DOCUMENT_LOGO, VISUAL_SIGNATURE, etc.
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", server_default=text("'local'"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'"), nullable=False)


class AuthorizedSignerModel(Base):
    """Authorized signers with visual signature associations and scoping (Phase 021)."""

    __tablename__ = "authorized_signers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    position_title: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_number_masked: Mapped[str | None] = mapped_column(String(32), nullable=True)
    authorization_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    authorization_type: Mapped[str] = mapped_column(String(64), default="LEGAL_REPRESENTATIVE", server_default=text("'LEGAL_REPRESENTATIVE'"), nullable=False)

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)

    signature_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_assets.id", ondelete="SET NULL"), nullable=True
    )
    stamp_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_assets.id", ondelete="SET NULL"), nullable=True
    )

    can_sign_all_branches: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    branch_scope: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    document_family_scope: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    document_type_scope: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    signature_asset: Mapped["OrganizationAssetModel | None"] = relationship("OrganizationAssetModel", foreign_keys=[signature_asset_id])


class OrganizationDocumentSettingsModel(Base):
    """Institutional document presentation settings per organization (Phase 021)."""

    __tablename__ = "organization_document_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    profile_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_profile_versions.id", ondelete="SET NULL"), nullable=True
    )
    document_logo_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_assets.id", ondelete="SET NULL"), nullable=True
    )
    default_address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_addresses.id", ondelete="SET NULL"), nullable=True
    )
    default_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization_contacts.id", ondelete="SET NULL"), nullable=True
    )

    show_ruc: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_trade_name: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_legal_name: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_address: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_contact: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_template_version: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_renderer_version: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_partial_hash: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_qr: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_page_number: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    confidentiality_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    footer_text: Mapped[str | None] = mapped_column(String(512), nullable=True)

    default_locale: Mapped[str] = mapped_column(String(10), default="es-PE", server_default=text("'es-PE'"), nullable=False)
    default_timezone: Mapped[str] = mapped_column(String(50), default="America/Lima", server_default=text("'America/Lima'"), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), default="PEN", server_default=text("'PEN'"), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class OrganizationNumberingDisplayPolicyModel(Base):
    """Institutional numbering presentation policy (Phase 021)."""

    __tablename__ = "organization_numbering_display_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="SET NULL"), nullable=True
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False
    )
    code_standard_version: Mapped[str] = mapped_column(String(32), default="1.0.0", server_default=text("'1.0.0'"), nullable=False)
    document_site_code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_site_codes.id", ondelete="SET NULL"), nullable=True
    )

    display_pattern: Mapped[str] = mapped_column(
        String(128), default="{TYPE}-{SITE}-{YEAR}-{SEQUENCE}", server_default=text("'{TYPE}-{SITE}-{YEAR}-{SEQUENCE}'"), nullable=False
    )
    sequence_padding: Mapped[int] = mapped_column(Integer, default=6, server_default=text("6"), nullable=False)

    show_internal_code: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_external_series: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_external_number: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
