// ─── RUC Integration – TypeScript strict types ──────────────────────────────

export type RucTaxpayerStatus =
  | 'ACTIVO'
  | 'BAJA_PROVISIONAL'
  | 'BAJA_DEFINITIVA'
  | 'SUSPENSION_TEMPORAL'
  | 'INHABILITADO'
  | 'DESCONOCIDO'

export type RucDomicileCondition =
  | 'HABIDO'
  | 'NO_HABIDO'
  | 'NO_HALLADO'
  | 'PENDIENTE'
  | 'DESCONOCIDO'

export type RucSourceType =
  | 'OFFICIAL_PADRON'
  | 'ANNEX_PADRON'
  | 'AUTHORIZED_PROVIDER'
  | 'ASSISTED_REVIEW'
  | 'PARTNER_DECLARED'
  | 'HERITAGE'
  | 'UNKNOWN'

export type RucFreshnessStatus =
  | 'FRESH'
  | 'AGING'
  | 'STALE'
  | 'CRITICAL'
  | 'UNKNOWN'

export type RucConfidenceLevel =
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'UNVERIFIED'

export type RucDatasetStatus =
  | 'DISCOVERED'
  | 'DOWNLOADING'
  | 'VALIDATING'
  | 'IMPORTING'
  | 'VALIDATED'
  | 'ACTIVE'
  | 'SUPERSEDED'
  | 'REJECTED'
  | 'FAILED'
  | 'ROLLED_BACK'

export type RucImportStatus =
  | 'QUEUED'
  | 'DOWNLOADING'
  | 'VERIFYING'
  | 'EXTRACTING'
  | 'PROCESSING'
  | 'STAGING'
  | 'VALIDATING'
  | 'ACTIVATING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'

export type RucVerificationStatus =
  | 'VALIDATED'
  | 'PENDING_REVIEW'
  | 'CONFLICTED'
  | 'EXPIRED'
  | 'REVOKED'

// ─── Sub-structures ─────────────────────────────────────────────────────────

export interface RucAnnexAddress {
  id: string
  address: string
  ubigeo: string
  department: string | null
  province: string | null
  district: string | null
  source: RucSourceType
  source_label: string
  source_date: string // ISO date
  is_active: boolean
}

export interface RucFieldProvenance {
  field_name: string
  field_label: string
  value: string | null
  source: RucSourceType
  source_label: string
  source_date: string // ISO datetime
  confidence: RucConfidenceLevel
  age_in_days: number
  freshness_status: RucFreshnessStatus
  has_conflict: boolean
}

export interface RucDataConflict {
  id: string
  field_name: string
  field_label: string
  padron_value: string | null
  padron_date: string | null
  provider_value: string | null
  provider_date: string | null
  partner_value: string | null
  partner_date: string | null
  status: 'OPEN' | 'RESOLVED' | 'IGNORED'
  recommended_value: string | null
}

// ─── Main Lookup Result ─────────────────────────────────────────────────────

export interface RucLookupResponse {
  ruc: string
  legal_name: string
  trade_name: string | null
  taxpayer_status: RucTaxpayerStatus
  taxpayer_status_label: string
  domicile_condition: RucDomicileCondition
  domicile_condition_label: string
  ubigeo: string
  fiscal_address: string | null
  economic_activities: string[]
  annex_addresses: RucAnnexAddress[]
  source: RucSourceType
  source_label: string
  dataset_version: string | null
  source_date: string // ISO date/datetime
  lookup_date: string // ISO datetime
  age_in_days: number
  freshness_status: RucFreshnessStatus
  confidence_level: RucConfidenceLevel
  verification_status: RucVerificationStatus
  provider_used: string | null
  is_cached: boolean
  warnings: string[]
  conflicts: RucDataConflict[]
  provenance_by_field: RucFieldProvenance[]
}

export interface RucLookupRequest {
  ruc: string
  include_annexes?: boolean
  use_authorized_provider?: boolean
  partner_id?: string
}

// ─── Datasets & Imports ──────────────────────────────────────────────────────

export interface RucDatasetStatistics {
  total_rows: number
  accepted_rows: number
  rejected_rows: number
  duplicate_rows: number
  new_records: number
  updated_records: number
  deleted_records: number
}

export interface RucDataset {
  id: string
  dataset_type: string
  version: string
  source: RucSourceType
  source_label: string
  published_date: string
  downloaded_date: string
  status: RucDatasetStatus
  statistics: RucDatasetStatistics
  partial_hash: string
  parser_name: string
  duration_seconds: number
  has_anomalies: boolean
  anomaly_reasons: string[]
  created_at: string
}

export interface RucImportJob {
  id: string
  dataset_id: string | null
  dataset_type: string
  origin: string
  triggered_by_user_id: string
  triggered_by_user_name: string
  status: RucImportStatus
  stage: string
  progress_pct: number
  processed_rows: number
  total_rows: number
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
  error_message: string | null
}

// ─── Assisted Verification ───────────────────────────────────────────────────

export interface RucAssistedVerification {
  id: string
  ruc: string
  partner_id: string | null
  partner_name: string | null
  reason: string
  source_type: RucSourceType
  reference_number: string | null
  reviewed_at: string
  observed_legal_name: string
  observed_status: RucTaxpayerStatus
  observed_condition: RucDomicileCondition
  observed_ubigeo: string
  result: 'APPROVED' | 'REJECTED' | 'OBSERVED'
  observations: string
  created_by_user_id: string
  created_by_user_name: string
  approved_by_user_id: string | null
  approved_by_user_name: string | null
  approved_at: string | null
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED'
  created_at: string
}

export interface AssistedVerificationCreate {
  ruc: string
  partner_id?: string
  reason: string
  source_type: RucSourceType
  reference_number?: string
  reviewed_at: string
  observed_legal_name: string
  observed_status: RucTaxpayerStatus
  observed_condition: RucDomicileCondition
  observed_ubigeo: string
  result: 'APPROVED' | 'REJECTED' | 'OBSERVED'
  observations: string
}

// ─── Business Partner Integration ───────────────────────────────────────────

export interface BusinessPartnerRucVerification {
  id: string
  partner_id: string
  ruc: string
  verification_date: string
  source: RucSourceType
  source_label: string
  dataset_version: string | null
  confidence_level: RucConfidenceLevel
  taxpayer_status: RucTaxpayerStatus
  domicile_condition: RucDomicileCondition
  age_in_days: number
  freshness_status: RucFreshnessStatus
  verification_status: RucVerificationStatus
  applied_fields: string[]
  conflicts_count: number
  created_by_name: string
}

export interface ApplyRucDataRequest {
  verification_id: string
  apply_legal_name?: boolean
  apply_annex_as_candidate?: boolean
  selected_annex_address?: string
  reason?: string
}

// ─── Sources Health & Capabilities ──────────────────────────────────────────

export interface RucSourceHealth {
  source_id: string
  source_name: string
  source_type: RucSourceType
  status: 'OPERATIONAL' | 'DEGRADED' | 'DISABLED' | 'FAILED' | 'UNDER_REVIEW'
  priority: number
  last_successful_sync: string | null
  last_failure: string | null
  consecutive_failures: number
  active_dataset_version: string | null
  age_in_days: number
  freshness_status: RucFreshnessStatus
  capabilities: string[]
}

export interface RucCapabilities {
  can_lookup_RUC: boolean
  can_lookup_enriched_RUC: boolean
  can_view_annexes: boolean
  can_create_assisted_verification: boolean
  can_approve_assisted_verification: boolean
  can_apply_to_partner: boolean
  can_view_sources: boolean
  can_view_datasets: boolean
  can_start_import: boolean
  can_activate_dataset: boolean
  can_rollback_dataset: boolean
  can_use_authorized_provider: boolean
  can_view_technical_metrics: boolean
}
