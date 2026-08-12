// ── Fase 043 — Tipos de ubicación dirigida ──────────────────────────────────────

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
  requires_lot?: boolean
  requires_serial?: boolean
  requires_expiration?: boolean
  temperature_min?: string | null
  temperature_max?: string | null
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
  location_class: string
  is_pickable: boolean
  is_receivable: boolean
  is_quarantine: boolean
  is_damaged: boolean
  temperature_min?: string | null
  temperature_max?: string | null
}

export interface LotSummary {
  lot_id: string
  lot_code: string
  product_id?: string
  product_name?: string
  manufacture_date?: string | null
  expiration_date?: string | null
  status?: string
}

export interface SerialSummary {
  serial_id: string
  serial_code: string
  product_id?: string
  product_name?: string
  status?: string
}

export interface PalletSummary {
  pallet_id: string
  pallet_code: string
  warehouse_id?: string
  location_id?: string | null
  status?: string
}

// ── Órdenes de ubicación ───────────────────────────────────────────────────────

export type PutawayOrderStatus =
  | 'draft'
  | 'planned'
  | 'in_progress'
  | 'partially_completed'
  | 'completed'
  | 'cancelled'
  | 'on_hold'

export type PutawayOrderPriority = 'low' | 'normal' | 'high' | 'urgent'

export type PutawayOrderSource =
  | 'reception'
  | 'transfer'
  | 'return'
  | 'quality_release'
  | 'manual'

export interface PutawayOrderSummary {
  order_id: string
  order_number: string
  warehouse_id: string
  warehouse: WarehouseSummary
  status: PutawayOrderStatus
  priority: PutawayOrderPriority
  source_type: PutawayOrderSource
  source_id: string | null
  source_number: string | null
  total_lines: number
  completed_lines: number
  pending_lines: number
  assigned_user_id: string | null
  assigned_user: UserSummary | null
  due_at: string | null
  created_at: string
  updated_at: string
}

export interface PutawayOrderLine {
  line_id: string
  order_id: string
  product_id: string
  product: ProductSummary
  quantity: DecimalValue
  unit_id: string
  unit: UnitOfMeasureSummary
  lot_id: string | null
  lot: LotSummary | null
  serial_id: string | null
  serial: SerialSummary | null
  pallet_id: string | null
  pallet: PalletSummary | null
  suggested_location_id: string | null
  suggested_location: WarehouseLocationSummary | null
  assigned_location_id: string | null
  assigned_location: WarehouseLocationSummary | null
  status: PutawayLineStatus
  reservation_id: string | null
  priority: PutawayOrderPriority
  temperature_requirement?: string | null
  hazmat_class?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export type PutawayLineStatus =
  | 'pending'
  | 'in_transit'
  | 'placed'
  | 'confirmed'
  | 'diverted'
  | 'exception'

export interface PutawayOrder extends PutawayOrderSummary {
  lines: PutawayOrderLine[]
  notes?: string | null
  metadata?: Record<string, unknown>
  created_by: UserSummary
  updated_by: UserSummary | null
}

// ── Tareas de ubicación ────────────────────────────────────────────────────────

export type PutawayTaskStatus =
  | 'pending'
  | 'in_progress'
  | 'on_hold'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type PutawayTaskType =
  | 'scan_destination'
  | 'place_item'
  | 'confirm_placement'
  | 'divert_item'
  | 'split_item'

export interface PutawayTask {
  task_id: string
  order_id: string
  line_id: string
  product: ProductSummary
  quantity: DecimalValue
  unit: UnitOfMeasureSummary
  lot: LotSummary | null
  serial: SerialSummary | null
  pallet: PalletSummary | null
  source_location: WarehouseLocationSummary
  destination_location: WarehouseLocationSummary | null
  suggested_destination: WarehouseLocationSummary | null
  status: PutawayTaskStatus
  task_type: PutawayTaskType
  assigned_user_id: string | null
  assigned_user: UserSummary | null
  started_at: string | null
  completed_at: string | null
  hold_reason: string | null
  exception_reason: string | null
  scan_history: PutawayScanEvent[]
  created_at: string
  updated_at: string
}

export interface PutawayScanEvent {
  scan_id: string
  scanned_code: string
  scan_type: 'source' | 'destination' | 'product' | 'pallet' | 'lot' | 'serial'
  is_valid: boolean
  matched_location_id: string | null
  scanned_at: string
  scanned_by: UserSummary
}

// ── Candidatos de ubicación ────────────────────────────────────────────────────

export type LocationCandidateReason =
  | 'capacity'
  | 'compatibility'
  | 'proximity'
  | 'rotation'
  | 'zone_rule'
  | 'temperature'
  | 'hazmat'
  | 'lot_grouping'

export interface LocationCandidate {
  location_id: string
  location: WarehouseLocationSummary
  score: DecimalValue
  rank: number
  reasons: LocationCandidateReason[]
  capacity_available: DecimalValue
  capacity_total: DecimalValue
  capacity_percentage: DecimalValue
  distance_from_source: DecimalValue | null
  estimated_walk_time_seconds: number | null
  temperature_match: boolean
  hazmat_compatible: boolean
  lot_grouping_match: boolean
  product_compatible: boolean
  zone_preferred: boolean
  warnings: string[]
  metadata?: Record<string, unknown>
}

export interface LocationCandidatesResponse {
  line_id: string
  product: ProductSummary
  quantity: DecimalValue
  candidates: LocationCandidate[]
  generated_at: string
  algorithm_version: string
  parameters_used: Record<string, unknown>
}

// ── Capacidad ──────────────────────────────────────────────────────────────────

export interface LocationCapacity {
  location_id: string
  location: WarehouseLocationSummary
  total_capacity: DecimalValue
  used_capacity: DecimalValue
  available_capacity: DecimalValue
  utilization_percentage: DecimalValue
  unit: UnitOfMeasureSummary
  weight_capacity_kg: DecimalValue | null
  weight_used_kg: DecimalValue | null
  volume_capacity_m3: DecimalValue | null
  volume_used_m3: DecimalValue | null
  pallet_positions: number | null
  pallet_positions_used: number | null
  last_updated: string
}

export interface WarehouseCapacitySummary {
  warehouse_id: string
  total_locations: number
  available_locations: number
  full_locations: number
  quarantine_locations: number
  overall_utilization: DecimalValue
  by_zone: ZoneCapacitySummary[]
}

export interface ZoneCapacitySummary {
  zone: string
  total_locations: number
  available_locations: number
  full_locations: number
  utilization: DecimalValue
}

// ── Compatibilidad ─────────────────────────────────────────────────────────────

export type IncompatibilitySeverity = 'blocked' | 'restricted' | 'warning'

export interface ProductLocationCompatibility {
  product_id: string
  location_id: string
  is_compatible: boolean
  temperature_compatible: boolean
  hazmat_compatible: boolean
  category_allowed: boolean
  incompatibilities: LocationIncompatibility[]
  effective_rules: CompatibilityRule[]
}

export interface LocationIncompatibility {
  rule_id: string
  rule_name: string
  severity: IncompatibilitySeverity
  reason: string
  product_ids?: string[]
  location_ids?: string[]
}

export interface CompatibilityRule {
  rule_id: string
  rule_name: string
  description: string
  rule_type: 'product_category' | 'temperature' | 'hazmat' | 'lot_group' | 'custom'
  conditions: Record<string, unknown>
  action: 'allow' | 'block' | 'restrict'
  priority: number
  is_active: boolean
}

// ── Rotación ───────────────────────────────────────────────────────────────────

export type RotationMethod = 'FIFO' | 'FEFO' | 'LIFO' | 'CUSTOM'

export interface RotationDirective {
  directive_id: string
  product_id: string
  product: ProductSummary
  warehouse_id: string
  method: RotationMethod
  lot_id: string | null
  lot: LotSummary | null
  expiration_date: string | null
  manufacture_date: string | null
  current_location_id: string | null
  current_location: WarehouseLocationSummary | null
  quantity_available: DecimalValue
  oldest_days_in_stock: number | null
  is_expired: boolean
  is_expiring_soon: boolean
  days_until_expiration: number | null
}

export interface RotationComplianceReport {
  warehouse_id: string
  total_lines_evaluated: number
  fifo_compliant: number
  fefo_compliant: number
  non_compliant: number
  compliance_percentage: DecimalValue
  violations: RotationViolation[]
  generated_at: string
}

export interface RotationViolation {
  line_id: string
  product: ProductSummary
  method: RotationMethod
  expected_location_id: string
  expected_location: WarehouseLocationSummary
  actual_location_id: string | null
  actual_location: WarehouseLocationSummary | null
  lot_id: string | null
  lot: LotSummary | null
  expiration_date: string | null
  days_old: number
  severity: 'critical' | 'warning' | 'info'
}

// ── Proximidad ─────────────────────────────────────────────────────────────────

export interface ProximityMatrix {
  warehouse_id: string
  source_locations: ProximitySourceLocation[]
  generated_at: string
}

export interface ProximitySourceLocation {
  location_id: string
  location: WarehouseLocationSummary
  nearby_destinations: ProximityDestination[]
}

export interface ProximityDestination {
  location_id: string
  location: WarehouseLocationSummary
  distance_meters: DecimalValue
  walk_time_seconds: number
  is_preferred: boolean
  zone_match: boolean
}

// ── Excepciones ────────────────────────────────────────────────────────────────

export type PutawayExceptionType =
  | 'capacity_exceeded'
  | 'incompatible_product'
  | 'rotation_violation'
  | 'location_unavailable'
  | 'scan_mismatch'
  | 'lot_mismatch'
  | 'serial_mismatch'
  | 'temperature_violation'
  | 'hazmat_violation'
  | 'manual_override'

export type PutawayExceptionSeverity = 'low' | 'medium' | 'high' | 'critical'

export type PutawayExceptionStatus =
  | 'open'
  | 'acknowledged'
  | 'in_progress'
  | 'resolved'
  | 'escalated'

export interface PutawayException {
  exception_id: string
  order_id: string
  line_id: string | null
  task_id: string | null
  exception_type: PutawayExceptionType
  severity: PutawayExceptionSeverity
  status: PutawayExceptionStatus
  title: string
  description: string
  suggested_action: string
  product: ProductSummary | null
  source_location: WarehouseLocationSummary | null
  destination_location: WarehouseLocationSummary | null
  assigned_user_id: string | null
  assigned_user: UserSummary | null
  resolved_by: UserSummary | null
  resolved_at: string | null
  resolution_notes: string | null
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ── Dashboard ──────────────────────────────────────────────────────────────────

export interface PutawayDashboardSummary {
  orders_summary: PutawayOrdersSummaryMetrics
  tasks_summary: PutawayTasksSummaryMetrics
  exceptions_summary: PutawayExceptionsSummaryMetrics
  capacity_overview: WarehouseCapacitySummary
  rotation_compliance: RotationComplianceReport
  overdue_orders: PutawayOrderSummary[]
  pending_tasks: PutawayTask[]
  open_exceptions: PutawayException[]
  recent_activity: PutawayActivityEvent[]
  generated_at: string
}

export interface PutawayOrdersSummaryMetrics {
  total_orders: number
  draft: number
  planned: number
  in_progress: number
  completed_today: number
  on_hold: number
  overdue: number
  avg_completion_time_minutes: DecimalValue | null
}

export interface PutawayTasksSummaryMetrics {
  total_tasks: number
  pending: number
  in_progress: number
  on_hold: number
  completed_today: number
  failed: number
  avg_task_time_minutes: DecimalValue | null
}

export interface PutawayExceptionsSummaryMetrics {
  total_open: number
  critical: number
  high: number
  medium: number
  low: number
  resolved_today: number
  avg_resolution_time_minutes: DecimalValue | null
}

export interface PutawayActivityEvent {
  event_id: string
  event_type: 'order_created' | 'task_assigned' | 'task_completed' | 'exception_opened' | 'exception_resolved' | 'placement_confirmed' | 'diversion'
  description: string
  order_id: string | null
  task_id: string | null
  user: UserSummary
  timestamp: string
  metadata?: Record<string, unknown>
}

// ── Historial ──────────────────────────────────────────────────────────────────

export interface PutawayHistoryEntry {
  entry_id: string
  entity_type: 'order' | 'line' | 'task' | 'exception'
  entity_id: string
  action: string
  description: string
  previous_state: Record<string, unknown> | null
  new_state: Record<string, unknown> | null
  user: UserSummary
  timestamp: string
  ip_address?: string
  metadata?: Record<string, unknown>
}

// ── Integridad ─────────────────────────────────────────────────────────────────

export interface PutawayIntegrityReport {
  order_id: string
  checks: PutawayIntegrityCheck[]
  overall_status: 'pass' | 'warning' | 'fail'
  generated_at: string
}

export interface PutawayIntegrityCheck {
  check_id: string
  check_name: string
  status: 'pass' | 'warning' | 'fail'
  description: string
  details?: Record<string, unknown>
}

// ── Documentos ─────────────────────────────────────────────────────────────────

export interface PutawayDocument {
  document_id: string
  document_type: 'putaway_label' | 'putaway_summary' | 'diversion_report'
  order_id: string
  format: 'pdf' | 'html' | 'csv'
  url: string
  generated_at: string
  generated_by: UserSummary
}

// ── Planificación ──────────────────────────────────────────────────────────────

export interface PutawayPlanRequest {
  order_id: string
  strategy: PutawayStrategy
  parameters: PutawayPlanParameters
}

export type PutawayStrategy =
  | 'auto_optimal'
  | 'capacity_first'
  | 'proximity_first'
  | 'rotation_first'
  | 'manual'

export interface PutawayPlanParameters {
  prefer_closest: boolean
  respect_rotation: boolean
  max_distance_meters: number | null
  preferred_zones: string[]
  excluded_zones: string[]
  allow_split: boolean
  max_locations_per_line: number
  temperature_enforcement: 'strict' | 'advisory'
  hazmat_enforcement: 'strict' | 'advisory'
}

export interface PutawayPlanResult {
  order_id: string
  strategy: PutawayStrategy
  lines_planned: number
  lines_with_candidates: number
  lines_without_candidates: number
  generated_at: string
  parameters_used: PutawayPlanParameters
}

// ── Workspace móvil ────────────────────────────────────────────────────────────

export interface MobilePutawayWorkspace {
  user_id: string
  assigned_tasks: PutawayTask[]
  active_task: PutawayTask | null
  orders_with_pending_tasks: PutawayOrderSummary[]
  scanner_config: MobileScannerConfig
}

export interface MobileScannerConfig {
  enable_camera: boolean
  enable_keyboard_wedge: boolean
  enable_bluetooth: boolean
  auto_submit: boolean
  beep_on_success: boolean
  vibrate_on_error: boolean
}

export interface MobileScanResult {
  scan_id: string
  code: string
  scan_type: 'barcode' | 'qr_code' | 'rfid' | 'nfc'
  matched_entity_type: 'location' | 'product' | 'pallet' | 'lot' | 'serial' | 'none'
  matched_entity_id: string | null
  is_valid: boolean
  timestamp: string
}

// ── Solicitudes de creación/actualización ───────────────────────────────────────

export interface CreatePutawayOrderRequest {
  warehouse_id: string
  source_type: PutawayOrderSource
  source_id?: string
  priority?: PutawayOrderPriority
  assigned_user_id?: string
  due_at?: string
  notes?: string
  lines: CreatePutawayOrderLineRequest[]
}

export interface CreatePutawayOrderLineRequest {
  product_id: string
  quantity: DecimalValue
  unit_id: string
  lot_id?: string
  serial_id?: string
  pallet_id?: string
  temperature_requirement?: string
  hazmat_class?: string
  notes?: string
}

export interface UpdatePutawayOrderRequest {
  priority?: PutawayOrderPriority
  assigned_user_id?: string | null
  due_at?: string | null
  notes?: string | null
  status?: PutawayOrderStatus
}

export interface AssignPutawayTaskRequest {
  task_id: string
  user_id: string
}

export interface StartPutawayTaskRequest {
  task_id: string
}

export interface CompletePutawayTaskRequest {
  task_id: string
  destination_location_id: string
  quantity_placed: DecimalValue
  scan_evidence: PutawayScanEvent[]
  notes?: string
}

export interface DivertPutawayTaskRequest {
  task_id: string
  diversion_reason: string
  alternative_location_id?: string
  notes?: string
}

export interface ConfirmPutawayPlacementRequest {
  order_id: string
  line_id: string
  location_id: string
  quantity: DecimalValue
  lot_id?: string
  serial_id?: string
}

export interface UpdatePutawayTaskPriorityRequest {
  task_id: string
  priority: PutawayOrderPriority
}

export interface BulkAssignPutawayTasksRequest {
  task_ids: string[]
  user_id: string
}

export interface BulkCompletePutawayTasksRequest {
  completions: CompletePutawayTaskRequest[]
}

// ── Parámetros de consulta ─────────────────────────────────────────────────────

export interface PutawayOrderListParams {
  warehouse_id?: string
  status?: PutawayOrderStatus | PutawayOrderStatus[]
  priority?: PutawayOrderPriority | PutawayOrderPriority[]
  source_type?: PutawayOrderSource
  assigned_user_id?: string
  created_from?: string
  created_to?: string
  due_from?: string
  due_to?: string
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_direction?: 'asc' | 'desc'
}

export interface PutawayTaskListParams {
  order_id?: string
  warehouse_id?: string
  status?: PutawayTaskStatus | PutawayTaskStatus[]
  assigned_user_id?: string
  product_id?: string
  created_from?: string
  created_to?: string
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_direction?: 'asc' | 'desc'
}

export interface PutawayExceptionListParams {
  order_id?: string
  warehouse_id?: string
  exception_type?: PutawayExceptionType | PutawayExceptionType[]
  severity?: PutawayExceptionSeverity | PutawayExceptionSeverity[]
  status?: PutawayExceptionStatus | PutawayExceptionStatus[]
  assigned_user_id?: string
  created_from?: string
  created_to?: string
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_direction?: 'asc' | 'desc'
}

export interface PutawayHistoryParams {
  entity_type?: 'order' | 'line' | 'task' | 'exception'
  entity_id?: string
  action?: string
  user_id?: string
  from?: string
  to?: string
  page?: number
  page_size?: number
}
