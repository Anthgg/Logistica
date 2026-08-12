/**
 * Tipos del dominio de muelles de entrada y descarga (Fase 038).
 *
 * Reglas:
 * - No se envían assigned_by, started_by, completed_by, released_by.
 * - No se envían timestamps autoritativos (arrived_at, started_at, etc.).
 * - No se envían duraciones calculadas en frontend.
 * - El backend es la única fuente de disponibilidad, compatibilidad y tiempos.
 * - Montos, pesos y cantidades decimales como string.
 * - Duraciones como número entero de segundos cuando provengan del backend.
 * - No se usa any.
 */

// ── Tipos base reutilizados ───────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
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

export interface GateCheckInSummary {
  id: string
  cpv_code: string | null
  cit_code: string | null
  warehouse_id: string
  warehouse_name: string
  gate_id: string | null
  gate_name: string | null
  vehicle_plate: string | null
  vehicle_id: string | null
  driver_name_redacted: string | null
  supplier_name: string | null
  carrier_name: string | null
  arrived_at: string | null
  authorized_at: string | null
  decision_type: string | null
  seal_number: string | null
  pallets: number | null
  packages: number | null
  weight: string | null
  special_requirements: string | null
  conditions: string | null
  warnings: string[]
  status: string
}

export interface ReceptionAppointmentSummary {
  id: string
  cit_code: string
  warehouse_id: string
  warehouse_name: string
  date: string
  time_start: string
  time_end: string
  supplier_name: string | null
  carrier_name: string | null
  vehicle_plate: string | null
  po_codes: string[]
  pallets: number | null
  packages: number | null
  weight: string | null
  special_requirements: string | null
}

export interface FileAssetSummary {
  id: string
  name: string
  content_type: string | null
  size: number | null
  partial_hash: string | null
}

export interface DecimalValue {
  value: string
  unit: string | null
}

// ── Muelles ───────────────────────────────────────────────────────────────────

export type WarehouseDockStatus =
  | 'ACTIVE'
  | 'INACTIVE'
  | 'BLOCKED'
  | 'MAINTENANCE'
  | 'ARCHIVED'

export type WarehouseDockOperationalStatus =
  | 'AVAILABLE'
  | 'RESERVED'
  | 'OCCUPIED'
  | 'UNLOADING'
  | 'PENDING_RELEASE'
  | 'BLOCKED'
  | 'MAINTENANCE'
  | 'INACTIVE'
  | 'UNKNOWN'

export type DockType =
  | 'STANDARD'
  | 'REFRIGERATED'
  | 'HAZMAT'
  | 'OVERSIZED'
  | 'DRIVE_THROUGH'
  | 'COVERED'
  | 'OUTDOOR'

export type DockDirection =
  | 'INBOUND'
  | 'OUTBOUND'
  | 'BIDIRECTIONAL'

export interface WarehouseDockCapability {
  refrigerated: boolean
  hazmat: boolean
  oversized: boolean
  drive_through: boolean
  covered: boolean
  max_vehicle_types: string[]
  max_length_m: string | null
  max_height_m: string | null
  max_weight_kg: string | null
  equipment: string[]
  special_requirements: string[]
}

export interface WarehouseDockOperatingWindow {
  id: string
  dock_id: string
  day_of_week: number
  opens_at: string
  closes_at: string
  is_active: boolean
  effective_from: string | null
  effective_to: string | null
}

export interface WarehouseDockBlackout {
  id: string
  dock_id: string
  starts_at: string
  ends_at: string
  reason: string
  created_by_display: string
  created_at: string
  affects_active_assignments: boolean
}

export interface WarehouseDockAvailability {
  dock_id: string
  is_available: boolean
  operational_status: WarehouseDockOperationalStatus
  next_available_from: string | null
  blackouts: WarehouseDockBlackout[]
  active_assignment_id: string | null
  server_time: string
  timezone: string
}

export interface WarehouseDock {
  id: string
  code: string
  name: string
  warehouse_id: string
  warehouse_name: string
  type: DockType
  direction: DockDirection
  address: string | null
  zone: string | null
  timezone: string
  status: WarehouseDockStatus
  operational_status: WarehouseDockOperationalStatus
  capabilities: WarehouseDockCapability
  operating_windows: WarehouseDockOperatingWindow[]
  active_assignment_id: string | null
  active_assignment_vehicle_plate: string | null
  active_assignment_operation_id: string | null
  occupied_since: string | null
  next_scheduled_assignment_id: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface WarehouseDockSummary {
  id: string
  code: string
  name: string
  warehouse_id: string
  warehouse_name: string
  type: DockType
  direction: DockDirection
  status: WarehouseDockStatus
  operational_status: WarehouseDockOperationalStatus
  active_assignment_id: string | null
  active_assignment_vehicle_plate: string | null
  occupied_since: string | null
}

export interface WarehouseDockCreate {
  code: string
  name: string
  warehouse_id: string
  type: DockType
  direction: DockDirection
  address?: string | null
  zone?: string | null
  timezone: string
  capabilities?: Partial<WarehouseDockCapability>
  notes?: string | null
}

export interface WarehouseDockUpdate {
  name?: string
  address?: string | null
  zone?: string | null
  timezone?: string
  capabilities?: Partial<WarehouseDockCapability>
  notes?: string | null
}

export interface WarehouseDockListQuery {
  warehouse_id?: string
  status?: WarehouseDockStatus
  operational_status?: WarehouseDockOperationalStatus
  type?: DockType
  direction?: DockDirection
  search?: string
  page?: number
  page_size?: number
}

// ── Cola de vehículos ─────────────────────────────────────────────────────────

export type InboundDockPriority =
  | 'LOW'
  | 'NORMAL'
  | 'HIGH'
  | 'URGENT'

export type InboundDockQueueStatus =
  | 'WAITING'
  | 'ASSIGNED'
  | 'IN_MOVEMENT'
  | 'AT_DOCK'
  | 'READY'
  | 'UNLOADING'
  | 'PAUSED'
  | 'COMPLETED'
  | 'PENDING_RELEASE'
  | 'RELEASED'
  | 'HELD'
  | 'CANCELLED'

export interface InboundDockQueueEntry {
  id: string
  position: number
  priority: InboundDockPriority
  status: InboundDockQueueStatus
  check_in_id: string
  cpv_code: string | null
  cit_code: string | null
  warehouse_id: string
  warehouse_name: string
  supplier_id: string | null
  supplier_name: string | null
  carrier_id: string | null
  carrier_name: string | null
  vehicle_id: string | null
  vehicle_plate: string | null
  vehicle_type: string | null
  driver_name_redacted: string | null
  gate_clearance_at: string | null
  entered_queue_at: string
  assigned_dock_id: string | null
  assigned_dock_code: string | null
  assigned_dock_name: string | null
  cit_window_start: string | null
  cit_window_end: string | null
  pallets: number | null
  packages: number | null
  weight: string | null
  special_requirements: string[]
  compatible_dock_ids: string[]
  alerts: string[]
  waiting_seconds: number | null
  server_time: string
}

export interface InboundDockQueueSummary {
  warehouse_id: string
  total_waiting: number
  total_assigned: number
  total_in_movement: number
  total_at_dock: number
  total_unloading: number
  total_paused: number
  total_completed_pending_release: number
  docks_available: number
  docks_reserved: number
  docks_occupied: number
  prolonged_waits: number
  operations_with_anomalies: number
  operations_with_incomplete_data: number
  server_time: string
  timezone: string
}

export interface InboundDockQueueListQuery {
  warehouse_id?: string
  dock_id?: string
  status?: InboundDockQueueStatus
  priority?: InboundDockPriority
  supplier_id?: string
  carrier_id?: string
  search?: string
  date_from?: string
  date_to?: string
  with_anomalies?: boolean
  with_reassignment?: boolean
  page?: number
  page_size?: number
}

export interface ChangePriorityRequest {
  priority: InboundDockPriority
  reason: string
  evidence_file_id?: string | null
  idempotency_key?: string
}

// ── Plan de asignación ────────────────────────────────────────────────────────

export type DockCompatibilityStatus =
  | 'COMPATIBLE'
  | 'COMPATIBLE_WITH_WARNINGS'
  | 'INCOMPATIBLE'
  | 'REQUIRES_REVIEW'
  | 'INCOMPLETE_INFO'

export interface DockCompatibilityResult {
  dock_id: string
  dock_code: string
  dock_name: string
  operational_status: WarehouseDockOperationalStatus
  compatibility_status: DockCompatibilityStatus
  matched_capabilities: string[]
  missing_capabilities: string[]
  restrictions_met: boolean
  restriction_conflicts: string[]
  missing_information: string[]
  warnings: string[]
  conflicts: string[]
  estimated_availability: string | null
  recommendation_score: number | null
  recommendation_rank: number | null
  recommendation_explanation: string | null
}

export interface DockRecommendation {
  recommended_dock_id: string | null
  recommended_dock_code: string | null
  recommended_dock_name: string | null
  reasons: string[]
  is_available: boolean
  matched_capabilities: string[]
  estimated_wait_seconds: number | null
  warnings: string[]
  policy_used: string | null
  alternatives: DockCompatibilityResult[]
}

export interface DockAssignmentPlan {
  id: string
  queue_entry_id: string
  compatible_docks: DockCompatibilityResult[]
  incompatible_docks: DockCompatibilityResult[]
  recommendation: DockRecommendation | null
  expires_at: string
  server_time: string
  created_at: string
}

export interface CreateDockAssignmentPlanRequest {
  queue_entry_id: string
}

export interface ExecuteDockAssignmentPlanRequest {
  plan_id: string
  dock_id: string
  reason?: string | null
  idempotency_key?: string
  override_incompatibility?: boolean
  override_reason?: string | null
  override_evidence_file_id?: string | null
  override_conditions?: string | null
}

// ── Asignación de muelle ──────────────────────────────────────────────────────

export type InboundDockAssignmentStatus =
  | 'ASSIGNED'
  | 'IN_MOVEMENT'
  | 'AT_DOCK'
  | 'UNLOADING_ACTIVE'
  | 'UNLOADING_PAUSED'
  | 'UNLOADING_COMPLETED'
  | 'PENDING_RELEASE'
  | 'RELEASED'
  | 'CANCELLED'
  | 'REASSIGNED'

export interface DockAssignmentCapabilities {
  can_view: boolean
  can_manage_docks: boolean
  can_manage_blackouts: boolean
  can_view_queue: boolean
  can_change_priority: boolean
  can_plan_assignment: boolean
  can_assign: boolean
  can_reassign: boolean
  can_start_movement: boolean
  can_confirm_dock_arrival: boolean
  can_manage_readiness: boolean
  can_manage_responsibles: boolean
  can_record_seal_opening: boolean
  can_start_unloading: boolean
  can_pause: boolean
  can_resume: boolean
  can_abort: boolean
  can_complete: boolean
  can_release_dock: boolean
  can_request_time_correction: boolean
  can_approve_time_correction: boolean
  can_view_metrics: boolean
  can_export: boolean
  can_view_history: boolean
  can_view_receiving_preparation: boolean
}

export interface InboundDockAssignment {
  id: string
  queue_entry_id: string
  dock_id: string
  dock_code: string
  dock_name: string
  warehouse_id: string
  warehouse_name: string
  check_in_id: string
  cpv_code: string | null
  cit_code: string | null
  supplier: SupplierSummary | null
  carrier: CarrierSummary | null
  vehicle: VehicleSummary | null
  status: InboundDockAssignmentStatus
  priority: InboundDockPriority
  assigned_at: string
  movement_started_at: string | null
  arrived_at_dock_at: string | null
  released_at: string | null
  cancelled_at: string | null
  is_override: boolean
  override_reason: string | null
  was_reassigned: boolean
  previous_dock_id: string | null
  previous_dock_code: string | null
  reassignment_reason: string | null
  active_unloading_operation_id: string | null
  capabilities: DockAssignmentCapabilities
  alerts: string[]
  server_time: string
  created_at: string
  updated_at: string
}

export interface DockAssignmentMetrics {
  assignment_id: string
  wait_seconds: number | null
  movement_seconds: number | null
  dock_wait_seconds: number | null
  unloading_gross_seconds: number | null
  unloading_pause_seconds: number | null
  unloading_net_seconds: number | null
  release_delay_seconds: number | null
  dock_occupancy_seconds: number | null
  total_cycle_seconds: number | null
  data_quality: OperationalTimeQualityStatus
}

export interface StartMovementRequest {
  idempotency_key?: string
}

export interface ConfirmDockArrivalRequest {
  idempotency_key?: string
}

export interface CancelDockAssignmentRequest {
  reason: string
}

export interface ReleaseDockRequest {
  idempotency_key?: string
}

export interface ReassignDockRequest {
  new_dock_id: string
  reason: string
  plan_id?: string | null
  idempotency_key?: string
}

// ── Operación de descarga ─────────────────────────────────────────────────────

export type UnloadingOperationStatus =
  | 'CREATED'
  | 'READINESS_PENDING'
  | 'READY'
  | 'ACTIVE'
  | 'PAUSED'
  | 'COMPLETED'
  | 'ABORTED'
  | 'CANCELLED'

export type UnloadingReadinessStatus =
  | 'PENDING'
  | 'COMPLETE'
  | 'COMPLETE_WITH_OBSERVATIONS'
  | 'BLOCKED'
  | 'OVERRIDE_PENDING'
  | 'OVERRIDE_APPROVED'

export type UnloadingCheckResult =
  | 'PASS'
  | 'PASS_WITH_OBSERVATION'
  | 'FAIL'
  | 'NOT_APPLICABLE'
  | 'PENDING_REVIEW'

export interface UnloadingReadinessCheck {
  id: string
  operation_id: string
  code: string
  name: string
  description: string
  is_required: boolean
  is_blocking: boolean
  result: UnloadingCheckResult | null
  observation: string | null
  evidence_file_id: string | null
  override_requested: boolean
  override_approved: boolean | null
  override_reason: string | null
  performed_by: UserSummary | null
  performed_at: string | null
}

export interface UnloadingCompletionCheck {
  id: string
  operation_id: string
  code: string
  name: string
  result: UnloadingCheckResult | null
  observation: string | null
  evidence_file_id: string | null
  performed_by: UserSummary | null
  performed_at: string | null
}

export interface UnloadingResponsibleAssignment {
  id: string
  operation_id: string
  responsibility_type: string
  responsibility_label: string
  user: UserSummary | null
  team_name: string | null
  organization_name: string | null
  status: 'ASSIGNED' | 'ACCEPTED' | 'RELEASED' | 'REVOKED'
  assigned_by: UserSummary | null
  assigned_at: string
  accepted_at: string | null
  released_at: string | null
  valid_until: string | null
  comment: string | null
}

export interface UnloadingEquipmentAssignment {
  id: string
  operation_id: string
  equipment_type: string
  equipment_identifier: string | null
  status_declared: string
  responsible: UserSummary | null
  assigned_at: string
  released_at: string | null
}

export type SealOpeningResult =
  | 'OPENED_NORMALLY'
  | 'OPENED_WITH_OBSERVATION'
  | 'ABSENT'
  | 'DOES_NOT_MATCH'
  | 'PREVIOUSLY_BROKEN'
  | 'POSSIBLE_TAMPERING'
  | 'NOT_APPLICABLE'

export interface UnloadingSealOpening {
  id: string
  operation_id: string
  expected_seal_number: string | null
  observed_seal_number: string | null
  result: SealOpeningResult
  observation: string | null
  opened_by: UserSummary | null
  witness: UserSummary | null
  photo_before_file_id: string | null
  photo_after_file_id: string | null
  has_anomaly: boolean
  created_at: string
}

export interface CreateSealOpeningRequest {
  observed_seal_number?: string | null
  result: SealOpeningResult
  observation?: string | null
  witness_user_id?: string | null
  photo_before_file_id?: string | null
  photo_after_file_id?: string | null
  idempotency_key?: string
}

export interface UnloadingPause {
  id: string
  operation_id: string
  reason: string
  reason_label: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  comment: string | null
  evidence_file_id: string | null
  responsible_informed: UserSummary | null
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
  is_active: boolean
  created_by: UserSummary | null
}

export interface CreatePauseRequest {
  reason: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  comment?: string | null
  evidence_file_id?: string | null
  responsible_informed_user_id?: string | null
  idempotency_key?: string
}

export interface ResumeUnloadingRequest {
  condition_resolved: string
  evidence_file_id?: string | null
  idempotency_key?: string
}

export interface AbortUnloadingRequest {
  reason: string
  category: string
  risk_level: string
  evidence_file_id?: string | null
  supervisor_user_id?: string | null
  next_action: string
  idempotency_key?: string
}

export interface CompleteUnloadingRequest {
  idempotency_key?: string
}

export interface StartUnloadingRequest {
  idempotency_key?: string
}

export interface UnloadingOperation {
  id: string
  assignment_id: string
  dock_id: string
  dock_code: string
  dock_name: string
  warehouse_id: string
  check_in_id: string
  cpv_code: string | null
  cit_code: string | null
  supplier: SupplierSummary | null
  carrier: CarrierSummary | null
  vehicle: VehicleSummary | null
  status: UnloadingOperationStatus
  readiness_status: UnloadingReadinessStatus
  responsibles: UnloadingResponsibleAssignment[]
  seal_opening: UnloadingSealOpening | null
  active_pause: UnloadingPause | null
  started_at: string | null
  completed_at: string | null
  aborted_at: string | null
  server_time: string
  started_at_server: string | null
  active_pause_started_at: string | null
  accumulated_pause_seconds: number
  alerts: string[]
  capabilities: UnloadingOperationCapabilities
  created_at: string
  updated_at: string
}

export interface UnloadingOperationCapabilities {
  can_view: boolean
  can_manage_readiness: boolean
  can_manage_responsibles: boolean
  can_record_seal_opening: boolean
  can_start_unloading: boolean
  can_pause: boolean
  can_resume: boolean
  can_abort: boolean
  can_complete: boolean
  can_view_metrics: boolean
  can_view_history: boolean
  can_view_receiving_preparation: boolean
  can_request_time_correction: boolean
}

export interface UnloadingExpectedLoad {
  operation_id: string
  po_codes: string[]
  expected_lines_count: number | null
  pallets: number | null
  packages: number | null
  weight: string | null
  special_requirements: string[]
  documents: FileAssetSummary[]
  seal_number: string | null
  conditions: string | null
  gate_warnings: string[]
}

// ── Historial y eventos ───────────────────────────────────────────────────────

export type DockEventType =
  | 'GATE_CLEARANCE'
  | 'QUEUE_ENTRY'
  | 'PRIORITY_CHANGED'
  | 'PLAN_GENERATED'
  | 'DOCK_ASSIGNED'
  | 'MOVEMENT_STARTED'
  | 'DOCK_ARRIVAL'
  | 'READINESS_UPDATED'
  | 'RESPONSIBLE_ASSIGNED'
  | 'SEAL_OPENING_RECORDED'
  | 'UNLOADING_STARTED'
  | 'UNLOADING_PAUSED'
  | 'UNLOADING_RESUMED'
  | 'UNLOADING_ABORTED'
  | 'UNLOADING_COMPLETED'
  | 'DOCK_RELEASED'
  | 'DOCK_REASSIGNED'
  | 'TIME_CORRECTION_REQUESTED'
  | 'TIME_CORRECTION_APPROVED'
  | 'TIME_CORRECTION_REJECTED'
  | 'INTEGRITY_FAILED'

export interface DockOperationalEvent {
  id: string
  event_type: DockEventType
  occurred_at: string
  actor: UserSummary | null
  previous_status: string | null
  new_status: string | null
  reason: string | null
  result: string | null
  data_quality: OperationalTimeQualityStatus | null
  partial_hash: string | null
}

export interface DockOperationHistoryEvent {
  id: string
  event_type: DockEventType
  occurred_at: string
  actor: UserSummary | null
  previous_status: string | null
  new_status: string | null
  reason: string | null
  result: string | null
}

// ── Tiempos y métricas ────────────────────────────────────────────────────────

export type OperationalTimeQualityStatus =
  | 'COMPLETE'
  | 'PARTIAL'
  | 'MISSING_EVENT'
  | 'INVALID_ORDER'
  | 'CORRECTED'
  | 'IMPORTED'
  | 'INTEGRITY_FAILED'

export interface DockOperationalTimes {
  assignment_id: string
  gate_arrival_at: string | null
  gate_clearance_at: string | null
  queue_entry_at: string | null
  assigned_at: string | null
  movement_started_at: string | null
  dock_arrival_at: string | null
  unloading_started_at: string | null
  unloading_completed_at: string | null
  dock_released_at: string | null
  pauses: UnloadingPause[]
  data_quality: OperationalTimeQualityStatus
  missing_events: string[]
  corrections: DockOperationalTimeCorrection[]
  last_validated_at: string | null
}

export interface DockOperationalMetrics {
  assignment_id: string
  wait_seconds: number | null
  movement_seconds: number | null
  dock_wait_seconds: number | null
  unloading_gross_seconds: number | null
  unloading_pause_seconds: number | null
  unloading_net_seconds: number | null
  release_delay_seconds: number | null
  dock_occupancy_seconds: number | null
  total_cycle_seconds: number | null
  gate_control_seconds: number | null
  data_quality: OperationalTimeQualityStatus
  impact_on_kpi: string[]
}

export interface DockOperationalTimeCorrection {
  id: string
  assignment_id: string
  event_type: DockEventType
  original_time: string
  proposed_time: string
  timezone: string
  reason: string
  evidence_file_id: string | null
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  requested_by: UserSummary | null
  reviewed_by: UserSummary | null
  created_at: string
  reviewed_at: string | null
  estimated_impact: string | null
}

export interface CreateTimeCorrectionRequest {
  event_type: DockEventType
  proposed_time: string
  timezone: string
  reason: string
  evidence_file_id?: string | null
  idempotency_key?: string
}

export interface DockOperationIntegrity {
  assignment_id: string
  status: 'VALID' | 'FAILED' | 'PENDING'
  failures: string[]
  last_checked_at: string | null
  partial_hash: string | null
}

// ── Preparación para Fase 039 ─────────────────────────────────────────────────

export interface ReceivingScanPreparation {
  operation_id: string
  assignment_id: string
  dock_code: string
  dock_name: string
  cpv_code: string | null
  cit_code: string | null
  supplier: SupplierSummary | null
  carrier: CarrierSummary | null
  vehicle: VehicleSummary | null
  po_codes: string[]
  expected_lines_count: number | null
  pallets: number | null
  packages: number | null
  weight: string | null
  documents: FileAssetSummary[]
  seal_number: string | null
  unloading_started_at: string | null
  unloading_completed_at: string | null
  responsibles: UnloadingResponsibleAssignment[]
  warnings: string[]
  data_quality: OperationalTimeQualityStatus
  is_ready_for_receiving: boolean
  blocking_issues: string[]
}

// ── Blackouts ─────────────────────────────────────────────────────────────────

export interface CreateBlackoutRequest {
  dock_id: string
  starts_at: string
  ends_at: string
  reason: string
  idempotency_key?: string
}

// ── Responsables ──────────────────────────────────────────────────────────────

export interface AssignResponsibleRequest {
  responsibility_type: string
  user_id?: string | null
  team_id?: string | null
  contractor_id?: string | null
  valid_until?: string | null
  comment?: string | null
  idempotency_key?: string
}

// ── Exportación ───────────────────────────────────────────────────────────────

export type ExportFormat = 'CSV' | 'XLSX' | 'PDF'
export type ExportJobStatus = 'PENDING' | 'PROCESSING' | 'READY' | 'FAILED' | 'EXPIRED'

export interface DockOperationExportRequest {
  format: ExportFormat
  warehouse_id?: string
  dock_ids?: string[]
  date_from?: string
  date_to?: string
  status_filter?: string[]
  include_metrics?: boolean
  include_timeline?: boolean
  classification?: string
}

export interface DockOperationExportJob {
  id: string
  status: ExportJobStatus
  format: ExportFormat
  download_url: string | null
  expires_at: string | null
  created_at: string
  completed_at: string | null
  error_message: string | null
}

// ── Formularios de muelle ─────────────────────────────────────────────────────

export interface WarehouseDockBlockRequest {
  reason: string
  idempotency_key?: string
}

export interface WarehouseDockMaintenanceRequest {
  reason: string
  estimated_end: string | null
}

export interface WarehouseDockReadinessOverrideRequest {
  check_id: string
  reason: string
  evidence_file_id?: string | null
  conditions?: string | null
  idempotency_key?: string
}
