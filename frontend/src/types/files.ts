// ─── File Repository – TypeScript strict types (Phase 030) ────────────────────
// No base64. No localStorage. No signed URLs persisted. No buckets exposed.

import type { PaginatedResponse } from './logistics-resources'

// ─── Enums ───────────────────────────────────────────────────────────────────

export type FileAssetType =
  | 'DOCUMENT'
  | 'IMAGE'
  | 'PDF'
  | 'XML'
  | 'SPREADSHEET'
  | 'SIGNATURE'
  | 'PHOTO'
  | 'EVIDENCE'
  | 'OTHER'

export type FileLifecycleStatus =
  | 'UPLOADING'
  | 'PROCESSING'
  | 'QUARANTINED'
  | 'AVAILABLE'
  | 'REJECTED'
  | 'ARCHIVED'
  | 'DELETED'
  | 'CORRUPTED'
  | 'FAILED'

export type MalwareScanStatus =
  | 'PENDING'
  | 'SCANNING'
  | 'CLEAN'
  | 'INFECTED'
  | 'SCAN_FAILED'
  | 'NOT_APPLICABLE'

export type FileIntegrityStatus =
  | 'VERIFIED'
  | 'UNVERIFIED'
  | 'MISMATCH'
  | 'OBJECT_MISSING'
  | 'CORRUPTED'

export type FileClassification =
  | 'INTERNAL'
  | 'CONFIDENTIAL'
  | 'RESTRICTED'
  | 'HIGHLY_RESTRICTED'
  | 'PUBLIC_APPROVED'

export type FileUploadStatus =
  | 'PREPARING'
  | 'AUTHORIZING'
  | 'UPLOADING'
  | 'PAUSED'
  | 'RESUMING'
  | 'FINALIZING'
  | 'ANALYZING'
  | 'VALIDATING'
  | 'QUARANTINED'
  | 'AVAILABLE'
  | 'REJECTED'
  | 'FAILED'
  | 'CANCELLED'

export type EvidenceStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'REVOKED'
  | 'SUPERSEDED'

export type FileDeletionRequestStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'PURGED'

export type FileVersionStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'SUPERSEDED'
  | 'ARCHIVED'

// ─── Capabilities ────────────────────────────────────────────────────────────

export interface FileCapabilities {
  can_view_metadata: boolean
  can_preview: boolean
  can_download: boolean
  can_upload: boolean
  can_upload_version: boolean
  can_update_metadata: boolean
  can_associate: boolean
  can_archive: boolean
  can_restore: boolean
  can_request_deletion: boolean
  can_view_history: boolean
  can_view_integrity: boolean
  can_manage_access: boolean
  can_create_evidence: boolean
  can_accept_evidence: boolean
  can_revoke_evidence: boolean
  can_view_custody: boolean
  can_apply_legal_hold: boolean
  can_release_legal_hold: boolean
}

// ─── Upload Session ──────────────────────────────────────────────────────────

export interface FileUploadSessionRequest {
  filename: string
  size_bytes: number
  declared_mime_type: string
  asset_type: FileAssetType
  classification: FileClassification
  resource_type?: string
  resource_id?: string
  association_type?: string
  metadata?: Record<string, string | undefined>
  client_sha256?: string
}

export interface FileUploadSession {
  id: string
  upload_target_url: string
  upload_headers: Record<string, string>
  method: 'PUT' | 'POST'
  expires_at: string
  requires_resumable: boolean
  chunk_size: number | null
  file_asset_id: string | null
  status: FileUploadStatus
}

// ─── File Asset ───────────────────────────────────────────────────────────────

export interface FileMetadata {
  title: string
  description: string | null
  document_number: string | null
  issuer_name: string | null
  issue_date: string | null
  effective_date: string | null
  expiration_date: string | null
  source: string | null
  language: string | null
  tags: string[]
  classification: FileClassification
}

export interface FileOwnership {
  organization_id: string | null
  business_owner: string | null
  custodian: string | null
  resource_type: string | null
  resource_id: string | null
  uploader_user_id: string | null
  uploader_user_name: string | null
  effective_from: string | null
  effective_until: string | null
}

export interface FileAssociation {
  id: string
  file_id: string
  resource_type: string
  resource_id: string
  resource_code: string
  resource_description: string
  association_type: string
  is_primary: boolean
  status: 'ACTIVE' | 'REMOVED'
  created_by_name: string
  created_at: string
}

export interface FileVersion {
  id: string
  file_id: string
  version_number: number
  status: FileVersionStatus
  filename: string
  mime_type: string
  size_bytes: number
  partial_hash: string
  scan_status: MalwareScanStatus
  integrity_status: FileIntegrityStatus
  uploaded_by_name: string
  uploaded_at: string
  reason: string | null
  is_current: boolean
}

export interface FileIntegrity {
  file_id: string
  sha256: string
  checksum_auxiliary: string | null
  calculated_at: string
  last_verified_at: string | null
  result: FileIntegrityStatus
  object_status: string
  alerts: string[]
  history: FileIntegrityEvent[]
}

export interface FileIntegrityEvent {
  id: string
  verified_at: string
  result: FileIntegrityStatus
  verifier: string
  notes: string | null
}

export interface FileRetentionPolicy {
  id: string
  name: string
  description: string
  minimum_retention_days: number
  archive_after_days: number | null
  deletion_after_days: number | null
  status: 'DRAFT' | 'ACTIVE' | 'RETIRED'
  created_at: string
  updated_at: string
}

export interface FileRetentionInfo {
  policy_id: string | null
  policy_name: string | null
  minimum_retention_days: number | null
  initial_date: string | null
  archive_date: string | null
  potential_deletion_date: string | null
  legal_hold_active: boolean
  blocking_reasons: string[]
}

export interface FileLegalHold {
  id: string
  file_id: string
  reason: string
  reference: string | null
  applied_at: string
  applied_by_name: string
  expires_at: string | null
  is_active: boolean
}

export interface FileDeletionRequest {
  id: string
  file_id: string
  file_code: string
  file_title: string
  requester_name: string
  reviewer_name: string | null
  reason: string
  basis: string
  status: FileDeletionRequestStatus
  requested_at: string
  reviewed_at: string | null
  purge_scheduled_at: string | null
  result: string | null
}

export interface FileAccessGrant {
  id: string
  file_id: string
  scope: string
  grantee_type: 'USER' | 'ROLE' | 'RESOURCE'
  grantee_id: string
  grantee_name: string
  permissions: string[]
  expires_at: string | null
  is_active: boolean
  created_by_name: string
  created_at: string
}

export interface FileAccessInfo {
  scope: string
  inherited_permissions: string[]
  owner_id: string | null
  resource_permissions: string[]
  grants: FileAccessGrant[]
}

// ─── Evidence ─────────────────────────────────────────────────────────────────

export interface EvidenceRecord {
  id: string
  code: string
  evidence_type: string
  subject_type: string
  subject_id: string
  subject_code: string
  file_id: string
  file_code: string
  file_title: string
  version_id: string
  version_number: number
  captured_by: string
  captured_at: string
  method: string
  source: string
  description: string | null
  status: EvidenceStatus
  accepted_by: string | null
  accepted_at: string | null
  retention_policy_id: string | null
  retention_policy_name: string | null
  integrity_status: FileIntegrityStatus
  partial_hash: string
  capabilities: EvidenceCapabilities
  created_at: string
  updated_at: string
}

export interface EvidenceCapabilities {
  can_view: boolean
  can_accept: boolean
  can_reject: boolean
  can_revoke: boolean
  can_supersede: boolean
  can_view_custody: boolean
}

export interface EvidenceCustodyEvent {
  id: string
  evidence_id: string
  event_type: string
  action: string
  result: string
  actor: string
  service: string
  reason: string | null
  event_hash_partial: string
  correlation_id_partial: string | null
  created_at: string
}

export interface EvidenceCreateRequest {
  evidence_type: string
  subject_type: string
  subject_id: string
  file_id: string
  version_id: string
  captured_at: string
  method: string
  source: string
  description?: string
  retention_policy_id?: string
}

// ─── File History ────────────────────────────────────────────────────────────

export interface FileHistoryEvent {
  id: string
  file_id: string
  event_type: string
  action_description: string
  result: string
  reason: string | null
  user_name: string
  version_number: number | null
  created_at: string
}

// ─── Main Entities ────────────────────────────────────────────────────────────

export interface FileAsset {
  id: string
  code: string
  title: string
  asset_type: FileAssetType
  mime_type: string
  size_bytes: number
  classification: FileClassification
  lifecycle_status: FileLifecycleStatus
  scan_status: MalwareScanStatus
  integrity_status: FileIntegrityStatus
  partial_hash: string
  current_version_number: number
  resource_type: string | null
  resource_id: string | null
  resource_code: string | null
  owner_name: string | null
  uploader_name: string | null
  retention_info: FileRetentionInfo | null
  legal_hold_active: boolean
  has_evidence: boolean
  evidence_count: number
  association_count: number
  version_count: number
  capabilities: FileCapabilities
  created_at: string
  updated_at: string
}

export interface FileAssetSummary {
  id: string
  code: string
  title: string
  asset_type: FileAssetType
  mime_type: string
  size_bytes: number
  classification: FileClassification
  lifecycle_status: FileLifecycleStatus
  scan_status: MalwareScanStatus
  integrity_status: FileIntegrityStatus
  resource_code: string | null
  owner_name: string | null
  uploader_name: string
  has_evidence: boolean
  legal_hold_active: boolean
  updated_at: string
}

export interface FileAssetDetail extends FileAsset {
  metadata: FileMetadata
  ownership: FileOwnership
  associations: FileAssociation[]
  versions: FileVersion[]
  access_info: FileAccessInfo | null
  retention_info: FileRetentionInfo | null
}

export interface FileListQuery {
  page?: number
  page_size?: number
  search?: string
  asset_type?: FileAssetType
  classification?: FileClassification
  lifecycle_status?: FileLifecycleStatus
  scan_status?: MalwareScanStatus
  integrity_status?: FileIntegrityStatus
  resource_type?: string
  resource_id?: string
  owner_id?: string
  uploader_id?: string
  has_evidence?: boolean
  has_legal_hold?: boolean
  has_versions?: boolean
  has_associations?: boolean
  created_from?: string
  created_to?: string
}

export interface FileRepositoryStats {
  total_files: number
  available_count: number
  processing_count: number
  quarantined_count: number
  rejected_count: number
  evidence_accepted_count: number
  integrity_failed_count: number
  legal_holds_count: number
  deletion_pending_count: number
}

export interface FileDeletionRequestListQuery {
  page?: number
  page_size?: number
  status?: FileDeletionRequestStatus
  requester_id?: string
  date_from?: string
  date_to?: string
}

export interface FileDeletionRequestCreate {
  file_id: string
  reason: string
  basis: string
}

export type PaginatedFileAssets = PaginatedResponse<FileAssetSummary>
export type PaginatedEvidence = PaginatedResponse<EvidenceRecord>
export type PaginatedDeletionRequests = PaginatedResponse<FileDeletionRequest>