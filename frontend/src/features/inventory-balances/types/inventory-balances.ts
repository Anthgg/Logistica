import type {
  DecimalValue,
  PaginatedResponse,
  ProductSummary,
  WarehouseSummary,
  WarehouseLocationSummary,
  UnitOfMeasureSummary,
  UserSummary,
  InventoryAvailabilityState,
  InventoryQualityState,
  InventoryTransitState,
  InventoryDamageState,
  InventoryExpirationState,
  InventoryMovementSummary,
} from '../../inventory-ledger/types/inventory-ledger'

export type {
  DecimalValue,
  PaginatedResponse,
  ProductSummary,
  WarehouseSummary,
  WarehouseLocationSummary,
  UnitOfMeasureSummary,
  UserSummary,
  InventoryAvailabilityState,
  InventoryQualityState,
  InventoryTransitState,
  InventoryDamageState,
  InventoryExpirationState,
  InventoryMovementSummary,
}

export type InventoryBalanceMetricCode =
  | 'PHYSICAL'
  | 'AVAILABLE'
  | 'RESERVED'
  | 'BLOCKED'
  | 'QUARANTINE'
  | 'TRANSIT'
  | 'DAMAGED'
  | 'EXPIRED'
  | 'PENDING_PUTAWAY'
  | 'REJECTED'

export type InventoryBalanceFreshnessState =
  | 'CURRENT'
  | 'NEAR_REAL_TIME'
  | 'LAGGING'
  | 'OBSOLETE'
  | 'REBUILDING'
  | 'INTEGRITY_FAILED'

export type InventoryBalanceDataQualityStatus =
  | 'VERIFIED'
  | 'RECONCILED'
  | 'CURRENT'
  | 'LAGGING'
  | 'PARTIAL_BASELINE'
  | 'MISSING_BASELINE'
  | 'INTEGRITY_FAILED'
  | 'UNIT_CONFLICT'
  | 'POSITION_CONFLICT'
  | 'NEGATIVE'
  | 'REBUILD_REQUIRED'
  | 'UNKNOWN'

export type InventoryBalanceReconciliationStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'
  | 'DIFFERENCES_FOUND'
  | 'RECONCILED'

export type InventoryBalanceRebuildStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'

export type InventoryBalanceAsOfMethod =
  | 'CURRENT'
  | 'CHECKPOINT_REPLAY'
  | 'FULL_REPLAY'

export type InventoryBalanceAlertType =
  | 'NEGATIVE_BALANCE'
  | 'PROJECTION_LAG'
  | 'SEQUENCE_GAP'
  | 'HASH_MISMATCH'
  | 'RECONCILIATION_MISMATCH'
  | 'UNIT_CONFLICT'
  | 'POSITION_CONFLICT'
  | 'BASELINE_MISSING'
  | 'REBUILD_REQUIRED'

// ── Position balance ─────────────────────────────────────────────────────────

export interface InventoryPositionBalance {
  position_id: string
  position_id_display: string
  dimension_key_partial: string
  warehouse_id: string
  warehouse: WarehouseSummary
  location_id: string | null
  location: WarehouseLocationSummary | null
  product_id: string
  product: ProductSummary
  unit_id: string
  unit: UnitOfMeasureSummary
  physical: DecimalValue
  available: DecimalValue
  reserved: DecimalValue
  blocked: DecimalValue
  quarantine: DecimalValue
  transit: DecimalValue
  damaged: DecimalValue
  expired: DecimalValue
  pending_putaway: DecimalValue
  rejected: DecimalValue
  availability_state: InventoryAvailabilityState
  quality_state: InventoryQualityState
  transit_state: InventoryTransitState
  damage_state: InventoryDamageState
  expiration_state: InventoryExpirationState
  freshness_state: InventoryBalanceFreshnessState
  data_quality: InventoryBalanceDataQualityStatus
  ledger_sequence: number
  balance_sequence: number
  projection_lag_movements: number
  last_movement_id: string | null
  last_movement: InventoryMovementSummary | null
  tracking_reference_partial: string | null
  ownership: string | null
  hash_partial: string | null
  reconciliation_status: InventoryBalanceReconciliationStatus | null
  updated_at: string
}

// ── Balance summary (aggregate) ──────────────────────────────────────────────

export interface InventoryBalanceMetric {
  metric_code: InventoryBalanceMetricCode
  label: string
  count_products: number
  count_positions: number
  latest_sequence: number | null
  freshness_state: InventoryBalanceFreshnessState
  data_quality: InventoryBalanceDataQualityStatus
  as_of: string
}

export interface InventoryBalanceSummary {
  organization_id: string
  total_products: number
  total_positions: number
  total_warehouses: number
  total_locations: number
  metrics: InventoryBalanceMetric[]
  latest_movement_sequence: number | null
  balance_sequence: number | null
  projection_lag_movements: number
  freshness_state: InventoryBalanceFreshnessState
  data_quality: InventoryBalanceDataQualityStatus
  as_of: string
}

// ── Product balance ──────────────────────────────────────────────────────────

export interface InventoryProductBalance {
  product_id: string
  product: ProductSummary
  unit_id: string
  unit: UnitOfMeasureSummary
  physical: DecimalValue
  available: DecimalValue
  reserved: DecimalValue
  blocked: DecimalValue
  quarantine: DecimalValue
  transit: DecimalValue
  damaged: DecimalValue
  expired: DecimalValue
  pending_putaway: DecimalValue
  rejected: DecimalValue
  warehouse_count: number
  location_count: number
  position_count: number
  warehouses: WarehouseSummary[]
  latest_movement: InventoryMovementSummary | null
  ledger_sequence: number | null
  balance_sequence: number | null
  freshness_state: InventoryBalanceFreshnessState
  data_quality: InventoryBalanceDataQualityStatus
  as_of: string
}

// ── Warehouse balance ────────────────────────────────────────────────────────

export interface InventoryWarehouseBalance {
  warehouse_id: string
  warehouse: WarehouseSummary
  product_count: number
  location_count: number
  physical_products: number
  available_products: number
  reserved_products: number
  blocked_products: number
  quarantine_products: number
  damaged_products: number
  expired_products: number
  pending_putaway_products: number
  projection_lag_movements: number
  reconciliation_status: InventoryBalanceReconciliationStatus | null
  latest_movement: InventoryMovementSummary | null
  freshness_state: InventoryBalanceFreshnessState
  data_quality: InventoryBalanceDataQualityStatus
  as_of: string
}

// ── Location balance ─────────────────────────────────────────────────────────

export interface InventoryLocationBalance {
  location_id: string
  location: WarehouseLocationSummary
  warehouse_id: string
  warehouse: WarehouseSummary
  product_id: string
  product: ProductSummary
  unit_id: string
  unit: UnitOfMeasureSummary
  physical: DecimalValue
  available: DecimalValue
  reserved: DecimalValue
  blocked: DecimalValue
  quarantine: DecimalValue
  transit: DecimalValue
  damaged: DecimalValue
  expired: DecimalValue
  pending_putaway: DecimalValue
  rejected: DecimalValue
  availability_state: InventoryAvailabilityState
  quality_state: InventoryQualityState
  latest_movement: InventoryMovementSummary | null
  ledger_sequence: number | null
  freshness_state: InventoryBalanceFreshnessState
  data_quality: InventoryBalanceDataQualityStatus
  as_of: string
}

// ── Historical (as-of) ──────────────────────────────────────────────────────

export interface InventoryBalanceAsOfRequest {
  product_id?: string
  warehouse_id?: string
  location_id?: string
  position_id?: string
  as_of_date?: string
  as_of_sequence?: number
  metrics?: InventoryBalanceMetricCode[]
  group_by?: 'PRODUCT' | 'WAREHOUSE' | 'LOCATION' | 'POSITION'
}

export interface InventoryBalanceAsOfResponse {
  method: InventoryBalanceAsOfMethod
  as_of_date: string | null
  as_of_sequence: number | null
  current_sequence: number | null
  positions: InventoryPositionBalance[]
  formulas_used: string[]
  data_quality: InventoryBalanceDataQualityStatus
}

// ── Freshness ────────────────────────────────────────────────────────────────

export interface InventoryBalanceFreshness {
  partition_key: string
  warehouse_id: string | null
  warehouse_name: string | null
  year: number
  head_sequence: number
  balance_sequence: number
  lag_movements: number
  lag_seconds: number | null
  last_movement_at: string | null
  last_projection_at: string | null
  state: InventoryBalanceFreshnessState
  error_message: string | null
}

// ── Formula ──────────────────────────────────────────────────────────────────

export interface InventoryBalanceFormula {
  formula_id: string
  metric_code: InventoryBalanceMetricCode
  metric_label: string
  description: string
  dimension: string
  formula_expression: string
  version: string
  status: 'ACTIVE' | 'INACTIVE' | 'DEPRECATED'
  effective_from: string
  effective_to: string | null
  overlap_allowed: boolean
  mutually_exclusive_group: string | null
  last_activated_at: string | null
}

// ── Reconciliation ───────────────────────────────────────────────────────────

export interface InventoryBalanceReconciliationJob {
  job_id: string
  organization_id: string
  warehouse_id: string | null
  product_id: string | null
  partition_key: string | null
  period_start: string | null
  period_end: string | null
  status: InventoryBalanceReconciliationStatus
  ledger_sequence: number | null
  rebuild_sequence: number | null
  differences_count: number
  duration_ms: number | null
  requested_by: UserSummary | null
  created_at: string
  completed_at: string | null
}

export interface InventoryBalanceReconciliationDifference {
  difference_id: string
  job_id: string
  difference_type: string
  product_id: string
  product: ProductSummary
  warehouse_id: string
  warehouse: WarehouseSummary
  location_id: string | null
  location: WarehouseLocationSummary | null
  position_id: string | null
  position_display: string | null
  projected_quantity: DecimalValue
  replay_quantity: DecimalValue
  delta: DecimalValue
  unit_id: string
  unit: UnitOfMeasureSummary
  expected_sequence: number | null
  current_sequence: number | null
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'DISMISSED'
  diagnostic: string | null
}

// ── Rebuild ──────────────────────────────────────────────────────────────────

export interface InventoryBalanceRebuildJob {
  job_id: string
  organization_id: string
  rebuild_type: 'FULL' | 'PARTITION' | 'WAREHOUSE' | 'PRODUCT' | 'POSITION'
  scope: string
  status: InventoryBalanceRebuildStatus
  initial_sequence: number | null
  final_sequence: number | null
  checkpoint_id: string | null
  positions_processed: number
  differences_found: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  duration_ms: number | null
  requested_by: UserSummary | null
  progress_percent: number | null
  movements_processed: number
  throughput_per_second: number | null
  error_message: string | null
}

// ── Checkpoint ───────────────────────────────────────────────────────────────

export interface InventoryBalanceCheckpoint {
  checkpoint_id: string
  partition_key: string
  sequence: number
  movement_id: string | null
  movement_hash_partial: string | null
  manifest_hash_partial: string | null
  position_count: number
  product_count: number
  formula_version: string
  status: 'VALID' | 'INVALID' | 'PENDING'
  created_at: string
  verified_at: string | null
}

// ── Alerts ───────────────────────────────────────────────────────────────────

export interface InventoryBalanceAlert {
  alert_id: string
  alert_type: InventoryBalanceAlertType
  product_id: string | null
  product: ProductSummary | null
  warehouse_id: string | null
  warehouse: WarehouseSummary | null
  position_id: string | null
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  message: string
  details: Record<string, unknown> | null
  created_at: string
  acknowledged_at: string | null
}

// ── Export ───────────────────────────────────────────────────────────────────

export type InventoryBalanceExportFormat = 'CSV' | 'XLSX' | 'PDF'

export interface InventoryBalanceExportRequest {
  format: InventoryBalanceExportFormat
  filters: Record<string, unknown>
  metrics?: InventoryBalanceMetricCode[]
  group_by?: string
}

export interface InventoryBalanceExport {
  export_id: string
  format: InventoryBalanceExportFormat
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  balance_as_of: string
  balance_sequence: number | null
  formula_version: string | null
  data_quality: InventoryBalanceDataQualityStatus
  reconciliation_status: InventoryBalanceReconciliationStatus | null
  requested_by: UserSummary | null
  file_url: string | null
  file_name: string | null
  file_size_bytes: number | null
  expires_at: string | null
  created_at: string
  completed_at: string | null
  error_message: string | null
}

// ── Availability validation ──────────────────────────────────────────────────

export interface InventoryAvailabilityValidation {
  available: DecimalValue
  unit: UnitOfMeasureSummary
  requested_quantity: DecimalValue
  sufficient: boolean
  balance_sequence: number | null
  projection_lag_movements: number
  data_quality: InventoryBalanceDataQualityStatus
  is_stale: boolean
  warning: string | null
}

// ── Traceability readiness ───────────────────────────────────────────────────

export interface InventoryTraceabilityReadiness {
  product_id: string
  product: ProductSummary
  position_id: string
  position_display: string
  quantity: DecimalValue
  unit: UnitOfMeasureSummary
  observed_tracking_references: string[]
  lot_references: string[]
  serial_references: string[]
  expiration_date: string | null
  packaging_info: Record<string, unknown> | null
  movement_lineage: string[]
  readiness_status: 'READY' | 'PARTIAL' | 'NOT_READY'
  notes: string | null
}

// ── Capabilities ─────────────────────────────────────────────────────────────

export interface InventoryBalanceCapabilities {
  can_view: boolean
  can_view_all: boolean
  can_view_positions: boolean
  can_view_movements: boolean
  can_view_formulas: boolean
  can_view_freshness: boolean
  can_view_integrity: boolean
  can_view_historical: boolean
  can_reconcile: boolean
  can_review_reconciliation: boolean
  can_rebuild: boolean
  can_rebuild_full: boolean
  can_create_checkpoint: boolean
  can_export: boolean
  can_validate_availability: boolean
}

// ── Filters ──────────────────────────────────────────────────────────────────

export interface InventoryBalanceFilters {
  organization_id?: string
  warehouse_id?: string
  location_id?: string
  product_id?: string
  position_id?: string
  availability_state?: InventoryAvailabilityState
  quality_state?: InventoryQualityState
  transit_state?: InventoryTransitState
  damage_state?: InventoryDamageState
  expiration_state?: InventoryExpirationState
  has_physical?: boolean
  has_available?: boolean
  has_reserved?: boolean
  has_blocked?: boolean
  has_quarantine?: boolean
  has_transit?: boolean
  has_damaged?: boolean
  has_expired?: boolean
  has_pending_putaway?: boolean
  has_rejected?: boolean
  is_negative?: boolean
  has_projection_lag?: boolean
  reconciliation_status?: InventoryBalanceReconciliationStatus
  data_quality?: InventoryBalanceDataQualityStatus
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_direction?: 'ASC' | 'DESC'
}
