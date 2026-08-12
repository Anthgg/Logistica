"""Pydantic v2 DTO Schemas for Phase 030 — Files and Evidence Centralization."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- UPLOAD SESSIONS ---

class UploadSessionCreateRequest(BaseModel):
    expected_filename: str = Field(..., max_length=255, description="Nombre esperado del archivo")
    expected_size_bytes: int = Field(..., gt=0, description="Tamaño en bytes esperado")
    declared_mime_type: str = Field(..., max_length=100, description="Content-Type declarado por cliente")
    asset_type: str = Field("DOCUMENT", description="Tipo de activo (DOCUMENT, XML, IMAGE, etc.)")
    classification: str = Field("CONFIDENTIAL", description="Clasificación de confidencialidad")
    intended_resource_type: Optional[str] = Field(None, description="Tipo de recurso destino opcional")
    intended_resource_id: Optional[str] = Field(None, description="ID del recurso destino opcional")
    intended_association_type: Optional[str] = Field(None, description="Tipo de asociación opcional")
    expected_sha256: Optional[str] = Field(None, max_length=64, description="Hash SHA-256 esperado opcional")


class UploadSessionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    expected_filename: str
    expected_size_bytes: int
    declared_mime_type: str
    upload_mode: str
    status: str
    quarantine_object_key: str
    upload_target_url: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class UploadSessionFinalizeRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Título visible del archivo")


# --- FILE VERSIONS & ASSETS ---

class FileVersionResponse(BaseModel):
    id: UUID
    file_asset_id: UUID
    version_number: int
    status: str
    storage_provider: str
    original_filename: str
    extension: str
    declared_MIME_type: str
    detected_MIME_type: str
    size_bytes: int
    SHA256: str
    page_count: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    XML_root_element: Optional[str] = None
    content_validation_status: str
    malware_scan_status: str
    malware_scanner_version: Optional[str] = None
    uploaded_by: UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True


class FileAssetResponse(BaseModel):
    id: UUID
    organization_id: UUID
    file_code: str
    normalized_file_code: str
    title: str
    description: Optional[str] = None
    asset_type: str
    classification: str
    lifecycle_status: str
    evidence_status: str
    owner_type: str
    owner_user_id: Optional[UUID] = None
    current_version_id: Optional[UUID] = None
    access_scope: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    row_version: int

    class Config:
        from_attributes = True


class FileAssetUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    classification: Optional[str] = None


# --- ASSOCIATIONS ---

class FileAssociationCreateRequest(BaseModel):
    resource_type: str = Field(..., max_length=50)
    resource_id: str = Field(..., max_length=100)
    association_type: str = Field("ATTACHMENT", max_length=50)
    is_primary: bool = False


class FileAssociationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    file_asset_id: UUID
    file_version_id: Optional[UUID] = None
    resource_type: str
    resource_id: str
    association_type: str
    is_primary: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- EVIDENCE & CUSTODY ---

class EvidenceRegisterRequest(BaseModel):
    file_asset_id: UUID
    evidence_type: str = Field(..., max_length=50)
    subject_type: str = Field(..., max_length=50)
    subject_id: str = Field(..., max_length=100)
    description: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    evidence_code: str
    evidence_type: str
    subject_type: str
    subject_id: str
    file_asset_id: UUID
    file_version_id: UUID
    captured_at: datetime
    captured_by_user_id: Optional[UUID] = None
    status: str
    acceptance_status: str
    accepted_by: Optional[UUID] = None
    accepted_at: Optional[datetime] = None
    chain_of_custody_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CustodyEventResponse(BaseModel):
    id: UUID
    evidence_id: UUID
    event_type: str
    actor_type: str
    actor_user_id: Optional[UUID] = None
    event_at: datetime
    reason: Optional[str] = None
    event_hash: str
    correlation_id: str

    class Config:
        from_attributes = True


# --- RETENTION & LEGAL HOLD ---

class LegalHoldApplyRequest(BaseModel):
    reason: str = Field(..., min_length=5)
    authority_reference: Optional[str] = None


class LegalHoldResponse(BaseModel):
    id: UUID
    file_asset_id: UUID
    reason: str
    authority_reference: Optional[str] = None
    applied_by: UUID
    applied_at: datetime
    status: str

    class Config:
        from_attributes = True


class DeletionRequestCreateRequest(BaseModel):
    reason: str = Field(..., min_length=5)
    deletion_basis: str = Field("USER_REQUEST")


class DeletionRequestResponse(BaseModel):
    id: UUID
    file_asset_id: UUID
    requested_by: UUID
    reason: str
    deletion_basis: str
    requested_at: datetime
    status: str

    class Config:
        from_attributes = True


class SignedUrlResponse(BaseModel):
    url: str
    expires_at: datetime
    file_id: UUID
    filename: str
