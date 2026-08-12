"""Pydantic schemas for Document Catalog endpoints (Phase 011)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentFamilyResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    owner_module: str
    display_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentFamilyListResponse(BaseModel):
    items: list[DocumentFamilyResponse]
    total: int


class DocumentRetentionPolicyResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    retention_class: str
    minimum_retention_days: int
    maximum_retention_days: int | None = None
    archive_after_days: int | None = None
    deletion_allowed: bool
    legal_hold_supported: bool
    requires_manual_review: bool
    applies_to_origin_type: str
    status: str
    version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTypeVersionResponse(BaseModel):
    id: UUID
    document_type_id: UUID
    version: str
    schema_version: str
    status: str
    effective_from: datetime
    effective_to: datetime | None = None
    required_fields_schema: dict[str, Any]
    optional_fields_schema: dict[str, Any] | None = None
    sections_schema: dict[str, Any] | None = None
    allowed_statuses: list[str]
    permission_policy: dict[str, str]
    retention_policy_id: UUID | None = None
    template_key: str
    template_version: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTypeSummaryResponse(BaseModel):
    id: UUID
    code: str
    name: str
    short_name: str | None = None
    description: str | None = None
    family_code: str
    family_name: str
    origin_type: str
    owner_module: str
    resource_type: str
    catalog_status: str
    is_sensitive: bool
    supports_issue: bool
    supports_reprint: bool
    supports_cancel: bool
    requires_qr: bool
    requires_signature: bool
    display_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTypeDetailResponse(DocumentTypeSummaryResponse):
    active_version: DocumentTypeVersionResponse | None = None
    is_system: bool
    is_official_external: bool
    supports_internal_number: bool
    supports_external_number: bool
    supports_series: bool
    supports_talonario: bool
    supports_preview: bool
    supports_download: bool
    supports_bulk_download: bool
    supports_public_verification: bool
    requires_reason_on_reprint: bool
    requires_reason_on_cancel: bool


class DocumentTypeListResponse(BaseModel):
    items: list[DocumentTypeSummaryResponse]
    total: int


class DocumentCatalogVersionResponse(BaseModel):
    version: str
    status: str
    released_at: datetime
    checksum: str
    total_families: int
    total_document_types: int
    total_proposed_types: int


class DocumentCatalogValidationResponse(BaseModel):
    valid: bool
    version: str
    errors: list[str]
    warnings: list[str]
    total_families: int
    total_document_types: int
    total_proposed_types: int
    total_retention_policies: int


# --- PHASE 020 SCHEMAS ---

class DocumentDraftCreate(BaseModel):
    document_type_code: str
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID | None = None
    source_resource_type: str
    source_resource_id: UUID | None = None
    source_operation_id: UUID | None = None
    title: str
    structured_data: dict[str, Any]
    sensitivity: str = "RESTRICTED"


class DocumentDraftUpdate(BaseModel):
    title: str | None = None
    structured_data: dict[str, Any] | None = None
    warehouse_id: UUID | None = None
    sensitivity: str | None = None


class DocumentIssueRequest(BaseModel):
    expected_document_version: str | None = None
    reason: str | None = None


class DocumentIssueResponse(BaseModel):
    document_id: UUID
    document_code: str
    status: str
    issued_at: datetime
    authoritative_artifact_id: UUID
    checksum: str


class DocumentSummaryResponse(BaseModel):
    id: UUID
    document_code: str | None = None
    document_type_code: str
    document_type_name: str
    family: str
    title: str
    status: str
    issued_at: datetime | None = None
    issued_by_summary: dict[str, Any] | None = None
    branch_summary: dict[str, Any]
    warehouse_summary: dict[str, Any] | None = None
    source_reference: dict[str, Any]
    reprint_count: int
    print_request_count: int
    sensitivity: str
    can_preview: bool
    can_download: bool
    can_print: bool
    can_reprint: bool
    can_cancel: bool
    can_view_history: bool
    authoritative_artifact_status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentSummaryResponse):
    lifecycle_status: str
    source_resource_type: str
    source_resource_id: UUID | None = None
    source_operation_id: UUID | None = None
    current_snapshot_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentSummaryResponse]
    total: int
    page: int
    page_size: int


class DocumentPreviewMetadataResponse(BaseModel):
    document_id: UUID
    title: str
    preview_url: str
    requires_watermark: bool
    watermark_text: str


class DocumentDownloadMetadataResponse(BaseModel):
    document_id: UUID
    artifact_id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    file_hash: str
    download_url: str


class DocumentPrintIntentCreate(BaseModel):
    reason: str | None = None
    client_context: dict[str, Any] | None = None


class DocumentReprintRequest(BaseModel):
    reason: str
    requested_copy_format: str = "PDF"


class DocumentReprintResponse(BaseModel):
    document_id: UUID
    copy_number: int
    artifact_id: UUID
    download_url: str
    generated_at: datetime


class DocumentCancelRequest(BaseModel):
    reason: str


class DocumentCancelResponse(BaseModel):
    document_id: UUID
    status: str
    cancelled_at: datetime
    cancelled_by: UUID
    reason: str


class DocumentHistoryEntryResponse(BaseModel):
    event_type: str
    timestamp: datetime
    actor_user_id: UUID | None = None
    actor_name: str | None = None
    reason: str | None = None
    copy_number: int | None = None
    details: dict[str, Any] | None = None



class DocumentHistoryResponse(BaseModel):
    document_id: UUID
    history: list[DocumentHistoryEntryResponse]


class DocumentSnapshotMetadataResponse(BaseModel):
    id: UUID
    snapshot_version: int
    created_at: datetime
    canonical_payload_hash: str


class DocumentArtifactResponse(BaseModel):
    id: UUID
    artifact_type: str
    mime_type: str
    filename: str
    size_bytes: int
    file_hash: str
    generated_at: datetime


class DocumentExportCreate(BaseModel):
    document_ids: list[UUID]
    export_format: str = "ZIP"  # ZIP, MERGED_PDF, MANIFEST_ONLY
    include_manifest: bool = True
    include_checksums: bool = True
    reason: str | None = None


class DocumentExportJobResponse(BaseModel):
    job_id: UUID
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    expires_at: datetime
    polling_url: str
    download_url: str | None = None


class DocumentPackageResponse(BaseModel):
    operation_id: UUID
    operation_type: str
    zip_url: str
    is_complete: bool
    missing_document_types: list[str]


class DocumentTalonarioExportRequest(BaseModel):
    purpose: str | None = None


class DocumentTalonarioManifestResponse(BaseModel):
    talonario_code: str
    range_start: int
    range_end: int
    total_numbers: int
    checksum: str

