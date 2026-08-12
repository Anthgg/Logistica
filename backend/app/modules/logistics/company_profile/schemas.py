"""Pydantic v2 schemas for Company Profile, versioning, addresses, contacts, assets & signers (Phase 021)."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# --- Organization Profile Schemas ---

class OrganizationProfileCreate(BaseModel):
    legal_name: str = Field(..., min_length=3, max_length=256, description="Razón Social oficial")
    trade_name: str | None = Field(None, max_length=256, description="Nombre Comercial opcional")
    ruc: str = Field(..., min_length=11, max_length=11, description="RUC peruano de 11 dígitos")

    legal_entity_type: str | None = Field(None, max_length=64, description="Ej: S.A.C., S.R.L., E.I.R.L.")
    economic_activity: str | None = Field(None, max_length=256)
    website: str | None = Field(None, max_length=256)
    primary_email: EmailStr | None = None
    primary_phone: str | None = Field(None, max_length=32)

    country_code: str = Field("PE", min_length=2, max_length=2)
    locale: str = Field("es-PE", max_length=10)
    timezone: str = Field("America/Lima", max_length=50)
    default_currency: str = Field("PEN", min_length=3, max_length=3)
    document_language: str = Field("es", max_length=10)


class OrganizationProfileUpdate(BaseModel):
    legal_name: str | None = Field(None, min_length=3, max_length=256)
    trade_name: str | None = Field(None, max_length=256)
    ruc: str | None = Field(None, min_length=11, max_length=11)

    legal_entity_type: str | None = None
    economic_activity: str | None = None
    website: str | None = None
    primary_email: EmailStr | None = None
    primary_phone: str | None = None

    country_code: str | None = None
    locale: str | None = None
    timezone: str | None = None
    default_currency: str | None = None
    document_language: str | None = None


class OrganizationProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    legal_name: str
    trade_name: str | None
    ruc: str
    legal_entity_type: str | None
    economic_activity: str | None
    website: str | None
    primary_email: str | None
    primary_phone: str | None
    country_code: str
    locale: str
    timezone: str
    default_currency: str
    document_language: str
    profile_status: str
    active_version_id: UUID | None
    verification_status: str
    verification_source: str | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OrganizationProfileVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_profile_id: UUID
    version: str
    status: str
    legal_name: str
    trade_name: str | None
    ruc: str
    institutional_payload: dict[str, Any]
    content_hash: str
    effective_from: datetime
    effective_to: datetime | None
    approved_by: UUID | None
    approved_at: datetime | None
    created_by: UUID | None
    created_at: datetime


class VersionActivateRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=256, description="Motivo de la activación de la versión institucional")


# --- Organization Address Schemas ---

class OrganizationAddressCreate(BaseModel):
    branch_id: UUID | None = None
    address_type: str = Field(..., max_length=32, description="LEGAL | FISCAL | COMMERCIAL | OPERATIONS | BILLING | CORRESPONDENCE | DOCUMENT_HEADER | OTHER")
    label: str = Field(..., min_length=2, max_length=128)
    address_line: str = Field(..., min_length=5, max_length=512)
    district: str | None = Field(None, max_length=128)
    province: str | None = Field(None, max_length=128)
    department: str | None = Field(None, max_length=128)
    postal_code: str | None = Field(None, max_length=32)
    country_code: str = Field("PE", min_length=2, max_length=2)
    latitude: float | None = None
    longitude: float | None = None
    is_primary: bool = False
    is_document_address: bool = True


class OrganizationAddressUpdate(BaseModel):
    branch_id: UUID | None = None
    address_type: str | None = None
    label: str | None = None
    address_line: str | None = None
    district: str | None = None
    province: str | None = None
    department: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_primary: bool | None = None
    is_document_address: bool | None = None


class OrganizationAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    branch_id: UUID | None
    address_type: str
    label: str
    address_line: str
    district: str | None
    province: str | None
    department: str | None
    postal_code: str | None
    country_code: str
    latitude: float | None
    longitude: float | None
    is_primary: bool
    is_document_address: bool
    verification_status: str
    status: str
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Organization Contact Schemas ---

class OrganizationContactCreate(BaseModel):
    branch_id: UUID | None = None
    contact_type: str = Field(..., max_length=32, description="GENERAL | COMMERCIAL | PURCHASES | RECEPTION | WAREHOUSE | DISPATCH | TRANSPORT | QUALITY | BILLING | LEGAL | EMERGENCY | OTHER")
    label: str = Field(..., min_length=2, max_length=128)
    full_name: str | None = Field(None, max_length=256)
    position: str | None = Field(None, max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=32)
    extension: str | None = Field(None, max_length=16)
    website: str | None = Field(None, max_length=256)
    is_primary: bool = False
    show_in_documents: bool = True
    document_families: list[str] | None = None


class OrganizationContactUpdate(BaseModel):
    branch_id: UUID | None = None
    contact_type: str | None = None
    label: str | None = None
    full_name: str | None = None
    position: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    extension: str | None = None
    website: str | None = None
    is_primary: bool | None = None
    show_in_documents: bool | None = None
    document_families: list[str] | None = None


class OrganizationContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    branch_id: UUID | None
    contact_type: str
    label: str
    full_name: str | None
    position: str | None
    email: str | None
    phone: str | None
    extension: str | None
    website: str | None
    is_primary: bool
    show_in_documents: bool
    document_families: list[str] | None
    status: str
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Organization Asset Schemas ---

class OrganizationAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    asset_type: str
    filename: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    file_hash: str
    status: str
    version: int
    uploaded_at: datetime
    approved_at: datetime | None
    revoked_at: datetime | None
    asset_metadata: dict[str, Any]


class AssetUploadResponse(BaseModel):
    asset_id: UUID
    asset_type: str
    filename: str
    size_bytes: int
    file_hash: str
    status: str
    message: str


# --- Authorized Signer Schemas ---

class AuthorizedSignerCreate(BaseModel):
    user_id: UUID | None = None
    full_name: str = Field(..., min_length=3, max_length=256)
    position_title: str = Field(..., min_length=2, max_length=128)
    department: str | None = Field(None, max_length=128)
    document_number_masked: str | None = Field(None, max_length=32, description="Ej: ****5678")
    authorization_reference: str | None = Field(None, max_length=128)
    authorization_type: str = Field("LEGAL_REPRESENTATIVE", max_length=64)

    valid_from: datetime | None = None
    valid_until: datetime | None = None
    signature_asset_id: UUID | None = None
    stamp_asset_id: UUID | None = None

    can_sign_all_branches: bool = True
    branch_scope: list[str] | None = None
    document_family_scope: list[str] | None = None
    document_type_scope: list[str] | None = None
    max_amount: Decimal | None = None
    currency_code: str | None = Field(None, max_length=3)
    notes: str | None = None


class AuthorizedSignerUpdate(BaseModel):
    full_name: str | None = None
    position_title: str | None = None
    department: str | None = None
    document_number_masked: str | None = None
    authorization_reference: str | None = None
    authorization_type: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    signature_asset_id: UUID | None = None
    stamp_asset_id: UUID | None = None
    can_sign_all_branches: bool | None = None
    branch_scope: list[str] | None = None
    document_family_scope: list[str] | None = None
    document_type_scope: list[str] | None = None
    max_amount: Decimal | None = None
    currency_code: str | None = None
    notes: str | None = None


class AuthorizedSignerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID | None
    full_name: str
    position_title: str
    department: str | None
    document_number_masked: str | None
    authorization_reference: str | None
    authorization_type: str
    valid_from: datetime
    valid_until: datetime | None
    status: str
    signature_asset_id: UUID | None
    stamp_asset_id: UUID | None
    can_sign_all_branches: bool
    branch_scope: list[str] | None
    document_family_scope: list[str] | None
    document_type_scope: list[str] | None
    max_amount: Decimal | None
    currency_code: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SignerRevokeRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=256, description="Motivo obligatorio de revocación del firmante")


# --- Organization Document Settings Schemas ---

class OrganizationDocumentSettingsUpdate(BaseModel):
    document_logo_asset_id: UUID | None = None
    default_address_id: UUID | None = None
    default_contact_id: UUID | None = None
    show_ruc: bool | None = None
    show_trade_name: bool | None = None
    show_legal_name: bool | None = None
    show_address: bool | None = None
    show_contact: bool | None = None
    show_template_version: bool | None = None
    show_renderer_version: bool | None = None
    show_partial_hash: bool | None = None
    show_qr: bool | None = None
    show_page_number: bool | None = None
    confidentiality_text: str | None = Field(None, max_length=512)
    footer_text: str | None = Field(None, max_length=512)
    default_locale: str | None = None
    default_timezone: str | None = None
    default_currency: str | None = None


class OrganizationDocumentSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    profile_version_id: UUID | None
    document_logo_asset_id: UUID | None
    default_address_id: UUID | None
    default_contact_id: UUID | None
    show_ruc: bool
    show_trade_name: bool
    show_legal_name: bool
    show_address: bool
    show_contact: bool
    show_template_version: bool
    show_renderer_version: bool
    show_partial_hash: bool
    show_qr: bool
    show_page_number: bool
    confidentiality_text: str | None
    footer_text: str | None
    default_locale: str
    default_timezone: str
    default_currency: str
    status: str
    created_at: datetime
    updated_at: datetime


# --- Numbering Display Policy Schemas ---

class NumberingDisplayPolicyCreate(BaseModel):
    branch_id: UUID | None = None
    document_type_id: UUID
    code_standard_version: str = Field("1.0.0", max_length=32)
    document_site_code_id: UUID | None = None
    display_pattern: str = Field("{TYPE}-{SITE}-{YEAR}-{SEQUENCE}", max_length=128)
    sequence_padding: int = Field(6, ge=4, le=10)
    show_internal_code: bool = True
    show_external_series: bool = True
    show_external_number: bool = True


class NumberingDisplayPolicyUpdate(BaseModel):
    branch_id: UUID | None = None
    document_site_code_id: UUID | None = None
    display_pattern: str | None = Field(None, max_length=128)
    sequence_padding: int | None = Field(None, ge=4, le=10)
    show_internal_code: bool | None = None
    show_external_series: bool | None = None
    show_external_number: bool | None = None


class NumberingDisplayPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    branch_id: UUID | None
    document_type_id: UUID
    code_standard_version: str
    document_site_code_id: UUID | None
    display_pattern: str
    sequence_padding: int
    show_internal_code: bool
    show_external_series: bool
    show_external_number: bool
    status: str
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Institutional Preview Schemas ---

class InstitutionalPreviewRequest(BaseModel):
    doc_type_code: str | None = Field(None, max_length=64, description="Código de tipo documental (ej: AREC, CIT, CPV, DIF, NC, APC, CEP, PED, MAN, POD, etc.)")
    document_type: str | None = Field(None, max_length=64)
    document_type_code: str | None = Field(None, max_length=64)
    family: str | None = None
    document_family: str | None = None
    branch_id: UUID | None = None
    signer_id: UUID | None = None
    address_id: UUID | None = None
    contact_id: UUID | None = None
    numbering_policy_id: UUID | None = None
    custom_data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_preview_request(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Clean empty strings into None for UUID fields
            for k in ["branch_id", "signer_id", "address_id", "contact_id", "numbering_policy_id"]:
                if data.get(k) == "" or data.get(k) is None:
                    data[k] = None
            
            # Resolve code
            code = data.get("doc_type_code") or data.get("document_type") or data.get("document_type_code") or "AREC"
            code_str = str(code).strip().upper()
            
            # Map frontend aliases/variants if any
            alias_map = {
                "GRR": "MAN",
                "GRT": "MAN",
                "MANIFEST": "MAN",
                "GUIA": "MAN",
                "REMISSION_GUIDE": "MAN",
                "PROOF_OF_DELIVERY": "POD",
            }
            resolved_code = alias_map.get(code_str, code_str)
            data["doc_type_code"] = resolved_code
        return data
