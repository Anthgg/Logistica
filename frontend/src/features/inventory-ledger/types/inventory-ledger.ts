// ── Fase 044 — Libro de inventario (kardex técnico) ────────────────────────────

// ── Primitivos ──────────────────────────────────────────────────────────────────

export interface DecimalValue {
  value: string
  scale: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
  cursor?: string | null
}

export interface UserSummary {
  user_id: string
  display_name: string
  email?: string
}

export interface DocumentSummary {
  document_id: string
  document_code: string
  document_type: string
  url?: string
}

export interface FileAssetSummary {
  file_id: string
  filename: string
  mime_type: string
  size_bytes: number
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
  barcode?: string
  category?: string
  category_id?: string
  unit_id?: string
  unit_name?: string
  product_version?: string
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
}

// ── Estados técnicos ───────────────────────────────────────────────────────────

export type InventoryAvailabilityState = 'AVAILABLE' | 'BLOCKED' | 'RESERVED' | 'IN_TRANSIT' | 'QUARANTINED' | 'DAMAGED' | 'EXPIRED' | 'UNKNOWN'
export type InventoryQualityState = 'PENDING' | 'APPROVED' | 'REJECTED' | 'QUARANTINED' | 'RELEASED' | 'UNKNOWN'
export type InventoryTransitState = 'STABLE' | 'IN_TRANSIT' | 'ARRIVED' | 'UNKNOWN'
export type InventoryDamageState = 'INTACT' | 'DAMAGED' | 'PARTIAL' | 'UNKNOWN'
export type InventoryExpirationState = 'VALID' | 'EXPIRING_SOON' | 'EXPIRED' | 'UNKNOWN'

// ── Posiciones ─────────────────────────────────────────────────────────────────

export interface InventoryPosition {
  position_id: string
  warehouse_id: string
  warehouse?: WarehouseSummary
  location_id?: string | null
  location?: WarehouseLocationSummary | null
  external_boundary?: string | null
}

export interface InventoryExternalBoundary {
  boundary_id: string
  code: string
  description?: string
  boundary_type: 'INBOUND_GATE' | 'OUTBOUND_GATE' | 'TRANSFER_POINT' | 'CUSTOMER' | 'SUPPLIER' | 'VIRTUAL'
}

// ── Tipos de movimiento ────────────────────────────────────────────────────────

export type InventoryMovementFamily = 'INBOUND' | 'OUTBOUND' | 'INTERNAL' | 'QUALITY' | 'PUTAWAY' | 'COMPENSATION' | 'STATE_CHANGE' | 'OTHER'

export type InventoryMovementType =
  | 'ENTRY'
  | 'EXIT'
  | 'TRANSFER'
  | 'RESERVATION'
  | 'RELEASE_RESERVATION'
  | 'QUARANTINE_APPLY'
  | 'QUARANTINE_RELEASE'
  | 'QUALITY_APPROVAL'
  | 'QUALITY_REJECTION'
  | 'PUTAWAY_COMPLETE'
  | 'STATE_BLOCKED'
  | 'STATE_DAMAGED'
  | 'STATE_EXPIRED'
  | 'COMPENSATION'
  | 'OTHER'

export type InventoryMovementStatus =
  | 'DRAFT'
  | 'PREPARED'
  | 'POSTED'
  | 'FAILED'
  | 'COMPENSATED'
  | 'CANCELLED'
  | 'DISPUTED'

export type InventoryMovementDirection = 'IN' | 'OUT' | 'INTERNAL'

export interface InventoryMovementSummary {
  movement_id: string
  movement_code: string
  ledger_sequence: number
  family: InventoryMovementFamily
  movement_type: InventoryMovementType
  status: InventoryMovementStatus
  warehouse_id: string
  warehouse: WarehouseSummary
  occurred_at: string
  posted_at: string | null
  source_system: string
  source_event_id: string | null
  source_document_code: string | null
  reason: string
  total_lines: number
  compensated_by_movement_id: string | null
  compensates_movement_id: string | null
  integrity_status: 'OK' | 'WARNING' | 'FAILED' | 'PENDING'
  integrity_hash_partial: string | null
  integrity_algorithm: string
  canonicalization_version: string
  posted_by: UserSummary | null
}

export interface InventoryMovement extends InventoryMovementSummary {
  organization_id: string
  branch_id: string
  created_by: UserSummary
  updated_by: UserSummary | null
  schema_version: string
  lines: InventoryMovementLine[]
  source: InventoryMovementSource | null
  source_document: DocumentSummary | null
  snapshot: InventoryMovementSnapshot | null
  integrity: InventoryMovementIntegrity | null
  compensation_origin_movement_id: string | null
  metadata: Record<string, unknown>
}

// ── Líneas ─────────────────────────────────────────────────────────────────────

export interface InventoryMovementLine {
  line_id: string
  line_number: number
  movement_id: string
  product_id: string
  product: ProductSummary
  quantity: DecimalValue
  unit_id: string
  unit: UnitOfMeasureSummary
  base_quantity_display: DecimalValue
  base_unit_id: string
  base_unit: UnitOfMeasureSummary
  direction: InventoryMovementDirection
  origin_position: InventoryPosition
  destination_position: InventoryPosition
  origin_availability: InventoryAvailabilityState
  destination_availability: InventoryAvailabilityState
  origin_quality: InventoryQualityState
  destination_quality: InventoryQualityState
  origin_transit: InventoryTransitState
  destination_transit: InventoryTransitState
  origin_damage: InventoryDamageState
  destination_damage: InventoryDamageState
  origin_expiration: InventoryExpirationState
  destination_expiration: InventoryExpirationState
  tracking_reference: string | null
  hash_partial: string | null
}

// ── Fuentes ────────────────────────────────────────────────────────────────────

export interface InventoryMovementSource {
  source_id: string
  source_system: string
  module: string
  event_type: string
  event_id: string
  event_version: string
  entity_type: string
  entity_id: string
  adapter: string
  adapter_version: string
  document_id: string | null
  document_code: string | null
  occurred_at: string
  hash_partial: string | null
  validation_status: 'PENDING' | 'VALID' | 'INVALID' | 'DUPLICATE'
  validation_errors: string[]
}

// ── Snapshot ───────────────────────────────────────────────────────────────────

export interface InventoryMovementSnapshot {
  snapshot_id: string
  organization_id: string
  warehouse_id: string
  product_id: string
  unit_id: string
  origin_position: InventoryPosition
  destination_position: InventoryPosition
  origin_availability: InventoryAvailabilityState
  destination_availability: InventoryAvailabilityState
  origin_quality: InventoryQualityState
  destination_quality: InventoryQualityState
  source_system: string
  source_event_id: string | null
  actor: UserSummary
  reason: string
  conversions: Record<string, unknown>
  references: Record<string, string>
  occurred_at: string
  posted_at: string | null
  hash: string
  schema_version: string
  canonicalization_version: string
}

// ── Integridad ─────────────────────────────────────────────────────────────────

export interface InventoryMovementIntegrity {
  integrity_id: string
  movement_id: string
  source_hash: string | null
  snapshot_hash: string | null
  lines_hash: string | null
  previous_movement_hash: string | null
  movement_hash: string
  ledger_sequence: number
  algorithm: string
  canonicalization_version: string
  last_verified_at: string | null
  status: 'OK' | 'WARNING' | 'FAILED' | 'PENDING'
}

// ── Compensaciones ─────────────────────────────────────────────────────────────

export type InventoryMovementCompensationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTED'
  | 'CANCELLED'

export interface InventoryMovementCompensationRequest {
  compensation_id: string
  original_movement_id: string
  original_movement: InventoryMovementSummary
  compensates_movement_id: string | null
  compensation_type: 'FULL' | 'PARTIAL'
  reason_code: string
  description: string
  affected_lines: InventoryMovementCompensationLine[]
  evidence_files: FileAssetSummary[]
  status: InventoryMovementCompensationStatus
  requester: UserSummary
  reviewer: UserSummary | null
  approver: UserSummary | null
  executor: UserSummary | null
  expected_inverse_movement: InventoryMovementSummary | null
  inverse_movement: InventoryMovementSummary | null
  integrity_hashes: { original: string | null; inverse: string | null }
  created_at: string
  submitted_at: string | null
  reviewed_at: string | null
  approved_at: string | null
  rejected_at: string | null
  executed_at: string | null
  cancelled_at: string | null
  notes: string | null
}

export interface InventoryMovementCompensationLine {
  line_id: string
  movement_line_id: string
  product_id: string
  quantity: DecimalValue
  unit_id: string
  reason: string | null
}

// ── Posting ────────────────────────────────────────────────────────────────────

export type InventoryMovementPostingStatus =
  | 'PENDING'
  | 'VALIDATED'
  | 'POSTING'
  | 'POSTED'
  | 'FAILED'
  | 'DUPLICATE'
  | 'CONFLICT'

export interface InventoryMovementPostingRequest {
  posting_id: string
  source_system: string
  source_event_id: string
  event_type: string
  entity_id: string
  status: InventoryMovementPostingStatus
  attempts: number
  last_attempt_at: string | null
  error_code: string | null
  error_message: string | null
  error_classification: 'TRANSIENT' | 'DATA_ERROR' | 'INTEGRITY_ERROR' | 'CONFLICT' | null
  resulting_movement_id: string | null
  resulting_movement_code: string | null
  hash_partial: string | null
  created_at: string
  posted_at: string | null
}

export interface PreparedInventoryEvent {
  event_id: string
  source_system: string
  module: string
  event_type: string
  entity_id: string
  occurred_at: string
  product: ProductSummary | null
  quantity: DecimalValue | null
  unit: UnitOfMeasureSummary | null
  origin_position: InventoryPosition | null
  destination_position: InventoryPosition | null
  origin_availability: InventoryAvailabilityState | null
  destination_availability: InventoryAvailabilityState | null
  hash_partial: string | null
  status: InventoryMovementPostingStatus
  validation_status: 'PENDING' | 'VALID' | 'INVALID'
  validation_errors: string[]
  validation_warnings: string[]
  resulting_movement_id: string | null
  resulting_movement_code: string | null
  attempts: number
  last_error: string | null
  created_at: string
  updated_at: string
}

export interface PreparedInventoryEventValidation {
  event_id: string
  is_valid: boolean
  errors: string[]
  warnings: string[]
  resolved_origin_position: InventoryPosition | null
  resolved_destination_position: InventoryPosition | null
  resolved_movement_type: InventoryMovementType | null
  adapter: string
  adapter_version: string
  hash: string
}

export interface InventoryPreparedEventsBatchRequest {
  batch_id: string
  source_system: string
  event_type: string
  warehouse_id: string
  date_from: string
  date_to: string
  estimated_events: number
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  processed: number
  succeeded: number
  failed: number
  duplicates: number
  created_at: string
  completed_at: string | null
  report_url: string | null
}

// ── Kardex ─────────────────────────────────────────────────────────────────────

export type InventoryKardexScopeState =
  | 'EXACT'
  | 'AMBIGUOUS'
  | 'MULTIPLE_POSITIONS'
  | 'UNIT_MISMATCH'
  | 'TECHNICAL_REPLAY_AVAILABLE'
  | 'RUNNING_QUANTITY_NOT_AVAILABLE'

export interface InventoryKardexScope {
  scope_id: string
  state: InventoryKardexScopeState
  organization_id: string
  warehouse_id: string | null
  location_id: string | null
  product_id: string | null
  position: InventoryPosition | null
  base_unit_id: string | null
  base_unit: UnitOfMeasureSummary | null
  period_from: string
  period_to: string
  calculation_type: 'TECHNICAL_REPLAY' | 'EXACT_REPLAY' | 'NONE'
  warnings: string[]
}

export interface InventoryKardexRow {
  row_id: string
  ledger_sequence: number
  occurred_at: string
  posted_at: string | null
  movement_id: string
  movement_code: string
  movement_type: InventoryMovementType
  document_code: string | null
  product: ProductSummary
  origin_position: InventoryPosition
  destination_position: InventoryPosition
  quantity: DecimalValue
  unit: UnitOfMeasureSummary
  signed_quantity_display: DecimalValue
  entry_quantity_display: DecimalValue | null
  exit_quantity_display: DecimalValue | null
  direction: InventoryMovementDirection
  compensated_by_movement_id: string | null
  integrity_status: 'OK' | 'WARNING' | 'FAILED' | 'PENDING'
}

export interface InventoryKardexRunningQuantityRow {
  row_id: string
  ledger_sequence: number
  occurred_at: string
  initial_reference_quantity: DecimalValue
  entry_quantity: DecimalValue | null
  exit_quantity: DecimalValue | null
  delta: DecimalValue
  accumulated_quantity: DecimalValue
  unit: UnitOfMeasureSummary
  data_quality: 'EXACT' | 'AMBIGUOUS'
  scope_state: InventoryKardexScopeState
}

// ── Particiones ────────────────────────────────────────────────────────────────

export interface InventoryLedgerPartition {
  partition_id: string
  partition_code: string
  organization_id: string
  warehouse_id: string
  warehouse: WarehouseSummary
  year: number
  current_sequence: number
  first_movement_sequence: number | null
  last_movement_sequence: number | null
  total_movements: number
  last_hash_partial: string | null
  last_verified_at: string | null
  last_checkpoint_id: string | null
  last_checkpoint_at: string | null
  integrity_status: 'OK' | 'WARNING' | 'FAILED' | 'PENDING'
  locked: boolean
  created_at: string
}

export interface InventoryLedgerPartitionIntegrity {
  partition_id: string
  first_movement_sequence: number
  last_movement_sequence: number
  total_movements: number
  first_hash: string | null
  last_hash: string | null
  gaps: number
  duplicates: number
  invalid_hashes: number
  status: 'OK' | 'WARNING' | 'FAILED' | 'PENDING'
  last_verified_at: string | null
  duration_ms: number | null
  job_id: string | null
}

export interface InventoryLedgerCheckpoint {
  checkpoint_id: string
  partition_id: string
  initial_sequence: number
  final_sequence: number
  total_movements: number
  first_hash: string | null
  last_hash: string | null
  manifest_hash: string
  status: 'CREATING' | 'COMPLETED' | 'FAILED'
  created_at: string
  duration_ms: number | null
  creator: UserSummary
}

// ── Reconciliación ─────────────────────────────────────────────────────────────

export interface InventoryLedgerReconciliationJob {
  job_id: string
  organization_id: string
  warehouse_id: string | null
  source_system: string
  period_from: string
  period_to: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  total_sources: number
  processed: number
  reconciled: number
  events_without_movement: number
  movements_without_source: number
  quantity_mismatches: number
  duplicate_sources: number
  hash_mismatches: number
  adapter_mismatches: number
  review_required: number
  started_at: string
  completed_at: string | null
}

export type InventoryLedgerReconciliationIssueType =
  | 'EVENT_WITHOUT_MOVEMENT'
  | 'MOVEMENT_WITHOUT_SOURCE'
  | 'QUANTITY_MISMATCH'
  | 'DUPLICATE_SOURCE'
  | 'HASH_MISMATCH'
  | 'ADAPTER_MISMATCH'
  | 'REVIEW_REQUIRED'

export interface InventoryLedgerReconciliationResult {
  result_id: string
  job_id: string
  issue_type: InventoryLedgerReconciliationIssueType
  source: InventoryMovementSource | null
  movement: InventoryMovementSummary | null
  source_quantity: DecimalValue | null
  movement_quantity: DecimalValue | null
  source_hash: string | null
  movement_hash: string | null
  adapter: string | null
  movement_adapter: string | null
  detected_at: string
  notes: string | null
  allowed_actions: ('OPEN_EVENT' | 'OPEN_MOVEMENT' | 'RETRY' | 'REVIEW' | 'REQUEST_COMPENSATION')[]
}

// ── Exportaciones ──────────────────────────────────────────────────────────────

export type InventoryKardexExportFormat = 'CSV' | 'XLSX' | 'PDF' | 'JSON'
export type InventoryKardexExportStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXPIRED'

export interface InventoryKardexExportRequest {
  export_id: string
  format: InventoryKardexExportFormat
  filters: Record<string, unknown>
  scope: InventoryKardexScope | null
  estimated_rows: number
  period_from: string
  period_to: string
  timezone: string
  include_integrity: boolean
  include_sensitive: boolean
  status: InventoryKardexExportStatus
  requester: UserSummary
  job_id: string | null
  created_at: string
  completed_at: string | null
  file_size_bytes: number | null
  expires_at: string | null
  download_count: number
  last_download_at: string | null
  manifest_hash: string | null
  initial_sequence: number | null
  final_sequence: number | null
  total_rows: number | null
  warnings: string[]
  download_url: string | null
}

// ── Preparación para Fase 045 (saldos reconciliables) ─────────────────────────

export interface InventoryBalancePreparationRow {
  row_id: string
  movement_id: string
  movement_code: string
  ledger_sequence: number
  line_id: string
  product_id: string
  product: ProductSummary
  position: InventoryPosition
  entry_quantity: DecimalValue
  exit_quantity: DecimalValue
  delta: DecimalValue
  availability_state: InventoryAvailabilityState
  quality_state: InventoryQualityState
  unit: UnitOfMeasureSummary
  hash: string | null
  materialization_key: string
}

// ── Preparación para Fase 046 (trazabilidad) ──────────────────────────────────

export interface InventoryTraceabilityPreparationRow {
  row_id: string
  movement_id: string
  movement_code: string
  line_id: string
  product_id: string
  product: ProductSummary
  origin: InventoryPosition
  destination: InventoryPosition
  observed_lots: string[]
  observed_serials: string[]
  expiration_dates: string[]
  packaging_type: string | null
  logistics_unit_reference: string | null
  quantity: DecimalValue
  unit: UnitOfMeasureSummary
  hash: string | null
}

// ── Capacidades ────────────────────────────────────────────────────────────────

export interface InventoryMovementCapabilities {
  movement_id: string | null
  can_view: boolean
  can_view_all: boolean
  can_view_sources: boolean
  can_view_snapshot: boolean
  can_view_integrity: boolean
  can_view_history: boolean
  can_view_sensitive: boolean
  can_validate_prepared_event: boolean
  can_post_prepared_event: boolean
  can_retry_failed_posting: boolean
  can_post_batch: boolean
  can_request_compensation: boolean
  can_review_compensation: boolean
  can_approve_compensation: boolean
  can_execute_compensation: boolean
  can_export: boolean
  can_verify_partition: boolean
  can_create_checkpoint: boolean
  can_reconcile: boolean
  can_view_balance_preparation: boolean
  can_view_traceability_preparation: boolean
}

// ── Historial ──────────────────────────────────────────────────────────────────

export interface InventoryMovementHistoryEvent {
  event_id: string
  event_type:
    | 'POSTING_REQUESTED'
    | 'SOURCE_VALIDATED'
    | 'MOVEMENT_POSTED'
    | 'DUPLICATE_DETECTED'
    | 'POSTING_FAILED'
    | 'COMPENSATION_REQUESTED'
    | 'COMPENSATION_REVIEWED'
    | 'COMPENSATION_APPROVED'
    | 'COMPENSATION_EXECUTED'
    | 'VERIFICATION_STARTED'
    | 'INTEGRITY_OK'
    | 'INTEGRITY_FAILED'
    | 'CHECKPOINT_CREATED'
    | 'RECONCILIATION_STARTED'
    | 'EXPORT_REQUESTED'
    | 'EXPORT_DOWNLOADED'
  occurred_at: string
  actor: UserSummary | null
  action: string
  previous_state: string | null
  new_state: string | null
  source: string | null
  result: 'SUCCESS' | 'FAILED' | 'WARNING'
  reason: string | null
  correlation_id: string | null
  metadata: Record<string, unknown>
}

// ── Dashboard ──────────────────────────────────────────────────────────────────

export interface InventoryLedgerDashboardSummary {
  movements_published_today: number
  entries: number
  exits: number
  transfers: number
  state_changes: number
  reservations: number
  compensated_movements: number
  pending_prepared_events: number
  failed_postings: number
  duplicate_events: number
  sequence_gaps: number
  partitions_with_integrity_failure: number
  pending_reconciliations: number
  last_checkpoint: InventoryLedgerCheckpoint | null
  recent_movements: InventoryMovementSummary[]
  generated_at: string
}

// ── Filtros de búsqueda ────────────────────────────────────────────────────────

export interface InventoryMovementListFilters {
  warehouse_id?: string
  family?: InventoryMovementFamily
  movement_type?: InventoryMovementType
  status?: InventoryMovementStatus
  product_id?: string
  product_version?: string
  source_system?: string
  event_type?: string
  document_type?: string
  origin_availability?: InventoryAvailabilityState
  destination_availability?: InventoryAvailabilityState
  origin_quality?: InventoryQualityState
  destination_quality?: InventoryQualityState
  in_transit?: boolean
  damaged?: boolean
  expiring?: boolean
  compensated?: boolean
  integrity_status?: 'OK' | 'WARNING' | 'FAILED' | 'PENDING'
  occurred_from?: string
  occurred_to?: string
  posted_from?: string
  posted_to?: string
  user_id?: string
  search?: string
  correlation_id?: string
  page?: number
  page_size?: number
  cursor?: string
  sort_by?: string
  sort_direction?: 'asc' | 'desc'
}

export interface InventoryKardexQuery {
  warehouse_id: string
  location_id?: string
  product_id: string
  position_id?: string
  availability_state?: InventoryAvailabilityState
  quality_state?: InventoryQualityState
  base_unit_id?: string
  period_from: string
  period_to: string
  page?: number
  page_size?: number
}

// ── Solicitudes ────────────────────────────────────────────────────────────────

export interface CreateInventoryCompensationRequestRequest {
  original_movement_id: string
  compensation_type: 'FULL' | 'PARTIAL'
  reason_code: string
  description: string
  affected_lines: { movement_line_id: string; quantity: DecimalValue; reason: string | null }[]
  evidence_file_ids: string[]
}

export interface SubmitInventoryCompensationRequestRequest {
  compensation_id: string
}

export interface ApproveInventoryCompensationRequestRequest {
  compensation_id: string
  approval_notes: string | null
}

export interface RejectInventoryCompensationRequestRequest {
  compensation_id: string
  rejection_reason: string
}

export interface ExecuteInventoryCompensationRequestRequest {
  compensation_id: string
}

export interface CancelInventoryCompensationRequestRequest {
  compensation_id: string
  cancellation_reason: string
}

export interface CreateInventoryKardexExportRequest {
  format: InventoryKardexExportFormat
  filters: Record<string, unknown>
  include_integrity: boolean
  include_sensitive: boolean
  timezone: string
}

export interface ValidatePreparedInventoryEventRequest {
  event_id: string
}

export interface PostPreparedInventoryEventRequest {
  event_id: string
  idempotency_key: string
}

export interface RetryInventoryPostingRequest {
  posting_id: string
  idempotency_key: string
}

export interface CreateInventoryLedgerCheckpointRequest {
  partition_id: string
}

export interface CreateInventoryLedgerReconciliationJobRequest {
  organization_id: string
  warehouse_id: string
  source_system: string
  period_from: string
  period_to: string
}

export interface InventoryPreparedEventsBatchRequestInput {
  source_system: string
  event_type: string
  warehouse_id: string
  date_from: string
  date_to: string
}
