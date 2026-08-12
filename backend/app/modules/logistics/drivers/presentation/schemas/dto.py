"""Pydantic v2 DTO Schemas for Phase 029 — Driver Master Data."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- DRIVER CORE DTOS ---
class CreateDriverRequestDTO(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    paternal_last_name: str = Field(..., min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    maternal_last_name: Optional[str] = Field(None, max_length=100)
    custom_code: Optional[str] = Field(None, max_length=30)
    date_of_birth: Optional[date] = None
    nationality_country_code: str = Field("PE", min_length=2, max_length=3)
    notes: Optional[str] = None


class UpdateDriverRequestDTO(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    paternal_last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    maternal_last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    notes: Optional[str] = None
    expected_row_version: Optional[int] = None


class DriverBlockRequestDTO(BaseModel):
    reason: str = Field(..., min_length=5)


class DriverResponseDTO(BaseModel):
    id: UUID
    organization_id: UUID
    driver_code: str
    display_name: str
    first_name: str
    middle_name: Optional[str] = None
    paternal_last_name: str
    maternal_last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality_country_code: str

    primary_identity_document_id: Optional[UUID] = None
    primary_license_id: Optional[UUID] = None
    current_carrier_assignment_id: Optional[UUID] = None
    primary_contact_id: Optional[UUID] = None
    current_photo_id: Optional[UUID] = None

    lifecycle_status: str
    compliance_status: str
    eligibility_status: str
    active_version_id: Optional[UUID] = None
    user_account_id: Optional[UUID] = None
    user_link_status: str

    notes: Optional[str] = None
    row_version: int
    created_at: datetime
    updated_at: datetime


class DriverSummaryDTO(BaseModel):
    id: UUID
    driver_code: str
    display_name: str
    lifecycle_status: str
    compliance_status: str
    eligibility_status: str
    updated_at: datetime


# --- IDENTITY DOCUMENT DTOS ---
class CreateDriverIdentityDocumentRequestDTO(BaseModel):
    document_type: str = Field("DNI", max_length=20)
    value: str = Field(..., min_length=5, max_length=50)
    country_code: str = Field("PE", min_length=2, max_length=3)
    is_primary: bool = True
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    valid_from: Optional[date] = None


class DriverIdentityDocumentResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    document_type: str
    country_code: str
    masked_value: str
    value: Optional[str] = None  # Exposed only if sensitive_read permission
    is_primary: bool
    verification_status: str
    status: str
    valid_from: date
    expires_at: Optional[date] = None
    created_at: datetime


# --- LICENSE & CATEGORY DTOS ---
class CreateDriverLicenseRequestDTO(BaseModel):
    license_number: str = Field(..., min_length=5, max_length=50)
    expires_at: date
    issuing_authority: str = Field("MTC", max_length=100)
    country_code: str = Field("PE", min_length=2, max_length=3)
    valid_from: Optional[date] = None
    primary_license: bool = True
    notes: Optional[str] = None


class DriverLicenseResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    country_code: str
    issuing_authority: str
    masked_license_number: str
    license_number: Optional[str] = None  # Exposed only if sensitive_read
    status: str
    verification_status: str
    valid_from: date
    expires_at: date
    primary_license: bool
    created_at: datetime


class DriverLicenseCategoryResponseDTO(BaseModel):
    id: UUID
    country_code: str
    code: str
    name: str
    hierarchy_level: int
    status: str


class AssignCategoryRequestDTO(BaseModel):
    category_code: str = Field(..., min_length=1, max_length=20)
    expires_at: date
    country_code: str = Field("PE", min_length=2, max_length=3)
    valid_from: Optional[date] = None


class DriverLicenseCategoryAssignmentResponseDTO(BaseModel):
    id: UUID
    driver_license_id: UUID
    category_id: UUID
    status: str
    valid_from: date
    expires_at: date
    created_at: datetime


# --- CARRIER ASSIGNMENT DTOS ---
class AssignCarrierRequestDTO(BaseModel):
    carrier_business_partner_id: UUID
    assignment_type: str = Field("INTERNAL", max_length=30)
    valid_from: Optional[date] = None
    employment_reference: Optional[str] = None


class DriverCarrierAssignmentResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    carrier_business_partner_id: UUID
    carrier_role_id: UUID
    assignment_type: str
    employment_reference: Optional[str] = None
    valid_from: date
    valid_until: Optional[date] = None
    status: str
    created_at: datetime


# --- CONTACT & PHOTO DTOS ---
class CreateDriverContactRequestDTO(BaseModel):
    contact_type: str = Field("PERSONAL", max_length=20)
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    address_line: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    department: Optional[str] = None
    is_primary: bool = True


class DriverContactResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    contact_type: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    is_primary: bool
    status: str
    created_at: datetime


class LinkDriverPhotoRequestDTO(BaseModel):
    file_reference_id: UUID
    photo_type: str = Field("PROFILE", max_length=30)
    source_type: str = Field("INTERNAL_CAPTURE", max_length=30)
    consent_reference: Optional[str] = None


class DriverPhotoResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    photo_type: str
    file_reference_id: UUID
    status: str
    is_current: bool
    captured_at: Optional[datetime] = None
    created_at: datetime


# --- DOCUMENT & RESTRICTION DTOS ---
class CreateDriverDocumentRequestDTO(BaseModel):
    document_type: str = Field(..., max_length=50)
    document_number: Optional[str] = None
    issuer: Optional[str] = None
    issued_at: Optional[date] = None
    valid_from: Optional[date] = None
    expires_at: Optional[date] = None
    file_reference_id: Optional[UUID] = None
    notes: Optional[str] = None


class DriverDocumentResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    document_type: str
    document_number: Optional[str] = None
    issuer: Optional[str] = None
    expires_at: Optional[date] = None
    verification_status: str
    status: str
    file_reference_id: Optional[UUID] = None
    created_at: datetime


class CreateDriverRestrictionRequestDTO(BaseModel):
    restriction_type: str = Field(..., max_length=40)
    description: str = Field(..., max_length=250)
    reason: str
    severity: str = Field("CRITICAL", max_length=20)
    blocking: bool = True
    valid_until: Optional[date] = None


class DriverRestrictionResponseDTO(BaseModel):
    id: UUID
    driver_id: UUID
    restriction_type: str
    severity: str
    blocking: bool
    description: str
    reason: str
    status: str
    valid_from: datetime
    valid_until: Optional[datetime] = None
    created_at: datetime


# --- COMPATIBILITY & DUPLICATES DTOS ---
class VehicleCompatibilityRequestDTO(BaseModel):
    vehicle_type: str = Field(..., min_length=2, max_length=50)
    body_type: Optional[str] = None
    effective_at: Optional[date] = None


class VehicleCompatibilityResponseDTO(BaseModel):
    status: str
    allowed: bool
    blocking_reasons: List[str]
    warnings: List[str]
    matching_categories: List[str]
    missing_categories: List[str]
    evaluated_at: str


class DuplicateCheckRequestDTO(BaseModel):
    identity_document_value: Optional[str] = None
    license_number: Optional[str] = None
    first_name: Optional[str] = None
    paternal_last_name: Optional[str] = None
    phone: Optional[str] = None


class DuplicateCheckResponseDTO(BaseModel):
    duplicate_found: bool
    match_level: str
    candidate_matches: List[Dict[str, Any]]
