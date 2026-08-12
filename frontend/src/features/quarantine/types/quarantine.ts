// ── Fase 042 — Tipos de cuarentena y liberación ────────────────────────────────

// ── Primitivos reutilizados ─────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
  cursor?: string | null
}

export interface DecimalValue {
  value: string
  scale: number
}

export interface UserSummary {
  user_id: string
  display_name: string
  email?: string
}

export interface FileAssetSummary {
  file_id: string
  filename: string
  mime_type: string
  size_bytes: number
  upload_session_id?: string
  url?: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
  status?: number
}

// ── Resúmenes de dominio ────────────────────────────────────────────────────────

export interface ProductSummary {
  product_id: string
  sku: string
  name: string
  description?: string
  barcode?: string
  category?: string
  category_id?: string
  unit_id?: string
  unit_name?: string
  temperature_declared?: string | null
  status?: string
  tracking?: ProductTrackingPolicySummary
}

export interface ProductTrackingPolicySummary {
  requires_lot: boolean
  requires_serial: boolean
  requires_expiration: boolean
  serial_uniqueness: 'GLOBAL' | 'PRODUCT' | 'INCONCLUSIVE'
  lot_format?: string
  serial_format?: string
}

export interface WarehouseSummary {
  warehouse_id: string
  name: string
  code: string
}

export interface UnitOfMeasureSummary {
  unit_id: string
  code: string
  name: string
  symbol: string
  unit_type: string
}

export interface BusinessPartnerSummary {
  partner_id: string
  name: string
  trade_name?: string
  document_type: string
  document_number: string
  roles: string[]
}

export interface WarehouseLocationSummary {
  location_id: string
  code: string
  name: string
  zone: string | null
  aisle: string | null
  rack: string | null
  level: string | null
  position: string | null
  location_type: string
  status: string
}

export interface InboundReceiptSummary {
  receipt_id: string
  code: string
  cpv_code: string | null
  cit_code: string | null
  supplier_name: string
  warehouse_name: string
  status: string
  completion_classification: string | null
}

export interface ReceptionDifferenceSummary {
  case_id: string
  case_code: string | null
  receipt_id: string
  receipt_code: string
  supplier_name: string
  warehouse_name: string
  severity: string
  items_count: number
  status: string
  created_at: string
}

// ── Asignación de disposición de inventario ─────────────────────────────────────

export type InventoryDispositionAllocationStatus =
  | 'PENDING_EVALUATION'
  | 'QUARANTINE_REQUIRED'
  | 'QUARANTINED'
  | 'INSPECTION_PENDING'
  | 'INSPECTION_IN_PROGRESS'
  | 'DECISION_PENDING'
  | 'QUALITY_APPROVED'
  | 'RELEASE_REQUESTED'
  | 'RELEASE_APPROVED'
  | 'RELEASED_FOR_PUTAWAY'
  | 'REJECTED'
  | 'REINSPECTION_PENDING'
  | 'CLOSED'
  | 'CANCELLED'

export type InventoryAvailabilityClass =
  | 'BLOCKED_QUARANTINE'
  | 'AVAILABLE_FOR_PUTAWAY'
  | 'REJECTED_NOT_AVAILABLE'
  | 'PARTIAL_RELEASE'
  | 'PENDING_EVALUATION'

export type InventoryQualityStatus =
  | 'NOT_EVALUATED'
  | 'PASS'
  | 'PASS_WITH_OBSERVATIONS'
  | 'FAIL'
  | 'INCONCLUSIVE'
  | 'REINSPECTION_REQUIRED'

export interface InboundInventoryDispositionAllocation {
  allocation_id: string
  receipt_line_id: string
  receipt_id: string
  receipt_code: string
  product: ProductSummary
  warehouse: WarehouseSummary
  expected_quantity: string
  received_quantity: string
  allocated_quantity: string
  released_quantity: string
  rejected_quantity: string
  quarantined_quantity: string
  unit: UnitOfMeasureSummary
  availability_class: InventoryAvailabilityClass
  quality_status: InventoryQualityStatus
  disposition_status: InventoryDispositionAllocationStatus
  quarantine_case_id: string | null
  quarantine_case_code: string | null
  inspection_id: string | null
  inspection_code: string | null
  disposition_decision_id: string | null
  release_authorization_id: string | null
  rejection_authorization_id: string | null
  lot_number: string | null
  serial_number: string | null
  expiration_date: string | null
  batch_reference: string | null
  requires_inspection: boolean
  requires_certificate_review: boolean
  is_reinspection: boolean
  reinspection_of_allocation_id: string | null
  notes: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

export interface InboundInventoryDispositionAllocationSummary {
  total_allocations: number
  pending_evaluation: number
  quarantined: number
  inspection_pending: number
  inspection_in_progress: number
  decision_pending: number
  quality_approved: number
  release_requested: number
  released_for_putaway: number
  rejected: number
  reinspection_pending: number
  closed: number
  cancelled: number
  total_quantity: string
  quarantined_quantity: string
  released_quantity: string
  rejected_quantity: string
  pending_quantity: string
}

export interface InventoryDispositionSplit {
  allocation_id: string
  original_quantity: string
  released_quantity: string
  rejected_quantity: string
  remaining_quantity: string
  unit: UnitOfMeasureSummary
  split_history: InventoryDispositionSplitRecord[]
}

export interface InventoryDispositionSplitRecord {
  split_id: string
  allocation_id: string
  split_type: 'RELEASE' | 'REJECTION' | 'REINSPECTION'
  quantity: string
  destination: string | null
  reason: string | null
  authorized_by: UserSummary | null
  created_at: string
}

// ── Caso de cuarentena ──────────────────────────────────────────────────────────

export type QualityQuarantineCaseStatus =
  | 'OPEN'
  | 'PENDING_INSPECTION'
  | 'UNDER_INSPECTION'
  | 'INSPECTION_COMPLETED'
  | 'DECISION_PENDING'
  | 'APPROVED_FOR_RELEASE'
  | 'RELEASE_REQUESTED'
  | 'RELEASED'
  | 'REJECTED'
  | 'REINSPECTION_REQUIRED'
  | 'PARTIALLY_RELEASED'
  | 'CLOSED'
  | 'CANCELLED'

export type QuarantineReason =
  | 'RECEPTION_DISCREPANCY'
  | 'DAMAGE'
  | 'EXPIRATION'
  | 'TEMPERATURE_DEVIATION'
  | 'MISSING_CERTIFICATE'
  | 'DOCUMENT_ANOMALY'
  | 'BROKEN_SEAL'
  | 'MANUAL_RETENTION'
  | 'OTHER'

export interface QualityQuarantineCase {
  case_id: string
  case_code: string | null
  title: string
  description: string | null
  status: QualityQuarantineCaseStatus
  reason: QuarantineReason
  priority: number
  severity: string
  receipt_id: string | null
  receipt_code: string | null
  difference_case_id: string | null
  difference_case_code: string | null
  warehouse: WarehouseSummary
  supplier: BusinessPartnerSummary | null
  product: ProductSummary | null
  total_quantity: string
  quarantined_quantity: string
  released_quantity: string
  rejected_quantity: string
  unit: UnitOfMeasureSummary | null
  quarantine_zone_id: string | null
  quarantine_zone_name: string | null
  allocation_ids: string[]
  allocation_count: number
  inspection_id: string | null
  inspection_code: string | null
  has_disposition_decision: boolean
  disposition_decision_type: string | null
  disposition_decision_id?: string | null
  has_release_authorization: boolean
  has_rejection_authorization: boolean
  has_reinspection_request: boolean
  has_non_conformity: boolean
  evidence_count: number
  certificate_review_count: number
  history_count: number
  locked_by: UserSummary | null
  locked_at: string | null
  due_date: string | null
  resolved_at: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

export interface QualityQuarantineCaseSummary {
  total_cases: number
  open_cases: number
  pending_inspection: number
  under_inspection: number
  decision_pending: number
  approved_for_release: number
  released: number
  rejected: number
  reinspection_required: number
  partially_released: number
  closed: number
  cancelled: number
  overdue_cases: number
  total_quarantined_quantity: string
  total_released_quantity: string
  total_rejected_quantity: string
  quarantine_zones_active: number
}

// ── Zona de cuarentena ──────────────────────────────────────────────────────────

export type QuarantineZoneStatus = 'ACTIVE' | 'BLOCKED' | 'ARCHIVED'

export interface QuarantineZone {
  zone_id: string
  code: string
  name: string
  description: string | null
  warehouse: WarehouseSummary
  zone_type: string
  status: QuarantineZoneStatus
  capacity: string | null
  capacity_unit: UnitOfMeasureSummary | null
  current_occupancy: string
  occupancy_percentage: string | null
  current_cases: number
  total_locations: number
  active_locations: number
  temperature_controlled: boolean
  min_temperature: string | null
  max_temperature: string | null
  access_restricted: boolean
  allowed_reasons: QuarantineReason[]
  blocked_reason: string | null
  blocked_at: string | null
  blocked_by: UserSummary | null
  last_inspection_at: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

// ── Ubicación de cuarentena ─────────────────────────────────────────────────────

export type QuarantinePlacementStatus = 'PENDING' | 'CONFIRMED' | 'SUPERSEDED'

export interface QuarantinePlacement {
  placement_id: string
  case_id: string
  case_code: string | null
  allocation_id: string | null
  zone: QuarantineZone
  location: WarehouseLocationSummary
  quantity: string
  unit: UnitOfMeasureSummary
  lot_number: string | null
  serial_number: string | null
  status: QuarantinePlacementStatus
  placed_by: UserSummary
  confirmed_by: UserSummary | null
  superseded_by: QuarantinePlacement | null
  superseded_at: string | null
  superseded_reason: string | null
  label_code: string | null
  notes: string | null
  placed_at: string
  confirmed_at: string | null
  created_at: string
  updated_at: string
}

// ── Inspección de calidad ───────────────────────────────────────────────────────

export type QualityInspectionStatus =
  | 'MATERIALIZED'
  | 'PENDING_START'
  | 'IN_PROGRESS'
  | 'PAUSED'
  | 'VALIDATING'
  | 'COMPLETED'
  | 'CANCELLED'

export type QualityInspectionOverallResult =
  | 'PASS'
  | 'PASS_WITH_OBSERVATIONS'
  | 'FAIL'
  | 'INCONCLUSIVE'
  | 'REINSPECTION_REQUIRED'
  | 'NOT_COMPUTED'

export interface QualityInspection {
  inspection_id: string
  inspection_code: string | null
  case_id: string
  case_code: string | null
  allocation_id: string | null
  plan_id: string | null
  plan_code: string | null
  plan_version_id: string | null
  status: QualityInspectionStatus
  overall_result: QualityInspectionOverallResult
  inspection_type: string
  product: ProductSummary | null
  warehouse: WarehouseSummary
  total_quantity: string
  sample_quantity: string
  unit: UnitOfMeasureSummary | null
  lot_number: string | null
  serial_number: string | null
  control_count: number
  controls_completed: number
  controls_passed: number
  controls_failed: number
  controls_with_observations: number
  controls_not_applicable: number
  measurement_count: number
  sample_set_count: number
  evidence_count: number
  certificate_review_count: number
  has_disposition_decision: boolean
  disposition_decision_type: string | null
  requires_reinspection: boolean
  reinspection_of_inspection_id: string | null
  inspector: UserSummary | null
  reviewer: UserSummary | null
  started_at: string | null
  paused_at: string | null
  completed_at: string | null
  reviewed_at: string | null
  cancelled_at: string | null
  cancellation_reason: string | null
  estimated_duration_minutes: number | null
  actual_duration_minutes: number | null
  notes: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

export interface QualityInspectionSummary {
  total_inspections: number
  materialized: number
  pending_start: number
  in_progress: number
  paused: number
  validating: number
  completed: number
  cancelled: number
  passed: number
  passed_with_observations: number
  failed: number
  inconclusive: number
  reinspection_required: number
  average_duration_minutes: string | null
  inspections_today: number
  overdue_inspections: number
}

// ── Control de inspección de calidad ────────────────────────────────────────────

export type QualityInspectionControlStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'NOT_APPLICABLE'
  | 'FAILED'
  | 'CORRECTED'

export type QualityControlResultStatus =
  | 'PENDING'
  | 'RECORDED'
  | 'VALIDATED'
  | 'CORRECTED'
  | 'SUPERSEDED'

export interface QualityInspectionControl {
  control_id: string
  inspection_id: string
  definition_control_id: string
  code: string
  name: string
  description: string | null
  instructions?: string | null
  control_type: string
  display_order: number
  required: boolean
  blocking_future: boolean
  evidence_required: boolean
  result_value_type: string
  status: QualityInspectionControlStatus
  result_status: QualityControlResultStatus
  result_value: string | null
  result_text: string | null
  result_boolean: boolean | null
  result_file_id: string | null
  unit: UnitOfMeasureSummary | null
  expected_value: string | null
  min_value: string | null
  max_value: string | null
  tolerance_result: QualityToleranceResult
  measurements: QualityMeasurement[]
  evidence: QualityInspectionEvidence[]
  certificate_reviews: QualityCertificateReview[]
  sample_references: QualityInspectionSampleReference[]
  condition_results: QualityControlConditionResult[]
  is_blocking: boolean
  blocking_reason: string | null
  corrected_by: UserSummary | null
  corrected_at: string | null
  correction_reason: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface QualityInspectionControlResult {
  result_id: string
  control_id: string
  inspection_id: string
  status: QualityControlResultStatus
  result_value: string | null
  result_text: string | null
  result_boolean: boolean | null
  result_file_id: string | null
  tolerance_result: QualityToleranceResult
  deviations: QualityMeasurementDeviation[]
  recorded_by: UserSummary
  validated_by: UserSummary | null
  corrected_by: UserSummary | null
  superseded_by: UserSummary | null
  correction_reason: string | null
  supersession_reason: string | null
  recorded_at: string
  validated_at: string | null
  corrected_at: string | null
  superseded_at: string | null
  created_at: string
  updated_at: string
}

export interface QualityControlConditionResult {
  condition_id: string
  control_id: string
  condition_field: string
  operator: string
  expected_value: string | null
  actual_value: string | null
  met: boolean
}

// ── Mediciones de calidad ───────────────────────────────────────────────────────

export type QualityMeasurementType =
  | 'WEIGHT'
  | 'TEMPERATURE'
  | 'LENGTH'
  | 'WIDTH'
  | 'HEIGHT'
  | 'VOLUME'
  | 'COUNT'
  | 'DENSITY'
  | 'HUMIDITY'
  | 'OTHER'

export type QualityToleranceResult =
  | 'WITHIN_TOLERANCE'
  | 'OUTSIDE_TOLERANCE'
  | 'NO_TOLERANCE_DEFINED'
  | 'NOT_EVALUATED'

export interface QualityMeasurement {
  measurement_id: string
  control_id: string
  inspection_id: string
  measurement_type: QualityMeasurementType
  value: string
  unit: UnitOfMeasureSummary
  target_value: string | null
  min_value: string | null
  max_value: string | null
  tolerance_result: QualityToleranceResult
  deviation: string | null
  deviation_percentage: string | null
  measurement_point: number | null
  device_id: string | null
  device_name: string | null
  calibrated: boolean | null
  calibration_date: string | null
  environment_conditions: string | null
  notes: string | null
  recorded_by: UserSummary
  recorded_at: string
  created_at: string
}

export interface QualityMeasurementDeviation {
  measurement_id: string
  measurement_type: QualityMeasurementType
  expected_value: string
  actual_value: string
  deviation: string
  deviation_percentage: string
  within_tolerance: boolean
  severity: 'NONE' | 'MINOR' | 'MODERATE' | 'MAJOR' | 'CRITICAL'
}

// ── Muestras de calidad ─────────────────────────────────────────────────────────

export interface QualityInspectionSampleSet {
  sample_set_id: string
  inspection_id: string
  control_id: string | null
  sample_unit: string
  population_size: string
  calculated_sample_size: string
  actual_sample_size: string
  selection_method: string
  rounding_mode: string
  minimum_applied: boolean
  maximum_applied: boolean
  samples: QualityInspectionSampleReference[]
  notes: string | null
  created_at: string
  updated_at: string
}

export interface QualityInspectionSampleReference {
  reference_id: string
  sample_set_id: string
  inspection_id: string
  sample_number: number
  lot_number: string | null
  serial_number: string | null
  package_code: string | null
  location_code: string | null
  selected_by: string
  selected_at: string
  inspected: boolean
  inspection_result: string | null
  notes: string | null
}

// ── Revisión de certificados ────────────────────────────────────────────────────

export type QualityCertificateReviewStatus =
  | 'PENDING'
  | 'UPLOADED'
  | 'VERIFIED'
  | 'MISSING'
  | 'ILLEGIBLE'
  | 'REVIEW_REQUESTED'

export interface QualityCertificateReview {
  review_id: string
  inspection_id: string
  control_id: string | null
  case_id: string | null
  allocation_id: string | null
  requirement_id: string | null
  requirement_name: string | null
  document_type: string | null
  status: QualityCertificateReviewStatus
  file: FileAssetSummary | null
  file_name: string | null
  file_hash: string | null
  issuer: string | null
  reference_number: string | null
  issue_date: string | null
  expiration_date: string | null
  is_expired: boolean | null
  days_until_expiration: number | null
  metadata_valid: boolean | null
  metadata_errors: string[]
  reviewer_notes: string | null
  reviewed_by: UserSummary | null
  reviewed_at: string | null
  upload_session_id: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

// ── Evidencia de inspección ─────────────────────────────────────────────────────

export interface QualityInspectionEvidence {
  evidence_id: string
  inspection_id: string
  control_id: string | null
  case_id: string | null
  evidence_type: string
  file: FileAssetSummary
  classification: string | null
  partial_hash: string | null
  anti_malware_status: string | null
  description: string | null
  tags: string[]
  is_sensitive: boolean
  uploaded_by: UserSummary
  created_at: string
}

// ── Decisión de disposición ─────────────────────────────────────────────────────

export type QualityDispositionDecisionType =
  | 'APPROVE_QUALITY'
  | 'KEEP_IN_QUARANTINE'
  | 'REQUEST_REINSPECTION'
  | 'REQUEST_ADDITIONAL_EVIDENCE'
  | 'REQUEST_DOCUMENT_CORRECTION'
  | 'REQUEST_SUPERVISOR_REVIEW'

export type QualityDispositionDecisionStatus =
  | 'PROPOSED'
  | 'SUBMITTED'
  | 'APPROVED'
  | 'CHANGES_REQUESTED'
  | 'REJECTED'
  | 'EXECUTED'

export interface QualityDispositionDecision {
  decision_id: string
  case_id: string
  case_code: string | null
  inspection_id: string | null
  inspection_code: string | null
  allocation_id: string | null
  decision_type: QualityDispositionDecisionType
  status: QualityDispositionDecisionStatus
  proposed_quantity: string | null
  released_quantity: string | null
  rejected_quantity: string | null
  unit: UnitOfMeasureSummary | null
  rationale: string
  conditions: string[]
  requires_release: boolean
  requires_rejection: boolean
  requires_reinspection: boolean
  requires_non_conformity: boolean
  release_authorization_id: string | null
  rejection_authorization_id: string | null
  reinspection_request_id: string | null
  non_conformity_id: string | null
  proposed_by: UserSummary
  submitted_by: UserSummary | null
  reviewed_by: UserSummary | null
  executed_by: UserSummary | null
  submission_notes: string | null
  review_notes: string | null
  execution_notes: string | null
  changes_requested_reason: string | null
  rejection_reason: string | null
  submitted_at: string | null
  reviewed_at: string | null
  executed_at: string | null
  created_at: string
  updated_at: string
}

export interface QualityDecisionApproval {
  approval_id: string
  decision_id: string
  case_id: string
  approval_level: number
  required_role: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'SKIPPED'
  approver: UserSummary | null
  comments: string | null
  delegated_to: UserSummary | null
  approved_at: string | null
  rejected_at: string | null
  expires_at: string | null
  created_at: string
  updated_at: string
}

// ── Liberación de cuarentena ────────────────────────────────────────────────────

export type QuarantineReleaseType = 'TOTAL' | 'PARTIAL'

export type QuarantineReleaseStatus =
  | 'REQUESTED'
  | 'APPROVED'
  | 'EXECUTED'
  | 'REJECTED'
  | 'CANCELLED'

export interface QuarantineReleaseAuthorization {
  authorization_id: string
  case_id: string
  case_code: string | null
  decision_id: string | null
  release_type: QuarantineReleaseType
  status: QuarantineReleaseStatus
  released_quantity: string
  unit: UnitOfMeasureSummary | null
  product: ProductSummary | null
  destination_warehouse_id: string | null
  destination_warehouse: WarehouseSummary | null
  destination_location_id: string | null
  destination_location: WarehouseLocationSummary | null
  putaway_preparation_id: string | null
  putaway_preparation_code: string | null
  reason: string
  conditions: string[]
  requires_putaway: boolean
  putaway_completed: boolean
  released_by: UserSummary | null
  approved_by: UserSummary | null
  executed_by: UserSummary | null
  rejected_by: UserSummary | null
  cancelled_by: UserSummary | null
  rejection_reason: string | null
  cancellation_reason: string | null
  approved_at: string | null
  executed_at: string | null
  rejected_at: string | null
  cancelled_at: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

// ── Rechazo de cuarentena ───────────────────────────────────────────────────────

export type QuarantineRejectionType = 'TOTAL' | 'PARTIAL'

export type QuarantineRejectionStatus =
  | 'REQUESTED'
  | 'APPROVED'
  | 'EXECUTED'
  | 'REJECTED'
  | 'CANCELLED'

export interface QuarantineRejectionAuthorization {
  authorization_id: string
  case_id: string
  case_code: string | null
  decision_id: string | null
  rejection_type: QuarantineRejectionType
  status: QuarantineRejectionStatus
  rejected_quantity: string
  unit: UnitOfMeasureSummary | null
  product: ProductSummary | null
  non_conformity_id: string | null
  non_conformity_code: string | null
  reason: string
  disposal_method: string | null
  requires_non_conformity: boolean
  non_conformity_completed: boolean
  rejected_by: UserSummary | null
  approved_by: UserSummary | null
  executed_by: UserSummary | null
  cancelled_by: UserSummary | null
  cancellation_reason: string | null
  approved_at: string | null
  executed_at: string | null
  rejected_at: string | null
  cancelled_at: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

// ── Reinspección ────────────────────────────────────────────────────────────────

export interface QualityReinspectionRequest {
  request_id: string
  case_id: string
  case_code: string | null
  original_inspection_id: string
  original_inspection_code: string | null
  new_inspection_id: string | null
  new_inspection_code: string | null
  status: 'REQUESTED' | 'APPROVED' | 'INSPECTION_CREATED' | 'COMPLETED' | 'CANCELLED'
  reason: string
  specific_controls: string[] | null
  additional_requirements: string | null
  urgency: string | null
  requested_by: UserSummary
  approved_by: UserSummary | null
  inspection_created_by: UserSummary | null
  approved_at: string | null
  inspection_created_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  cancellation_reason: string | null
  created_at: string
  updated_at: string
}

// ── Documento de no conformidad ─────────────────────────────────────────────────

export type QualityNonConformityDocumentStatus =
  | 'DRAFT'
  | 'EMITTED'
  | 'DOWNLOADED'
  | 'REPRINTED'
  | 'CANCELLED'

export interface QualityNonConformityDocument {
  document_id: string
  case_id: string
  case_code: string | null
  authorization_id: string | null
  document_code: string | null
  status: QualityNonConformityDocumentStatus
  non_conformity_type: string
  severity: string
  product: ProductSummary | null
  affected_quantity: string | null
  unit: UnitOfMeasureSummary | null
  supplier: BusinessPartnerSummary | null
  description: string
  root_cause: string | null
  corrective_action: string | null
  preventive_action: string | null
  disposal_method: string | null
  responsible_party: string | null
  emission_date: string | null
  due_date: string | null
  closed_at: string | null
  pdf_url: string | null
  pdf_hash: string | null
  integrity_hash: string | null
  reprint_count: number
  last_reprint_at: string | null
  emitted_by: UserSummary | null
  cancelled_by: UserSummary | null
  cancellation_reason: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

// ── Disponibilidad ──────────────────────────────────────────────────────────────

export interface QualityAvailabilityRecord {
  record_id: string
  allocation_id: string
  case_id: string | null
  inspection_id: string | null
  decision_id: string | null
  release_id: string | null
  product: ProductSummary
  warehouse: WarehouseSummary
  quantity: string
  unit: UnitOfMeasureSummary
  availability_class: InventoryAvailabilityClass
  quality_status: InventoryQualityStatus
  lot_number: string | null
  serial_number: string | null
  expiration_date: string | null
  available_for_putaway: boolean
  available_for_sale: boolean
  available_for_transfer: boolean
  available_for_consumption: boolean
  blocked_reason: string | null
  blocked_since: string | null
  last_status_change: string
  created_at: string
  updated_at: string
}

export interface QualityAvailabilitySummary {
  total_allocations: number
  available_for_putaway: number
  available_for_sale: number
  blocked_quarantine: number
  rejected_not_available: number
  pending_evaluation: number
  partial_release: number
  total_available_quantity: string
  total_blocked_quantity: string
  total_rejected_quantity: string
  products_available: number
  products_blocked: number
  products_partially_available: number
}

// ── Historial de cuarentena ─────────────────────────────────────────────────────

export type QualityQuarantineEventType =
  | 'CASE_CREATED'
  | 'CASE_OPENED'
  | 'CASE_LOCKED'
  | 'CASE_UNLOCKED'
  | 'PLACEMENT_CONFIRMED'
  | 'PLACEMENT_SUPERSEDED'
  | 'INSPECTION_ASSIGNED'
  | 'INSPECTION_STARTED'
  | 'INSPECTION_PAUSED'
  | 'INSPECTION_COMPLETED'
  | 'INSPECTION_CANCELLED'
  | 'CONTROL_COMPLETED'
  | 'MEASUREMENT_RECORDED'
  | 'EVIDENCE_UPLOADED'
  | 'CERTIFICATE_REVIEWED'
  | 'DECISION_PROPOSED'
  | 'DECISION_SUBMITTED'
  | 'DECISION_APPROVED'
  | 'DECISION_REJECTED'
  | 'DECISION_EXECUTED'
  | 'RELEASE_REQUESTED'
  | 'RELEASE_APPROVED'
  | 'RELEASE_EXECUTED'
  | 'RELEASE_CANCELLED'
  | 'REJECTION_REQUESTED'
  | 'REJECTION_APPROVED'
  | 'REJECTION_EXECUTED'
  | 'REJECTION_CANCELLED'
  | 'REINSPECTION_REQUESTED'
  | 'REINSPECTION_APPROVED'
  | 'NON_CONFORMITY_EMITTED'
  | 'NON_CONFORMITY_DOWNLOADED'
  | 'NON_CONFORMITY_CANCELLED'
  | 'STATUS_CHANGED'
  | 'PRIORITY_CHANGED'
  | 'DUE_DATE_SET'
  | 'CASE_CLOSED'
  | 'CASE_CANCELLED'
  | 'INTEGRITY_VERIFIED'
  | 'INTEGRITY_FAILED'

export interface QualityQuarantineHistoryEvent {
  event_id: string
  case_id: string
  inspection_id: string | null
  allocation_id: string | null
  event_type: QualityQuarantineEventType
  timestamp: string
  actor: UserSummary
  action: string
  previous_status: string | null
  new_status: string | null
  reason: string | null
  result: string | null
  metadata: Record<string, unknown> | null
}

// ── Integridad ──────────────────────────────────────────────────────────────────

export interface QualityQuarantineIntegrity {
  case_id: string
  source_hash: string | null
  allocations_hash: string | null
  placements_hash: string | null
  inspections_hash: string | null
  decisions_hash: string | null
  releases_hash: string | null
  rejections_hash: string | null
  non_conformities_hash: string | null
  evidence_hash: string | null
  history_hash: string | null
  snapshot_hash: string | null
  algorithm: string
  last_verified_at: string | null
  status: 'VALID' | 'INVALID' | 'PENDING' | 'NOT_VERIFIED'
}

// ── Capabilidades ───────────────────────────────────────────────────────────────

export interface QualityQuarantineCapabilities {
  case_id: string
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_lock: boolean
  can_unlock: boolean
  can_assign_inspection: boolean
  can_start_inspection: boolean
  can_complete_inspection: boolean
  can_cancel_inspection: boolean
  can_propose_disposition: boolean
  can_submit_disposition: boolean
  can_approve_disposition: boolean
  can_request_release: boolean
  can_approve_release: boolean
  can_execute_release: boolean
  can_request_rejection: boolean
  can_approve_rejection: boolean
  can_execute_rejection: boolean
  can_request_reinspection: boolean
  can_approve_reinspection: boolean
  can_emit_non_conformity: boolean
  can_download_non_conformity: boolean
  can_cancel_non_conformity: boolean
  can_place_in_zone: boolean
  can_supersede_placement: boolean
  can_upload_evidence: boolean
  can_review_certificates: boolean
  can_change_priority: boolean
  can_set_due_date: boolean
  can_close: boolean
  can_cancel: boolean
  can_view_history: boolean
  can_view_integrity: boolean
  can_view_availability: boolean
  can_view_putaway_preparation: boolean
  can_view_future_movements: boolean
}

export interface QualityInspectionCapabilities {
  inspection_id: string
  can_view: boolean
  can_start: boolean
  can_pause: boolean
  can_resume: boolean
  can_complete: boolean
  can_cancel: boolean
  can_record_measurement: boolean
  can_upload_evidence: boolean
  can_review_certificate: boolean
  can_complete_control: boolean
  can_skip_control: boolean
  can_correct_control: boolean
  can_submit_for_validation: boolean
  can_validate: boolean
  can_request_reinspection: boolean
  can_view_controls: boolean
  can_view_measurements: boolean
  can_view_samples: boolean
  can_view_evidence: boolean
  can_view_certificates: boolean
  can_view_history: boolean
}

// ── Preparación ─────────────────────────────────────────────────────────────────

export interface PutawayPreparation {
  preparation_id: string
  case_id: string
  release_authorization_id: string
  product: ProductSummary
  warehouse: WarehouseSummary
  quantity: string
  unit: UnitOfMeasureSummary
  lot_number: string | null
  serial_number: string | null
  suggested_location: WarehouseLocationSummary | null
  suggested_zone: string | null
  priority: number
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
  assigned_to: UserSummary | null
  completed_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface FutureInventoryMovementPreparation {
  preparation_id: string
  case_id: string
  allocation_id: string
  movement_type: string
  product: ProductSummary
  warehouse: WarehouseSummary
  quantity: string
  unit: UnitOfMeasureSummary
  lot_number: string | null
  serial_number: string | null
  origin_location: WarehouseLocationSummary | null
  destination_location: WarehouseLocationSummary | null
  estimated_date: string | null
  status: 'PLANNED' | 'CONFIRMED' | 'EXECUTED' | 'CANCELLED'
  created_at: string
}

export interface FutureInventoryBalancePreparation {
  preparation_id: string
  case_id: string
  allocation_id: string
  product: ProductSummary
  warehouse: WarehouseSummary
  quantity: string
  unit: UnitOfMeasureSummary
  lot_number: string | null
  serial_number: string | null
  balance_type: 'INBOUND' | 'OUTBOUND' | 'ADJUSTMENT'
  expected_date: string | null
  status: 'PLANNED' | 'CONFIRMED' | 'EXECUTED' | 'CANCELLED'
  created_at: string
}

export interface FutureTraceabilityPreparation {
  preparation_id: string
  case_id: string
  allocation_id: string
  product: ProductSummary
  lot_number: string | null
  serial_number: string | null
  expiration_date: string | null
  batch_reference: string | null
  origin_receipt_id: string | null
  origin_receipt_code: string | null
  supplier: BusinessPartnerSummary | null
  traceability_fields: Record<string, string>
  status: 'PLANNED' | 'CONFIRMED' | 'COMPLETED'
  created_at: string
}

// ── Request types ───────────────────────────────────────────────────────────────

export interface CreateQuarantineCaseRequest {
  source_type: string
  inbound_receipt_id: string
  product_id: string
  product_version_id?: string
  quarantine_reason?: string
  reason_description?: string
}

export interface UpdateQuarantineCaseRequest {
  title?: string
  description?: string
  severity?: string
  priority?: number
  due_date?: string
}

export interface LockQuarantineCaseRequest {
  reason: string
}

export interface UnlockQuarantineCaseRequest {
  reason: string
}

export interface PlaceInQuarantineZoneRequest {
  zone_id: string
  location_id: string
  allocation_id?: string
  quantity: string
  unit_id: string
  lot_number?: string
  serial_number?: string
  label_code?: string
  notes?: string
}

export interface SupersedeQuarantinePlacementRequest {
  placement_id: string
  new_zone_id: string
  new_location_id: string
  reason: string
}

export interface CreateQualityInspectionRequest {
  case_id: string
  allocation_id?: string
  plan_id?: string
  inspection_type?: string
  product_id?: string
  lot_number?: string
  serial_number?: string
  total_quantity?: string
  sample_quantity?: string
  unit_id?: string
  notes?: string
}

export interface UpdateQualityInspectionRequest {
  notes?: string
  estimated_duration_minutes?: number
}

export interface StartQualityInspectionRequest {
  inspector_id?: string
  notes?: string
}

export interface PauseQualityInspectionRequest {
  reason: string
}

export interface CompleteQualityInspectionRequest {
  overall_result: QualityInspectionOverallResult
  notes?: string
}

export interface CancelQualityInspectionRequest {
  reason: string
}

export interface RecordQualityMeasurementRequest {
  control_id: string
  measurement_type: QualityMeasurementType
  value: string
  unit_id: string
  target_value?: string
  min_value?: string
  max_value?: string
  measurement_point?: number
  device_id?: string
  device_name?: string
  calibrated?: boolean
  calibration_date?: string
  environment_conditions?: string
  notes?: string
}

export interface CompleteQualityInspectionControlRequest {
  control_id: string
  result_value?: string
  result_text?: string
  result_boolean?: boolean
  result_file_id?: string
  notes?: string
}

export interface SkipQualityInspectionControlRequest {
  control_id: string
  reason: string
}

export interface CorrectQualityInspectionControlRequest {
  control_id: string
  result_value?: string
  result_text?: string
  result_boolean?: boolean
  result_file_id?: string
  correction_reason: string
  notes?: string
}

export interface UploadQualityInspectionEvidenceRequest {
  control_id?: string
  evidence_type: string
  file_id: string
  classification?: string
  description?: string
  tags?: string[]
  is_sensitive?: boolean
}

export interface ReviewQualityCertificateRequest {
  review_id: string
  status: QualityCertificateReviewStatus
  file_id?: string
  issuer?: string
  reference_number?: string
  issue_date?: string
  expiration_date?: string
  reviewer_notes?: string
}

export interface CreateQualityDispositionDecisionRequest {
  case_id: string
  inspection_id?: string
  allocation_id?: string
  decision_type: QualityDispositionDecisionType
  proposed_quantity?: string
  unit_id?: string
  rationale: string
  conditions?: string[]
}

export interface UpdateQualityDispositionDecisionRequest {
  decision_type?: QualityDispositionDecisionType
  proposed_quantity?: string
  rationale?: string
  conditions?: string[]
}

export interface SubmitQualityDispositionDecisionRequest {
  notes?: string
}

export interface ApproveQualityDispositionDecisionRequest {
  decision: 'APPROVE' | 'REQUEST_CHANGES' | 'REJECT'
  comments?: string
  changes_requested_reason?: string
}

export interface RequestQuarantineReleaseRequest {
  case_id: string
  decision_id?: string
  release_type: QuarantineReleaseType
  released_quantity?: string
  unit_id?: string
  destination_warehouse_id?: string
  destination_location_id?: string
  reason: string
  conditions?: string[]
}

export interface ApproveQuarantineReleaseRequest {
  decision: 'APPROVE' | 'REJECT'
  comments?: string
}

export interface ExecuteQuarantineReleaseRequest {
  confirmation: boolean
}

export interface CancelQuarantineReleaseRequest {
  reason: string
}

export interface RequestQuarantineRejectionRequest {
  case_id: string
  decision_id?: string
  rejection_type: QuarantineRejectionType
  rejected_quantity?: string
  unit_id?: string
  reason: string
  disposal_method?: string
}

export interface ApproveQuarantineRejectionRequest {
  decision: 'APPROVE' | 'REJECT'
  comments?: string
}

export interface ExecuteQuarantineRejectionRequest {
  confirmation: boolean
}

export interface CancelQuarantineRejectionRequest {
  reason: string
}

export interface RequestQualityReinspectionRequest {
  case_id: string
  original_inspection_id: string
  reason: string
  specific_controls?: string[]
  additional_requirements?: string
  urgency?: string
}

export interface EmitQualityNonConformityRequest {
  case_id: string
  authorization_id?: string
  non_conformity_type: string
  severity: string
  product_id?: string
  affected_quantity?: string
  unit_id?: string
  supplier_id?: string
  description: string
  root_cause?: string
  corrective_action?: string
  preventive_action?: string
  disposal_method?: string
  responsible_party?: string
  due_date?: string
}

export interface CancelQualityNonConformityRequest {
  reason: string
}

export interface CreateQuarantineZoneRequest {
  code: string
  name: string
  description?: string
  warehouse_id: string
  zone_type: string
  capacity?: string
  capacity_unit_id?: string
  temperature_controlled?: boolean
  min_temperature?: string
  max_temperature?: string
  access_restricted?: boolean
  allowed_reasons?: QuarantineReason[]
}

export interface UpdateQuarantineZoneRequest {
  name?: string
  description?: string
  zone_type?: string
  capacity?: string
  capacity_unit_id?: string | null
  temperature_controlled?: boolean
  min_temperature?: string | null
  max_temperature?: string | null
  access_restricted?: boolean
  allowed_reasons?: QuarantineReason[]
}

export interface BlockQuarantineZoneRequest {
  reason: string
}

export interface UnblockQuarantineZoneRequest {
  reason: string
}

// ── Query types ─────────────────────────────────────────────────────────────────

export interface QualityQuarantineCaseListQuery {
  page?: number
  page_size?: number
  cursor?: string
  status?: QualityQuarantineCaseStatus | QualityQuarantineCaseStatus[]
  reason?: QuarantineReason | QuarantineReason[]
  severity?: string
  warehouse_id?: string
  supplier_id?: string
  product_id?: string
  allocation_id?: string
  zone_id?: string
  has_inspection?: boolean
  has_disposition_decision?: boolean
  has_release?: boolean
  has_rejection?: boolean
  has_non_conformity?: boolean
  is_overdue?: boolean
  is_locked?: boolean
  date_from?: string
  date_to?: string
  due_date_from?: string
  due_date_to?: string
  search?: string
  my_cases?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QualityInspectionListQuery {
  page?: number
  page_size?: number
  cursor?: string
  status?: QualityInspectionStatus | QualityInspectionStatus[]
  overall_result?: QualityInspectionOverallResult | QualityInspectionOverallResult[]
  inspection_type?: string
  case_id?: string
  allocation_id?: string
  plan_id?: string
  warehouse_id?: string
  product_id?: string
  inspector_id?: string
  has_disposition_decision?: boolean
  requires_reinspection?: boolean
  date_from?: string
  date_to?: string
  search?: string
  my_inspections?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QuarantineZoneListQuery {
  page?: number
  page_size?: number
  status?: QuarantineZoneStatus | QuarantineZoneStatus[]
  warehouse_id?: string
  temperature_controlled?: boolean
  access_restricted?: boolean
  has_capacity?: boolean
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QualityDispositionDecisionListQuery {
  page?: number
  page_size?: number
  status?: QualityDispositionDecisionStatus | QualityDispositionDecisionStatus[]
  decision_type?: QualityDispositionDecisionType | QualityDispositionDecisionType[]
  case_id?: string
  inspection_id?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QuarantineReleaseListQuery {
  page?: number
  page_size?: number
  status?: QuarantineReleaseStatus | QuarantineReleaseStatus[]
  release_type?: QuarantineReleaseType
  case_id?: string
  product_id?: string
  warehouse_id?: string
  date_from?: string
  date_to?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QuarantineRejectionListQuery {
  page?: number
  page_size?: number
  status?: QuarantineRejectionStatus | QuarantineRejectionStatus[]
  rejection_type?: QuarantineRejectionType
  case_id?: string
  product_id?: string
  warehouse_id?: string
  date_from?: string
  date_to?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QualityNonConformityListQuery {
  page?: number
  page_size?: number
  status?: QualityNonConformityDocumentStatus | QualityNonConformityDocumentStatus[]
  case_id?: string
  product_id?: string
  supplier_id?: string
  severity?: string
  date_from?: string
  date_to?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface QualityAvailabilityListQuery {
  page?: number
  page_size?: number
  availability_class?: InventoryAvailabilityClass | InventoryAvailabilityClass[]
  quality_status?: InventoryQualityStatus | InventoryQualityStatus[]
  warehouse_id?: string
  product_id?: string
  lot_number?: string
  serial_number?: string
  available_for_putaway?: boolean
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// ── Eventos de cuarentena (compatibilidad) ──────────────────────────────────────

export interface QualityQuarantineEvent {
  event_id: string
  case_id: string
  event_type: QualityQuarantineEventType
  timestamp: string
  actor: UserSummary
  action: string
  previous_status: string | null
  new_status: string | null
  reason: string | null
  result: string | null
}

// ── Resumen de disponibilidad por zona ──────────────────────────────────────────

export interface QuarantineZoneAvailabilitySummary {
  zone_id: string
  zone_code: string
  zone_name: string
  warehouse: WarehouseSummary
  total_capacity: string | null
  current_occupancy: string
  occupancy_percentage: string | null
  available_capacity: string | null
  active_cases: number
  total_allocations: number
  product_breakdown: {
    product: ProductSummary
    quantity: string
    unit: UnitOfMeasureSummary
    case_count: number
  }[]
}

// ── Resumen de inspección por caso ──────────────────────────────────────────────

export interface QualityCaseInspectionSummary {
  case_id: string
  total_inspections: number
  completed_inspections: number
  pending_inspections: number
  overall_quality_status: InventoryQualityStatus
  last_inspection_result: QualityInspectionOverallResult | null
  last_inspection_date: string | null
  total_measurements: number
  measurements_passed: number
  measurements_failed: number
  controls_completed: number
  controls_failed: number
  evidence_count: number
  certificate_review_count: number
}

// ── Dashboard de cuarentena ─────────────────────────────────────────────────────

export interface QualityQuarantineDashboard {
  case_summary: QualityQuarantineCaseSummary
  inspection_summary: QualityInspectionSummary
  availability_summary: QualityAvailabilitySummary
  zone_summaries: QuarantineZoneAvailabilitySummary[]
  recent_events: QualityQuarantineHistoryEvent[]
  overdue_cases: QualityQuarantineCase[]
  pending_decisions: QualityDispositionDecision[]
  pending_releases: QuarantineReleaseAuthorization[]
  pending_rejections: QuarantineRejectionAuthorization[]
}

// ── Filtros predefinidos ────────────────────────────────────────────────────────

export interface QualityQuarantineFilterPreset {
  preset_id: string
  name: string
  description: string | null
  query: QualityQuarantineCaseListQuery
  is_default: boolean
  created_by: UserSummary
  created_at: string
}

export interface QualityInspectionFilterPreset {
  preset_id: string
  name: string
  description: string | null
  query: QualityInspectionListQuery
  is_default: boolean
  created_by: UserSummary
  created_at: string
}

// ── Exportaciones masivas ────────────────────────────────────────────────────────

export interface QualityQuarantineExportRequest {
  query: QualityQuarantineCaseListQuery
  format: 'CSV' | 'XLSX' | 'PDF'
  fields: string[]
  include_history: boolean
  include_integrity: boolean
}

export interface QualityInspectionExportRequest {
  query: QualityInspectionListQuery
  format: 'CSV' | 'XLSX' | 'PDF'
  fields: string[]
  include_controls: boolean
  include_measurements: boolean
  include_evidence: boolean
}

// ── Estadísticas de cuarentena ──────────────────────────────────────────────────

export interface QualityQuarantineStatistics {
  period: {
    from: string
    to: string
  }
  cases: {
    created: number
    closed: number
    average_resolution_hours: string | null
    average_inspection_hours: string | null
  }
  inspections: {
    total: number
    passed: number
    failed: number
    average_duration_minutes: string | null
  }
  dispositions: {
    approved: number
    rejected: number
    reinspection: number
    average_decision_hours: string | null
  }
  releases: {
    requested: number
    approved: number
    executed: number
    average_release_hours: string | null
  }
  rejections: {
    requested: number
    approved: number
    executed: number
  }
  by_reason: {
    reason: QuarantineReason
    count: number
    percentage: string
  }[]
  by_warehouse: {
    warehouse: WarehouseSummary
    count: number
    percentage: string
  }[]
  by_supplier: {
    supplier: BusinessPartnerSummary
    count: number
    percentage: string
  }[]
}

// ── Notificaciones de cuarentena ────────────────────────────────────────────────

export type QualityQuarantineNotificationType =
  | 'CASE_CREATED'
  | 'CASE_ASSIGNED'
  | 'CASE_OVERDUE'
  | 'INSPECTION_ASSIGNED'
  | 'INSPECTION_COMPLETED'
  | 'INSPECTION_FAILED'
  | 'DECISION_REQUIRED'
  | 'DECISION_APPROVED'
  | 'DECISION_REJECTED'
  | 'RELEASE_READY'
  | 'RELEASE_APPROVED'
  | 'RELEASE_COMPLETED'
  | 'REJECTION_READY'
  | 'REJECTION_APPROVED'
  | 'REJECTION_COMPLETED'
  | 'REINSPECTION_REQUIRED'
  | 'NON_CONFORMITY_EMITTED'
  | 'ZONE_CAPACITY_WARNING'
  | 'ZONE_BLOCKED'

export interface QualityQuarantineNotification {
  notification_id: string
  case_id: string | null
  notification_type: QualityQuarantineNotificationType
  title: string
  message: string
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
  recipient: UserSummary
  read: boolean
  action_url: string | null
  created_at: string
  read_at: string | null
}

// ── Resumen de productor para cuarentena ────────────────────────────────────────

export interface ProductQuarantineSummary {
  product: ProductSummary
  total_quarantined_quantity: string
  unit: UnitOfMeasureSummary
  active_cases: number
  total_cases: number
  pending_inspection: number
  average_resolution_hours: string | null
  last_quarantine_date: string | null
  common_reasons: QuarantineReason[]
  supplier_breakdown: {
    supplier: BusinessPartnerSummary
    case_count: number
    quantity: string
  }[]
}

// ── Resumen de proveedor para cuarentena ────────────────────────────────────────

export interface SupplierQuarantineSummary {
  supplier: BusinessPartnerSummary
  total_cases: number
  open_cases: number
  total_quarantined_quantity: string
  total_rejected_quantity: string
  average_resolution_hours: string | null
  common_reasons: QuarantineReason[]
  product_breakdown: {
    product: ProductSummary
    case_count: number
    quantity: string
  }[]
  last_case_date: string | null
  non_conformity_count: number
}
