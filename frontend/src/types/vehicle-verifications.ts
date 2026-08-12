// ─── Vehicle Verifications – Strict TypeScript Types ────────────────────────

export type VehicleVerificationDomain =
  | 'REGISTRO_PROPIEDAD'
  | 'PROPIETARIO'
  | 'CARACTERISTICAS'
  | 'ESTADO_REGISTRAL'
  | 'GRAVAMENES'
  | 'AUTORIZACION_TRANSPORTE'
  | 'HABILITACION_CARRIER'
  | 'REVISION_TECNICA'
  | 'SOAT'
  | 'CAT'
  | 'SEGURO'
  | 'PERMISO_OPERATIVO'
  | 'REFRIGERACION'
  | 'MERCANCIAS_PELIGROSAS'

export type VehicleVerificationSourceType =
  | 'SUNARP'
  | 'MTC'
  | 'SBS'
  | 'AUTHORIZED_PROVIDER'
  | 'ASSISTED_MANUAL'
  | 'DOCUMENTARY_REVIEW'
  | 'INTERNAL'

export type VehicleVerificationMethod =
  | 'AUTHORIZED_API'
  | 'AUTHORIZED_BATCH'
  | 'ASSISTED_MANUAL'
  | 'DOCUMENTARY_REVIEW'

export type VehicleVerificationStatus =
  | 'REQUESTED'
  | 'QUEUED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'
  | 'UNDER_REVIEW'

export type VehicleVerificationResultStatus =
  | 'VALIDATED'
  | 'OBSERVED'
  | 'MISMATCH'
  | 'NOT_FOUND'
  | 'EXPIRED'
  | 'UNAVAILABLE'

export type VehicleVerificationFreshness =
  | 'FRESH'
  | 'AGING'
  | 'STALE'
  | 'CRITICAL'
  | 'EXPIRED'
  | 'UNKNOWN'

export type VehicleVerificationConflictStatus =
  | 'OPEN'
  | 'UNDER_REVIEW'
  | 'RESOLVED_KEEP_MASTER'
  | 'RESOLVED_APPLY_VERIFIED'
  | 'RESOLVED_MANUAL_ENTRY'
  | 'DISMISSED'

// ─── Verification Entities ──────────────────────────────────────────────────

export interface VehicleVerificationFieldProvenance {
  field_name: string
  field_label: string
  master_value: string | null
  verified_value: string | null
  source_type: VehicleVerificationSourceType
  source_name: string
  verification_date: string
  confidence_score: number // float between 0 and 1 provided by backend
  is_selected: boolean
  has_conflict: boolean
}

export interface VehicleVerificationEvidence {
  id: string
  evidence_type: string
  file_name: string
  file_reference_id: string | null
  partial_hash: string
  uploaded_by_user_name: string
  created_at: string
  notes: string | null
}

export interface VehicleVerification {
  id: string
  vehicle_id: string
  vehicle_internal_code: string
  plate_number: string
  domain: VehicleVerificationDomain
  domain_label: string
  status: VehicleVerificationStatus
  result_status: VehicleVerificationResultStatus
  source_type: VehicleVerificationSourceType
  source_name: string
  method: VehicleVerificationMethod
  source_date: string | null
  requested_at: string
  completed_at: string | null
  expires_at: string | null
  freshness: VehicleVerificationFreshness
  days_until_expiration: number | null
  confidence_score: number | null
  provenance_fields: VehicleVerificationFieldProvenance[]
  evidences: VehicleVerificationEvidence[]
  conflicts_count: number
  warnings: string[]
  requested_by_user_name: string
  capabilities: VehicleVerificationCapabilities
  history: VehicleVerificationHistoryEvent[]
}

export interface VehicleVerificationSummary {
  id: string
  vehicle_id: string
  plate_number: string
  make_model_summary: string
  domain: VehicleVerificationDomain
  domain_label: string
  status: VehicleVerificationStatus
  result_status: VehicleVerificationResultStatus
  source_type: VehicleVerificationSourceType
  source_name: string
  freshness: VehicleVerificationFreshness
  expiration_date: string | null
  conflicts_count: number
  updated_at: string
}

export interface VehicleVerificationRequest {
  vehicle_id: string
  plate_number: string
  domain: VehicleVerificationDomain
  preferred_source?: VehicleVerificationSourceType
  allow_authorized_provider?: boolean
  reason: string
  purpose?: string
}

export interface AssistedVehicleVerificationCreate {
  vehicle_id: string
  plate_number: string
  domain: VehicleVerificationDomain
  source_type: VehicleVerificationSourceType
  official_reference_number: string
  observation_timestamp: string
  observed_plate: string
  observed_owner_name?: string
  observed_make_name?: string
  observed_model_name?: string
  observed_year?: number
  observed_status: string
  observed_expiration_date?: string
  result_status: VehicleVerificationResultStatus
  notes: string
  evidence_file_reference_id?: string
}

export interface AssistedVehicleVerification {
  id: string
  vehicle_id: string
  plate_number: string
  domain: VehicleVerificationDomain
  source_type: VehicleVerificationSourceType
  official_reference_number: string
  observation_timestamp: string
  observed_plate: string
  observed_owner_name: string | null
  observed_make_name: string | null
  observed_model_name: string | null
  observed_year: number | null
  observed_status: string
  observed_expiration_date: string | null
  result_status: VehicleVerificationResultStatus
  notes: string
  created_by_user_name: string
  review_status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED'
  approved_by_user_name: string | null
  approved_at: string | null
  created_at: string
}

export interface VehicleVerificationConflict {
  id: string
  verification_id: string
  vehicle_id: string
  plate_number: string
  domain: VehicleVerificationDomain
  field_name: string
  field_label: string
  master_value: string
  verified_value: string
  source_name: string
  source_date: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: VehicleVerificationConflictStatus
  resolution_notes: string | null
  resolved_by_user_name: string | null
  resolved_at: string | null
  created_at: string
}

export interface VehicleVerificationConflictResolve {
  resolution_strategy: 'KEEP_MASTER' | 'APPLY_VERIFIED' | 'MANUAL_ENTRY' | 'DISMISS'
  manual_value?: string
  reason: string
}

export interface VehicleVerificationApplyRequest {
  expected_vehicle_version: number
  selected_fields: string[] // field names to apply
  reason: string
}

export interface VehicleVerificationRequirement {
  id: string
  vehicle_type: string
  body_type: string | null
  ownership_type: string | null
  carrier_category: string | null
  domain: VehicleVerificationDomain
  preferred_source: VehicleVerificationSourceType
  is_mandatory: boolean
  is_blocking: boolean
  max_age_days: number
  warning_days: number
  min_confidence_score: number
  allow_assisted_validation: boolean
  evidence_required: boolean
  status: 'DRAFT' | 'ACTIVE' | 'RETIRED'
  created_at: string
}

export interface VehicleVerificationRequirementCreate {
  vehicle_type: string
  body_type?: string
  ownership_type?: string
  carrier_category?: string
  domain: VehicleVerificationDomain
  preferred_source: VehicleVerificationSourceType
  is_mandatory?: boolean
  is_blocking?: boolean
  max_age_days?: number
  warning_days?: number
  min_confidence_score?: number
  allow_assisted_validation?: boolean
  evidence_required?: boolean
}

export interface VehicleVerificationRequirementUpdate {
  preferred_source?: VehicleVerificationSourceType
  is_mandatory?: boolean
  is_blocking?: boolean
  max_age_days?: number
  warning_days?: number
  min_confidence_score?: number
  allow_assisted_validation?: boolean
  evidence_required?: boolean
}

export interface VehicleVerificationConflictReviewStart {
  notes?: string
}

export interface VehicleVerificationReviewTaskAssign {
  assigned_to_user_id?: string
}

export interface VehicleVerificationReviewTaskComplete {
  outcome: string
  notes?: string
}

export interface VehicleVerificationReviewTaskStart {
  notes?: string
}

export interface VehicleVerificationHistoryEvent {
  id: string
  event_type:
    | 'REQUESTED'
    | 'STARTED'
    | 'COMPLETED'
    | 'FAILED'
    | 'RETRIED'
    | 'EXPIRED'
    | 'REPLACED'
    | 'REVOKED'
    | 'EVIDENCE_ASSOCIATED'
    | 'CONFLICT_DETECTED'
    | 'CONFLICT_RESOLVED'
    | 'DATA_APPLIED'
    | 'ASSISTED_VALIDATION'
    | 'PROVIDER_CALLED'
    | 'PROVIDER_DEGRADED'
    | string
  user_name: string | null
  source_name: string | null
  domain_label: string | null
  result_status: string | null
  reason: string | null
  vehicle_version: number | null
  correlation_id_prefix: string | null
  created_at: string
}

export interface VehicleVerificationSourceHealth {
  id: string
  source_type: VehicleVerificationSourceType
  source_name: string
  authority_name: string
  supported_domains: VehicleVerificationDomain[]
  method: VehicleVerificationMethod
  authorization_status: 'AUTHORIZED' | 'PENDING' | 'REVOKED'
  operational_status: 'OPERATIONAL' | 'DEGRADED' | 'DISABLED' | 'FAILED' | 'UNDER_REVIEW'
  last_successful_call_at: string | null
  last_failure_at: string | null
  consecutive_failures_count: number
  latency_ms: number | null
  circuit_breaker_open: boolean
  rate_limit_per_minute: number | null
}

export interface VehicleVerificationReviewTask {
  id: string
  vehicle_id: string
  plate_number: string
  domain: VehicleVerificationDomain
  reason: string
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
  due_date: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
  assigned_to_user_name: string | null
  suggested_source: VehicleVerificationSourceType
  created_at: string
}

export interface VehicleVerificationCompliance {
  vehicle_id: string
  general_status: 'COMPLIANT' | 'PARTIAL' | 'NON_COMPLIANT' | 'EXPIRED' | 'UNDER_REVIEW'
  required_domains_count: number
  validated_domains_count: number
  missing_domains_count: number
  expired_domains_count: number
  open_conflicts_count: number
  blocking_reasons: string[]
  warnings: string[]
  evaluation_date: string
}

export interface VehicleVerificationCapabilities {
  can_view_verifications: boolean
  can_request_verification: boolean
  can_retry_verification: boolean
  can_revoke_verification: boolean
  can_view_sensitive_result: boolean
  can_create_assisted_verification: boolean
  can_approve_assisted_verification: boolean
  can_apply_result: boolean
  can_resolve_conflict: boolean
  can_view_evidence: boolean
  can_manage_evidence: boolean
  can_view_sources: boolean
  can_manage_sources: boolean
  can_view_requirements: boolean
  can_manage_requirements: boolean
  can_activate_requirements: boolean
  can_view_review_tasks: boolean
}

export interface VehicleVerificationListQuery {
  page?: number
  page_size?: number
  vehicle_id?: string
  plate?: string
  domain?: VehicleVerificationDomain
  source_type?: VehicleVerificationSourceType
  status?: VehicleVerificationStatus
  result_status?: VehicleVerificationResultStatus
  freshness?: VehicleVerificationFreshness
  has_conflict?: boolean
  has_evidence?: boolean
}

export interface VehicleVerificationStats {
  total_verifications: number
  fresh_count: number
  expiring_soon_count: number
  expired_count: number
  conflicted_count: number
  degraded_sources_count: number
  pending_tasks_count: number
}
