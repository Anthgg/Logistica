/**
 * Tipos del dominio de control de puerta (Fase 037).
 *
 * Reglas:
 * - No se envían `guard_user_id`, `arrived_at` autoritativo, `decision_at`,
 *   `verification_passed`, `entry_authorized` ni flags locales.
 * - La hora oficial viene del backend.
 * - No se usa `any`.
 */

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ApiError {
  code: string
  message: string
  status: number | null
  details?: unknown
}

export interface FileAssetSummary {
  id: string
  name: string
  content_type: string | null
  size: number | null
  partial_hash: string | null
}

export interface UserSummary {
  id: string
  display_name: string
}

export interface WarehouseSummary {
  id: string
  code: string
  name: string
}

export interface SupplierSummary {
  id: string
  name: string
  code: string | null
}

export interface CarrierSummary {
  id: string
  name: string
  code: string | null
}

export interface VehicleSummary {
  id: string
  plate: string
  make: string | null
  model: string | null
  vehicle_type: string | null
  carrier_id: string | null
  carrier_name: string | null
  status: string
}

export interface DriverSummary {
  id: string
  full_name: string
  document_number_redacted: string
  license_number_redacted: string | null
  carrier_id: string | null
  carrier_name: string | null
}

export interface ReceptionAppointmentSummary {
  id: string
  cit_code: string
  warehouse_id: string
  warehouse_name: string
  gate_id: string | null
  gate_name: string | null
  date: string
  time_start: string
  time_end: string
  supplier_id: string | null
  supplier_name: string | null
  carrier_id: string | null
  carrier_name: string | null
  vehicle_id: string | null
  vehicle_plate: string | null
  driver_id: string | null
  driver_name_redacted: string | null
  driver_document_redacted: string | null
  seal_number_expected: string | null
  pallets: number | null
  packages: number | null
  weight: string | null
  special_requirements: string | null
  warnings: string[]
  status: string
  is_eligible: boolean
  po_codes: string[]
  guide_numbers: string[]
}

export interface ArrivalNoticeSummary {
  id: string
  appointment_id: string | null
  cit_code: string
  warehouse_id: string
  warehouse_name: string
  gate_id: string | null
  gate_name: string | null
  scheduled_at: string | null
  status: string
}

// ── Gates ────────────────────────────────────────────────────────────────────

export type WarehouseGateStatus = 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'
export type GateType = 'INBOUND' | 'OUTBOUND' | 'BIDIRECTIONAL'

export interface WarehouseGate {
  id: string
  code: string
  name: string
  warehouse_id: string
  warehouse_name: string
  type: GateType
  address: string | null
  timezone: string
  policy_id: string | null
  policy_name: string | null
  status: WarehouseGateStatus
  created_at: string
  updated_at: string
}

export interface WarehouseGateCreate {
  code: string
  name: string
  warehouse_id: string
  type: GateType
  address?: string | null
  timezone: string
  policy_id?: string | null
}

export interface WarehouseGateUpdate {
  name?: string
  address?: string | null
  timezone?: string
  policy_id?: string | null
}

export interface GateTodaySummary {
  gate_id: string
  expected_today: number
  upcoming_arrivals: number
  arrivals_registered: number
  verifications_in_progress: number
  held_at_gate: number
  waiting_supervisor: number
  authorized: number
  authorized_with_observations: number
  denied: number
  seals_observed: number
  documents_pending: number
  server_time: string
  timezone: string
}

// ── Políticas ────────────────────────────────────────────────────────────────

export interface GateVerificationCheckDefinition {
  id: string
  order: number
  code: string
  name: string
  description: string
  category: string
  is_required: boolean
  is_blocking: boolean
  evidence_required: boolean
  is_active: boolean
}

export interface GateVerificationPolicyVersion {
  id: string
  policy_id: string
  version: string
  status: 'DRAFT' | 'VALIDATED' | 'ACTIVE' | 'RETIRED' | 'ARCHIVED'
  effective_from: string | null
  effective_to: string | null
  checks: GateVerificationCheckDefinition[]
  partial_hash: string
  created_at: string
  updated_at: string
}

export interface GateVerificationPolicy {
  id: string
  code: string
  name: string
  description: string | null
  active_version_id: string | null
  active_version: GateVerificationPolicyVersion | null
  status: 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'
  created_at: string
  updated_at: string
}

export interface GateVerificationPolicyCreate {
  code: string
  name: string
  description?: string | null
}

export interface GateVerificationPolicyVersionCreate {
  version: string
}

// ── Check-in ─────────────────────────────────────────────────────────────────

export type GateCheckInStatus =
  | 'CREATED'
  | 'ARRIVED'
  | 'IN_VERIFICATION'
  | 'HELD'
  | 'WAITING_SUPERVISOR'
  | 'AUTHORIZED'
  | 'AUTHORIZED_WITH_OBSERVATIONS'
  | 'DENIED'
  | 'COMPLETED'
  | 'CANCELLED'

export type GateArrivalClassification = 'EARLY' | 'ON_TIME' | 'LATE' | 'WALK_IN' | 'UNKNOWN'

export type GateEntryDecisionType =
  | 'AUTHORIZE'
  | 'AUTHORIZE_WITH_OBSERVATIONS'
  | 'DENY'
  | 'HOLD'
  | 'REQUEST_SUPERVISOR'

export type GatePlateMatchStatus = 'MATCH' | 'MISMATCH' | 'FORMAT_VALID' | 'NOT_VERIFIED' | 'REQUIRES_REVIEW'
export type GateDriverMatchStatus = 'MATCH' | 'MISMATCH' | 'NOT_VERIFIED' | 'REQUIRES_REVIEW'
export type GateLicenseStatus = 'VALID' | 'EXPIRED' | 'NOT_MATCHING' | 'CATEGORY_MISMATCH' | 'NOT_VERIFIED' | 'REQUIRES_REVIEW'

export type GateVerificationState =
  | 'NOT_VERIFIED'
  | 'FORMAT_VALID'
  | 'VERIFIED_BY_SOURCE'
  | 'NOT_MATCHING'
  | 'REQUIRES_REVIEW'

export type GateCheckResultValue =
  | 'COMPLIANT'
  | 'COMPLIANT_WITH_OBSERVATION'
  | 'NON_COMPLIANT'
  | 'NOT_APPLICABLE'
  | 'NOT_VERIFIED'
  | 'REQUIRES_REVIEW'

export type GateExceptionStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED'

export type GateCorrectionStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'APPLIED'

export interface GateCheckInCapabilities {
  check_in_id: string
  can_view: boolean
  can_resolve_appointment: boolean
  can_create_check_in: boolean
  can_create_walk_in: boolean
  can_record_arrival: boolean
  can_start_verification: boolean
  can_manage_vehicle_inspection: boolean
  can_manage_driver_inspection: boolean
  can_manage_documents: boolean
  can_manage_seal: boolean
  can_capture_photo: boolean
  can_view_sensitive_photo: boolean
  can_manage_checks: boolean
  can_request_exception: boolean
  can_approve_exception: boolean
  can_hold: boolean
  can_request_supervisor: boolean
  can_authorize: boolean
  can_authorize_with_observations: boolean
  can_deny: boolean
  can_complete: boolean
  can_preview_CPV: boolean
  can_issue_CPV: boolean
  can_download_CPV: boolean
  can_request_correction: boolean
  can_view_history: boolean
  can_view_integrity: boolean
  can_view_dock_preparation: boolean
}

export interface GateVehicleInspection {
  id: string
  check_in_id: string
  expected_plate: string | null
  expected_vehicle_id: string | null
  expected_vehicle_summary: VehicleSummary | null
  observed_vehicle_id: string | null
  observed_vehicle_summary: VehicleSummary | null
  observed_plate: string | null
  plate_match_status: GatePlateMatchStatus
  legibility: string | null
  visual_condition: string | null
  observations: string | null
  photo_file_id: string | null
  photo_file: FileAssetSummary | null
  has_mismatch: boolean
}

export interface GateDriverInspection {
  id: string
  check_in_id: string
  expected_driver_id: string | null
  expected_driver_summary: DriverSummary | null
  observed_driver_id: string | null
  observed_driver_summary: DriverSummary | null
  declared_name: string | null
  document_number_redacted: string | null
  license_number_redacted: string | null
  license_category: string | null
  license_validity: string | null
  driver_match_status: GateDriverMatchStatus
  license_status: GateLicenseStatus
  photo_file_id: string | null
  photo_file: FileAssetSummary | null
  observations: string | null
}

export interface GatePresentedDocument {
  id: string
  check_in_id: string
  document_type: string
  expected: boolean
  presented: boolean
  serie: string | null
  number: string | null
  date: string | null
  issuer: string | null
  reference: string | null
  verification_state: GateVerificationState
  match_status: string | null
  file_id: string | null
  file: FileAssetSummary | null
  observations: string | null
}

export type GateSealPhysicalStatus =
  | 'INTACT'
  | 'BROKEN'
  | 'TAMPERED'
  | 'DAMAGED'
  | 'ABSENT'
  | 'ILLEGIBLE'
  | 'NOT_APPLICABLE'

export interface GateSealInspection {
  id: string
  check_in_id: string
  seal_required: boolean
  expected_number: string | null
  observed_number: string | null
  match_status: GateVerificationState
  physical_status: GateSealPhysicalStatus
  photo_file_id: string | null
  photo_file: FileAssetSummary | null
  observations: string | null
  is_critical: boolean
}

export type GatePhotoEvidenceType =
  | 'VEHICLE'
  | 'PLATE'
  | 'DRIVER_RESTRICTED'
  | 'DOCUMENT'
  | 'GUIDE'
  | 'SEAL'
  | 'EXTERIOR_CONDITION'
  | 'SECURITY'

export interface GatePhotoEvidence {
  id: string
  check_in_id: string
  evidence_type: GatePhotoEvidenceType
  file: FileAssetSummary
  classification: string
  captured_by: string | null
  captured_at: string
  is_sensitive: boolean
  requires_additional_permission: boolean
  can_view: boolean
}

export interface GateCheckResult {
  id: string
  check_in_id: string
  check_definition_id: string
  check_code: string
  check_name: string
  order: number
  category: string
  is_required: boolean
  is_blocking: boolean
  result: GateCheckResultValue
  evidence_file_id: string | null
  observation: string | null
  exception_id: string | null
  exception_status: GateExceptionStatus | null
  has_exception: boolean
}

export interface GateCheckResultInput {
  check_definition_id: string
  result: GateCheckResultValue
  evidence_file_id?: string | null
  observation?: string | null
}

export interface GateVerificationProgress {
  total_checks: number
  completed: number
  pending: number
  failed: number
  blocking: number
  warnings: number
  evidence_pending: number
  exceptions_pending: number
  can_proceed_to_decision: boolean
}

export interface GateVerificationException {
  id: string
  check_in_id: string
  type: string
  check_id: string | null
  check_code: string | null
  reason: string
  risk_level_shown: string | null
  evidence_file_id: string | null
  comment: string | null
  requested_by: string | null
  requested_at: string
  reviewed_by: string | null
  reviewed_at: string | null
  decision: 'APPROVED' | 'REJECTED' | null
  review_comment: string | null
  status: GateExceptionStatus
  impact: string | null
}

export interface GateExceptionCreate {
  type: string
  check_id?: string | null
  reason: string
  evidence_file_id?: string | null
  comment?: string | null
}

export interface GateEntryDecision {
  id: string
  check_in_id: string
  decision_type: GateEntryDecisionType
  decided_by: string | null
  decided_at: string | null
  conditions: string | null
  final_observation: string | null
  supervisor_id: string | null
  failures_summary: string | null
  risks_summary: string | null
  is_final: boolean
}

export interface GateEntryDecisionValidation {
  check_in_id: string
  is_valid: boolean
  errors: Array<{ code: string; message: string; field: string | null }>
  warnings: Array<{ code: string; message: string }>
  checks: Array<{
    code: string
    label: string
    status: 'PASS' | 'FAIL' | 'WARN'
    detail: string | null
  }>
  allowed_actions: GateEntryDecisionType[]
}

export interface GateCheckInCorrection {
  id: string
  check_in_id: string
  field: string
  original_value_redacted: string
  proposed_value: string
  reason: string
  evidence_file_id: string | null
  requested_by: string | null
  requested_at: string
  reviewed_by: string | null
  reviewed_at: string | null
  status: GateCorrectionStatus
}

export interface GateCheckInCorrectionCreate {
  field: string
  proposed_value: string
  reason: string
  evidence_file_id?: string | null
}

export interface GateIntegrityStatus {
  check_in_id: string
  revision_hash: string | null
  checklist_hash: string | null
  evidence_hash: string | null
  decision_hash: string | null
  snapshot_hash: string | null
  cpv_hash: string | null
  algorithm: string | null
  last_verified_at: string | null
  status: 'VERIFIED' | 'NOT_VERIFIED' | 'MISMATCH' | 'INCOMPLETE'
}

// ── CPV ───────────────────────────────────────────────────────────────────────

export interface GateCpvDocumentResponse {
  document_instance_id: string
  check_in_id: string
  document_code: string | null
  status: string
  issued_at: string | null
  snapshot_hash: string | null
  download_url: string
  expires_at: string | null
}

export interface GatePreviewResponse {
  check_in_id: string
  preview_data: unknown
}

/** @deprecated Alias mantenido para compatibilidad; usar GateCpvDocumentResponse */
export type GateControlDocument = GateCpvDocumentResponse

export interface GateControlPackage {
  id: string
  check_in_id: string
  status: 'QUEUED' | 'GENERATING' | 'AVAILABLE' | 'FAILED' | 'EXPIRED'
  includes_cpv: boolean
  includes_cit: boolean
  evidence_count: number
  document_count: number
  has_personal_photos: boolean
  file: FileAssetSummary | null
  requested_at: string
  expires_at: string | null
  created_at: string
}

// ── Preparación Fase 038 ──────────────────────────────────────────────────────

export interface DockAssignmentPreparation {
  check_in_id: string
  cpv_code: string | null
  cit_code: string | null
  warehouse_id: string
  warehouse_name: string
  gate_id: string | null
  gate_name: string | null
  supplier_name: string | null
  vehicle_plate: string | null
  driver_name_redacted: string | null
  arrived_at: string | null
  decision_type: GateEntryDecisionType | null
  conditions: string | null
  seal_number: string | null
  documents_count: number
  special_requirements: string | null
  pallets: number | null
  packages: number | null
  weight: string | null
  warnings: string[]
  queue_entry_id?: string | null
}

// ── Historial ────────────────────────────────────────────────────────────────

export interface GateCheckInHistoryEvent {
  id: string
  check_in_id: string
  action: string
  previous_state: string | null
  new_state: string | null
  reason: string | null
  result: string
  actor_display_name: string | null
  effective_actor_display_name: string | null
  occurred_at: string
}

// ── Check-in raíz ─────────────────────────────────────────────────────────────

export interface GateCheckIn {
  id: string
  cpv_code: string | null
  cit_code: string | null
  warehouse_id: string
  warehouse_name: string
  gate_id: string | null
  gate_name: string | null
  status: GateCheckInStatus
  decision_type: GateEntryDecisionType | null
  appointment_id: string | null
  is_walk_in: boolean
  expected_plate: string | null
  observed_plate: string | null
  supplier_name: string | null
  carrier_name: string | null
  driver_name_redacted: string | null
  arrived_at: string | null
  arrival_classification: GateArrivalClassification
  server_time: string | null
  timezone: string | null
  guard_display_name: string | null
  has_mismatches: boolean
  has_exceptions: boolean
  has_seal_issue: boolean
  has_missing_documents: boolean
  has_blocking_failures: boolean
  is_ready_for_decision: boolean
  completed_at: string | null
  cancelled_at: string | null
  created_at: string
  updated_at: string
}

export type GateCheckInSummary = GateCheckIn

export interface GateCheckInListQuery {
  page?: number
  page_size?: number
  search?: string
  warehouse_id?: string | null
  gate_id?: string | null
  status?: GateCheckInStatus | null
  decision_type?: GateEntryDecisionType | null
  supplier_id?: string | null
  carrier_id?: string | null
  plate?: string | null
  date_from?: string | null
  date_to?: string | null
  with_failures?: boolean
  with_exceptions?: boolean
  with_broken_seal?: boolean
  with_missing_documents?: boolean
  walk_in_only?: boolean
  tab?: 'expected' | 'at_gate' | 'in_verification' | 'held' | 'finished' | null
}

export interface GateCheckInCreate {
  gate_id: string
  appointment_id: string
  is_walk_in?: boolean
}

export interface GateArrivalRecord {
  check_in_id: string
  arrived_at: string
  classification: GateArrivalClassification
  server_time: string
  timezone: string
}

export interface GateResolveAppointmentRequest {
  cit_code?: string | null
  qr_payload?: string | null
  plate?: string | null
  po_code?: string | null
  warehouse_id?: string | null
}

export interface GateCheckInDetail extends GateCheckIn {
  appointment: ReceptionAppointmentSummary | null
  vehicle_inspection: GateVehicleInspection | null
  driver_inspection: GateDriverInspection | null
  presented_documents: GatePresentedDocument[]
  seal_inspection: GateSealInspection | null
  photos: GatePhotoEvidence[]
  check_results: GateCheckResult[]
  progress: GateVerificationProgress | null
  exceptions: GateVerificationException[]
  decision: GateEntryDecision | null
  document: GateControlDocument | null
  integrity: GateIntegrityStatus | null
  capabilities: GateCheckInCapabilities | null
}