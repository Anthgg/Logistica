export type DocumentStatus =
  | 'DRAFT'
  | 'READY_TO_ISSUE'
  | 'ISSUED'
  | 'CANCELLED'
  | 'REPLACED'
  | 'FAILED'
  | 'ARCHIVED'

export type DocumentFamily =
  | 'REMISSION_GUIDE'
  | 'MANIFEST'
  | 'PROOF_OF_DELIVERY'
  | 'INCIDENT_ACT'
  | 'OTHER'

export type ExportJobStatus =
  | 'QUEUED'
  | 'VALIDATING'
  | 'PROCESSING'
  | 'READY'
  | 'FAILED'
  | 'EXPIRED'
  | 'CANCELLED'

export interface DocumentCapabilities {
  can_preview: boolean
  can_download: boolean
  can_print: boolean
  can_reprint: boolean
  can_cancel: boolean
  can_view_history: boolean
  can_view_original_cancelled?: boolean
}

export interface DocumentItem {
  id: string
  code: string
  title: string
  family: DocumentFamily
  document_type: string
  status: DocumentStatus
  organization_id: string | null
  branch_id: string | null
  branch_name?: string | null
  warehouse_id: string | null
  warehouse_name?: string | null
  issued_at: string | null
  issued_by_user_id: string | null
  issued_by_user_name?: string | null
  operation_type: string | null
  operation_id: string | null
  reprint_count: number
  hash_sha256: string
  capabilities: DocumentCapabilities
  created_at: string
  updated_at: string
}

export interface DocumentDetail extends DocumentItem {
  template_version: string
  snapshot_version: string
  content_snapshot: Record<string, unknown>
  cancellation_reason?: string | null
  cancelled_at?: string | null
  cancelled_by_user_name?: string | null
}

export interface DocumentHistoryEntry {
  id: string
  document_id: string
  event_type: string
  description: string
  user_name: string | null
  created_at: string
  copy_number?: number | null
  reason?: string | null
  correlation_id?: string | null
}

export interface DocumentReprintRequest {
  reason: string
}

export interface DocumentCancelRequest {
  reason: string
  confirm_code: string
}

export interface DocumentExportRequest {
  document_ids: string[]
  export_format: 'ZIP' | 'COMBINED_PDF'
  include_manifest: boolean
  include_checksums: boolean
  reason?: string
}

export interface DocumentExportJob {
  id: string
  status: ExportJobStatus
  total_documents: number
  processed_documents: number
  export_format: string
  created_at: string
  expires_at: string
  download_url?: string | null
  error_message?: string | null
}

export interface DocumentTalonario {
  id: string
  series_code: string
  document_type: string
  start_number: number
  end_number: number
  current_number: number
  status: 'active' | 'exhausted' | 'closed'
  branch_id: string
  branch_name?: string
  warehouse_id?: string
  warehouse_name?: string
  year: number
  reserved_count: number
  issued_count: number
  cancelled_count: number
  available_count: number
  created_at: string
}

export interface DocumentPackageEntry {
  document_id: string
  code: string
  document_type: string
  family: DocumentFamily
  status: DocumentStatus
  is_required: boolean
  is_present: boolean
}

export interface DocumentPackage {
  operation_type: string
  operation_id: string
  status: 'COMPLETE' | 'INCOMPLETE' | 'NO_DOCUMENTS'
  required_count: number
  present_count: number
  missing_count: number
  documents: DocumentPackageEntry[]
}
