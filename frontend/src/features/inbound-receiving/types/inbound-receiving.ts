// ── Fase 039 — Tipos de recepción por escaneo ──────────────────────────────────

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

export interface PurchaseOrderSummary {
  purchase_order_id: string
  code: string
  supplier_name: string
  status: string
}

export interface UnloadingOperationSummary {
  operation_id: string
  dock_name: string
  warehouse_name: string
  cpv_code: string | null
  cit_code: string | null
  supplier_name: string
  carrier_name: string | null
  vehicle_plate: string | null
  started_at: string | null
  completed_at: string | null
  status: string
}

export interface ProductSummary {
  product_id: string
  sku: string
  name: string
  description?: string
  barcode?: string
  category?: string
}

export interface ProductTrackingPolicySummary {
  requires_lot: boolean
  requires_serial: boolean
  requires_expiration: boolean
  serial_uniqueness: 'GLOBAL' | 'PRODUCT' | 'INCONCLUSIVE'
  lot_format?: string
  serial_format?: string
}

export interface ProductPackagingSummary {
  packaging_id: string
  code: string
  name: string
  quantity: string
  unit_code: string
  factor: string
  version: number
}

export interface UnitOfMeasureSummary {
  unit_id: string
  code: string
  name: string
  symbol: string
  unit_type: string
}

// ── Recepción ───────────────────────────────────────────────────────────────────

export type InboundReceiptStatus =
  | 'DRAFT'
  | 'PREPARING'
  | 'READY'
  | 'IN_PROGRESS'
  | 'PAUSED'
  | 'VALIDATING'
  | 'COMPLETED_PARTIAL'
  | 'COMPLETED_TOTAL'
  | 'CANCELLED'

export type InboundReceiptCompletionClassification =
  | 'PARTIAL'
  | 'TOTAL'
  | 'WITH_CANDIDATES'
  | null

export interface InboundReceipt {
  receipt_id: string
  code: string
  cpv_code: string | null
  cit_code: string | null
  purchase_order_codes: string[]
  supplier_id: string
  supplier_name: string
  warehouse_id: string
  warehouse_name: string
  dock_id: string | null
  dock_name: string | null
  unloading_operation_id: string | null
  status: InboundReceiptStatus
  completion_classification: InboundReceiptCompletionClassification
  expected_lines_count: number
  received_lines_count: number
  scan_events_count: number
  unresolved_scans_count: number
  error_count: number
  candidate_count: number
  progress_percent: string | null
  started_at: string | null
  completed_at: string | null
  operator: UserSummary | null
  created_at: string
  updated_at: string
}

export interface InboundReceiptSummary {
  active_receipts: number
  scans_this_shift: number
  lines_completed: number
  unresolved_codes: number
  duplicate_serials: number
  expired_products: number
  partial_receipts: number
  ready_to_close: number
  difference_candidates: number
}

export interface InboundReceiptDetail extends InboundReceipt {
  purchase_orders: PurchaseOrderSummary[]
  unloading_operation: UnloadingOperationSummary | null
  scan_sessions: InboundScanSession[]
  warnings: string[]
  blocking_issues: string[]
}

export interface InboundReceiptProgress {
  receipt_id: string
  total_lines: number
  started_lines: number
  completed_lines: number
  scan_events: number
  unresolved_codes: number
  errors: number
  warnings: number
  candidates: number
  percent: string
  data_quality: string
}

export interface InboundReceiptComparison {
  receipt_id: string
  lines: InboundLineComparison[]
  totals: {
    ordered: string
    shipped: string
    previously_received: string
    received_now: string
    accumulated: string
    pending: string
  }
}

// ── Capabilities ────────────────────────────────────────────────────────────────

export interface InboundReceiptCapabilities {
  receipt_id: string
  can_view: boolean
  can_create: boolean
  can_prepare: boolean
  can_start: boolean
  can_scan: boolean
  can_batch_scan: boolean
  can_manual_entry: boolean
  can_capture_lot: boolean
  can_capture_serial: boolean
  can_capture_expiration: boolean
  can_resolve_unknown: boolean
  can_compensate_scan: boolean
  can_pause: boolean
  can_resume: boolean
  can_validate: boolean
  can_complete_partial: boolean
  can_complete_total: boolean
  can_complete_with_candidates: boolean
  can_cancel: boolean
  can_view_sensitive_identifiers: boolean
  can_view_difference_candidates: boolean
  can_acknowledge_candidate: boolean
  can_view_integrity: boolean
  can_view_history: boolean
  can_view_phase_040_preparation: boolean
}

// ── Líneas ──────────────────────────────────────────────────────────────────────

export interface InboundReceiptExpectedLine {
  line_id: string
  purchase_order_code: string
  po_line_number: number
  product: ProductSummary
  tracking_policy: ProductTrackingPolicySummary
  packaging_options: ProductPackagingSummary[]
  unit: UnitOfMeasureSummary
  ordered_quantity: string
  shipped_quantity: string
  previously_received_quantity: string
  max_receivable: string
  configured_barcodes: string[]
  requirements: string[]
  warnings: string[]
}

export interface InboundReceivedLine {
  line_id: string
  expected_line_id: string
  product: ProductSummary
  unit: UnitOfMeasureSummary
  ordered_quantity: string
  shipped_quantity: string
  previously_received: string
  received_now: string
  accumulated: string
  pending: string
  lot_observations: InboundLotObservation[]
  serial_observations_count: number
  expiration_observations_count: number
  status: InboundReceivedLineStatus
  alerts: string[]
}

export type InboundReceivedLineStatus =
  | 'NOT_STARTED'
  | 'PARTIAL'
  | 'MATCHES_SHIPMENT'
  | 'MATCHES_ORDER'
  | 'BELOW_SHIPMENT'
  | 'ABOVE_SHIPMENT'
  | 'BELOW_ORDER'
  | 'ABOVE_ORDER'
  | 'UNEXPECTED_PRODUCT'
  | 'INCOMPATIBLE_UNIT'
  | 'REVIEW'

export interface InboundLineComparison {
  line_id: string
  product: ProductSummary
  unit: UnitOfMeasureSummary
  ordered: string
  shipped: string
  previously_received: string
  received_now: string
  accumulated: string
  pending: string
  diff_vs_shipment: string
  diff_vs_order: string
  status: InboundReceivedLineStatus
  candidates: number
}

// ── Sesiones de escaneo ─────────────────────────────────────────────────────────

export type InboundScannerType = 'KEYBOARD_WEDGE' | 'CAMERA' | 'MANUAL'

export interface InboundScanSession {
  session_id: string
  receipt_id: string
  scanner_type: InboundScannerType
  operator: UserSummary
  started_at: string
  paused_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  scan_count: number
  status: 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED'
}

// ── Eventos de escaneo ──────────────────────────────────────────────────────────

export type BarcodeSymbology =
  | 'EAN_13'
  | 'EAN_8'
  | 'UPC_A'
  | 'UPC_E'
  | 'CODE_128'
  | 'CODE_39'
  | 'ITF'
  | 'QR_CODE'
  | 'DATA_MATRIX'
  | 'UNKNOWN'

export type BarcodeParseStatus =
  | 'IDENTIFIED'
  | 'UNKNOWN'
  | 'AMBIGUOUS'

export type InboundScanEventStatus =
  | 'APPLIED'
  | 'REQUIRES_QUANTITY'
  | 'REQUIRES_LOT'
  | 'REQUIRES_SERIAL'
  | 'REQUIRES_EXPIRATION'
  | 'UNKNOWN_CODE'
  | 'AMBIGUOUS'
  | 'DUPLICATE'
  | 'REJECTED'
  | 'EXCESS'
  | 'REVIEW'
  | 'COMPENSATED'

export interface InboundScanEvent {
  event_id: string
  session_id: string
  receipt_id: string
  raw_code: string
  symbology: BarcodeSymbology
  parse_status: BarcodeParseStatus
  product: ProductSummary | null
  matched_line_id: string | null
  unit: UnitOfMeasureSummary | null
  applied_quantity: string | null
  tracking_required: ProductTrackingPolicySummary | null
  status: InboundScanEventStatus
  warning: string | null
  error: string | null
  server_timestamp: string
  operator: UserSummary
  next_step: string | null
  client_scan_id?: string
  compensation_event_id?: string | null
}

export interface InboundCodeResolution {
  raw_code: string
  symbology: BarcodeSymbology
  exact_matches: ProductSummary[]
  expected_lines: InboundReceiptExpectedLine[]
  history: { last_seen: string; context: string }[]
  allowed_actions: ('ASSOCIATE_LINE' | 'ASSOCIATE_PRODUCT' | 'MARK_DUPLICATE' | 'REJECT' | 'REQUEST_SUPERVISOR')[]
}

// ── Observaciones ───────────────────────────────────────────────────────────────

export interface InboundLotObservation {
  observation_id: string
  line_id: string
  product: ProductSummary
  lot_code: string
  quantity: string
  unit: UnitOfMeasureSummary
  manufacturing_date: string | null
  expiration_date: string | null
  source: 'SCAN' | 'MANUAL' | 'BATCH'
  comment: string | null
  base_quantity_official: string | null
  created_at: string
}

export interface InboundSerialObservation {
  observation_id: string
  line_id: string
  product: ProductSummary
  serial_code: string
  source: 'SCAN' | 'MANUAL' | 'BATCH'
  duplicate_status: InboundSerialDuplicateStatus
  comment: string | null
  created_at: string
}

export type InboundSerialDuplicateStatus =
  | 'UNIQUE'
  | 'DUPLICATE_IN_RECEIPT'
  | 'DUPLICATE_IN_SYSTEM'
  | 'INCONCLUSIVE'

export interface InboundExpirationObservation {
  observation_id: string
  line_id: string
  product: ProductSummary
  lot_code: string | null
  manufacturing_date: string | null
  expiration_date: string
  source: 'SCAN' | 'MANUAL'
  days_remaining: number | null
  minimum_shelf_life: number | null
  validation_status: InboundExpirationValidationStatus
  warning: string | null
  blocking: boolean
  comment: string | null
  created_at: string
}

export type InboundExpirationValidationStatus =
  | 'VALID'
  | 'NEAR_EXPIRATION'
  | 'EXPIRED'
  | 'BELOW_MINIMUM_SHELF_LIFE'
  | 'PENDING_BACKEND_VALIDATION'

// ── Candidatos de diferencia ────────────────────────────────────────────────────

export type ReceptionDifferenceCandidateType =
  | 'POSSIBLE_SHORTAGE'
  | 'POSSIBLE_SURPLUS'
  | 'POSSIBLE_DAMAGE'
  | 'POSSIBLE_WRONG_PRODUCT'
  | 'UNKNOWN_CODE'
  | 'MISSING_DOCUMENT'
  | 'SEAL_ANOMALY'
  | 'EXPIRED_PRODUCT'
  | 'MISSING_LOT'
  | 'MISSING_SERIAL'
  | 'DUPLICATE_SERIAL'
  | 'INCOMPATIBLE_UNIT'
  | 'OTHER'

export interface ReceptionDifferenceCandidate {
  candidate_id: string
  receipt_id: string
  type: ReceptionDifferenceCandidateType
  line_id: string | null
  product: ProductSummary | null
  expected_quantity: string | null
  observed_quantity: string | null
  unit: UnitOfMeasureSummary | null
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  evidence: FileAssetSummary[]
  status: 'OPEN' | 'ACKNOWLEDGED' | 'DISMISSED' | 'FORMALIZED'
  created_at: string
  updated_at: string
}

export interface ReceptionDifferencePreparation {
  receipt_id: string
  receipt_code: string
  supplier_name: string
  purchase_order_codes: string[]
  expected_lines_count: number
  received_lines_count: number
  comparisons: InboundLineComparison[]
  shortage_candidates: number
  surplus_candidates: number
  damage_candidates: number
  wrong_product_candidates: number
  documents: FileAssetSummary[]
  seal_observations: string[]
  expiration_observations: number
  identifier_observations: number
  evidence: FileAssetSummary[]
  operators: UserSummary[]
  validation_hash: string | null
  overall_hash: string | null
}

// ── Integridad ──────────────────────────────────────────────────────────────────

export interface InboundReceiptIntegrity {
  receipt_id: string
  source_hash: string | null
  expected_lines_hash: string | null
  scan_events_hash: string | null
  compensations_hash: string | null
  received_lines_hash: string | null
  lots_hash: string | null
  serials_hash: string | null
  expirations_hash: string | null
  validation_hash: string | null
  candidates_hash: string | null
  closure_hash: string | null
  algorithm: string
  last_verified_at: string | null
  status: 'VALID' | 'INVALID' | 'PENDING' | 'NOT_VERIFIED'
}

// ── Historial ───────────────────────────────────────────────────────────────────

export type InboundReceiptEventType =
  | 'RECEIPT_CREATED'
  | 'PREPARATION'
  | 'START'
  | 'SESSION_STARTED'
  | 'CODE_SCANNED'
  | 'CODE_RESOLVED'
  | 'CODE_UNRESOLVED'
  | 'QUANTITY_APPLIED'
  | 'LOT_CAPTURED'
  | 'SERIAL_CAPTURED'
  | 'DUPLICATE_DETECTED'
  | 'EXPIRATION_CAPTURED'
  | 'SCAN_COMPENSATED'
  | 'PAUSE'
  | 'RESUME'
  | 'VALIDATION'
  | 'CANDIDATE_DETECTED'
  | 'PARTIAL_COMPLETION'
  | 'TOTAL_COMPLETION'
  | 'CLOSURE'
  | 'INTEGRITY_FAILED'

export interface InboundReceiptHistoryEvent {
  event_id: string
  receipt_id: string
  event_type: InboundReceiptEventType
  timestamp: string
  actor: UserSummary
  action: string
  line_id: string | null
  product: ProductSummary | null
  quantity: string | null
  previous_status: string | null
  new_status: string | null
  result: string | null
  reason: string | null
}

// ── Modos de escaneo ────────────────────────────────────────────────────────────

export type InboundScanMode =
  | 'UNIT'
  | 'CODE_PLUS_QUANTITY'
  | 'PACKAGING'
  | 'SERIAL'
  | 'LOT_PLUS_QUANTITY'
  | 'BLIND_COUNT'
  | 'GUIDED_COUNT'

// ── Condición observada ─────────────────────────────────────────────────────────

export type ReceivedCondition =
  | 'APPARENTLY_CORRECT'
  | 'DAMAGED_PACKAGING'
  | 'DAMAGED_PRODUCT'
  | 'WET'
  | 'OPENED'
  | 'POSSIBLE_CONTAMINATION'
  | 'WRONG_PRODUCT'
  | 'ILLEGIBLE_LABEL'
  | 'TEMPERATURE_CONCERN'
  | 'EXPIRED'
  | 'OTHER'

// ── Request/Query types ─────────────────────────────────────────────────────────

export interface InboundReceiptQuery {
  page?: number
  page_size?: number
  cursor?: string
  status?: InboundReceiptStatus | InboundReceiptStatus[]
  classification?: InboundReceiptCompletionClassification
  warehouse_id?: string
  dock_id?: string
  supplier_id?: string
  product_id?: string
  date_from?: string
  date_to?: string
  search?: string
  has_unresolved?: boolean
  has_errors?: boolean
  has_candidates?: boolean
  has_duplicate_serials?: boolean
  has_expiration?: boolean
  operator_id?: string
  my_receipts?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface CreateInboundReceiptFromUnloadingRequest {
  unloading_operation_id: string
}

export interface CreateInboundScanEventRequest {
  session_id: string
  raw_code: string
  symbology?: BarcodeSymbology
  client_scan_id: string
}

export interface CreateInboundScanEventBatchRequest {
  session_id: string
  events: {
    raw_code: string
    symbology?: BarcodeSymbology
    client_scan_id: string
  }[]
}

export interface ApplyQuantityRequest {
  line_id: string
  quantity: string
  unit_id: string
  lot_code?: string
  expiration_date?: string
  comment?: string
}

export interface CompensateScanRequest {
  event_id: string
  reason: string
  quantity_to_compensate?: string
  evidence_file_ids?: string[]
}

export interface CreateLotObservationRequest {
  line_id: string
  lot_code: string
  quantity: string
  unit_id: string
  manufacturing_date?: string
  expiration_date?: string
  source: 'SCAN' | 'MANUAL'
  comment?: string
}

export interface CreateSerialObservationRequest {
  line_id: string
  serial_code: string
  source: 'SCAN' | 'MANUAL' | 'BATCH'
  comment?: string
}

export interface CreateSerialBatchRequest {
  line_id: string
  serials: string[]
  source: 'BATCH'
}

export interface CreateExpirationObservationRequest {
  line_id: string
  lot_code?: string
  manufacturing_date?: string
  expiration_date: string
  source: 'SCAN' | 'MANUAL'
  comment?: string
}

export interface PauseReceiptRequest {
  reason: string
  comment?: string
  evidence_file_ids?: string[]
}

export interface CompleteReceiptRequest {
  classification: 'PARTIAL' | 'TOTAL' | 'WITH_CANDIDATES'
  confirmation: boolean
}

export interface DismissCandidateRequest {
  reason: string
  evidence_file_ids?: string[]
  confirmation: boolean
}

export interface ResolveUnknownScanRequest {
  action: 'ASSOCIATE_LINE' | 'ASSOCIATE_PRODUCT' | 'MARK_DUPLICATE' | 'REJECT' | 'REQUEST_SUPERVISOR'
  target_line_id?: string
  target_product_id?: string
  reason?: string
}

export interface ManualEntryRequest {
  expected_line_id: string
  product_id: string
  quantity: string
  unit_id: string
  reason: string
  lot_code?: string
  serial_code?: string
  expiration_date?: string
  evidence_file_ids?: string[]
}

// ── Descarga elegible ───────────────────────────────────────────────────────────

export interface EligibleUnloadingOperation {
  operation_id: string
  cpv_code: string | null
  cit_code: string | null
  supplier_name: string
  warehouse_name: string
  dock_name: string
  started_at: string | null
  completed_at: string | null
  purchase_order_codes: string[]
  expected_lines_count: number
  status: string
  warnings: string[]
  already_used: boolean
}

// ── Tipos de evidencia ──────────────────────────────────────────────────────────

export type InboundEvidenceType =
  | 'PRODUCT'
  | 'PACKAGING'
  | 'LABEL'
  | 'LOT'
  | 'SERIAL'
  | 'EXPIRATION'
  | 'APPARENT_DAMAGE'
  | 'ILLEGIBLE_CODE'
  | 'OTHER'
