// ── Fase 041 — Tipos de planes de inspección de calidad ────────────────────────

// ── Primitivos reutilizados ─────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
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
}

export interface ProductCategorySummary {
  category_id: string
  code: string
  name: string
  parent_id: string | null
  parent_name: string | null
  status: string
  product_count: number
  children_count: number
  path?: string
}

export interface WarehouseSummary {
  warehouse_id: string
  name: string
  code: string
}

export interface BranchSummary {
  branch_id: string
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

export interface DocumentTypeSummary {
  document_type_id: string
  code: string
  name: string
}

// ── Plan de inspección ──────────────────────────────────────────────────────────

export type QualityInspectionPlanStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'SCHEDULED'
  | 'ACTIVE'
  | 'RETIRED'
  | 'ARCHIVED'

export type QualityInspectionPlanFamily =
  | 'GENERAL'
  | 'PRODUCT'
  | 'CATEGORY'
  | 'WAREHOUSE'
  | 'SUPPLIER'
  | 'TEMPERATURE'
  | 'HAZMAT'

export interface QualityInspectionPlan {
  plan_id: string
  code: string
  name: string
  description: string | null
  family: QualityInspectionPlanFamily
  status: QualityInspectionPlanStatus
  active_version_id: string | null
  active_version_number: number | null
  active_version_valid_from: string | null
  active_version_valid_until: string | null
  priority: number
  conflict_count: number
  product_count: number
  category_count: number
  control_count: number
  has_packaging: boolean
  has_weight: boolean
  has_temperature: boolean
  has_certificates: boolean
  has_sampling: boolean
  created_by: UserSummary
  created_at: string
  updated_at: string
}

export interface QualityInspectionPlanSummary {
  total_plans: number
  active_plans: number
  draft_versions: number
  scheduled_versions: number
  plans_with_conflicts: number
  products_with_plan: number
  categories_with_plan: number
  plans_with_temperature: number
  plans_with_certificates: number
  versions_expiring_soon: number
  products_without_plan: number | null
}

export interface QualityInspectionPlanCapabilities {
  plan_id: string
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_clone: boolean
  can_archive: boolean
  can_create_version: boolean
  can_manage_scopes: boolean
  can_manage_controls: boolean
  can_manage_tolerances: boolean
  can_manage_sampling: boolean
  can_manage_certificates: boolean
  can_validate: boolean
  can_detect_conflicts: boolean
  can_activate: boolean
  can_retire: boolean
  can_preview: boolean
  can_resolve: boolean
  can_view_history: boolean
  can_view_integrity: boolean
  can_view_future_inspection_template: boolean
}

// ── Versiones ──────────────────────────────────────────────────────────────────

export type QualityInspectionPlanVersionStatus =
  | 'DRAFT'
  | 'VALIDATING'
  | 'VALIDATED'
  | 'SCHEDULED'
  | 'ACTIVE'
  | 'RETIRED'

export interface QualityInspectionPlanVersion {
  version_id: string
  plan_id: string
  version_number: number
  status: QualityInspectionPlanVersionStatus
  valid_from: string | null
  valid_until: string | null
  priority: number
  scope_count: number
  control_count: number
  tolerance_count: number
  sampling_count: number
  certificate_count: number
  conflict_count: number
  validation_status: 'NOT_VALIDATED' | 'VALID' | 'INVALID' | 'WARNING'
  validation_errors: string[]
  validation_warnings: string[]
  hash: string | null
  created_by: UserSummary
  validated_by: UserSummary | null
  activated_by: UserSummary | null
  retired_by: UserSummary | null
  created_at: string
  validated_at: string | null
  activated_at: string | null
  retired_at: string | null
  updated_at: string
}

// ── Ámbitos ────────────────────────────────────────────────────────────────────

export type QualityPlanScopeType = 'PRODUCT' | 'CATEGORY'
export type QualityPlanApplicabilityAction = 'INCLUDE' | 'EXCLUDE'

export interface QualityPlanScope {
  scope_id: string
  version_id: string
  scope_type: QualityPlanScopeType
  action: QualityPlanApplicabilityAction
  product_id: string | null
  product_name: string | null
  product_sku: string | null
  category_id: string | null
  category_name: string | null
  category_code: string | null
  include_descendants: boolean
  branch_id: string | null
  branch_name: string | null
  warehouse_id: string | null
  warehouse_name: string | null
  valid_from: string | null
  valid_until: string | null
  priority_override: number | null
  conflict_count: number
  specificity: number
  created_at: string
  updated_at: string
}

// ── Controles ──────────────────────────────────────────────────────────────────

export type QualityControlType =
  | 'PACKAGING'
  | 'WEIGHT'
  | 'TEMPERATURE'
  | 'VISUAL'
  | 'DOCUMENT'
  | 'CERTIFICATE'
  | 'MEASUREMENT'
  | 'COUNT'
  | 'OTHER'

export type QualityControlResultValueType =
  | 'BOOLEAN'
  | 'DECIMAL'
  | 'INTEGER'
  | 'STRING'
  | 'ENUM'
  | 'TEMPERATURE'
  | 'WEIGHT'
  | 'DATE'
  | 'FILE'

export interface QualityControlDefinition {
  control_id: string
  version_id: string
  code: string
  name: string
  description: string | null
  control_type: QualityControlType
  display_order: number
  required: boolean
  blocking_future: boolean
  evidence_required: boolean
  result_value_type: QualityControlResultValueType
  unit_id: string | null
  unit_name: string | null
  tolerance_id: string | null
  tolerance_name: string | null
  sampling_plan_id: string | null
  sampling_plan_name: string | null
  certificate_requirement_id: string | null
  certificate_requirement_name: string | null
  active: boolean
  configuration: ControlConfiguration
  conditions: QualityControlCondition[]
  evidence_types: string[]
  future_responsibilities: string[]
  created_at: string
  updated_at: string
}

export type ControlConfiguration =
  | PackagingControlConfiguration
  | WeightControlConfiguration
  | TemperatureControlConfiguration
  | GenericControlConfiguration

export interface PackagingControlConfiguration {
  type: 'PACKAGING'
  packaging_types: string[]
  check_primary: boolean
  check_secondary: boolean
  check_transport: boolean
  allowed_conditions: string[]
  requires_photography: boolean
  instructions: string | null
}

export interface WeightControlConfiguration {
  type: 'WEIGHT'
  expected_value_source: 'FIXED' | 'PRODUCT' | 'ORDER' | 'DECLARED'
  fixed_value: string | null
  unit_id: string | null
  tolerance_id: string | null
  decimal_scale: number
  requires_scale_reference: boolean
  requires_calibration_reference: boolean
  instructions: string | null
}

export interface TemperatureControlConfiguration {
  type: 'TEMPERATURE'
  range_source: 'PRODUCT' | 'FIXED' | 'DECLARED'
  unit: 'C' | 'F'
  min_value: string | null
  max_value: string | null
  tolerance_id: string | null
  measurement_points: number
  stabilization_time_seconds: number | null
  requires_device: boolean
  photograph_on_exception: boolean
  instructions: string | null
}

export interface GenericControlConfiguration {
  type: 'GENERIC'
  instructions: string | null
}

// ── Condiciones ────────────────────────────────────────────────────────────────

export type QualityControlConditionOperator =
  | 'EQUALS'
  | 'NOT_EQUALS'
  | 'IN_LIST'
  | 'NOT_IN_LIST'
  | 'GREATER_THAN'
  | 'GREATER_THAN_OR_EQUAL'
  | 'LESS_THAN'
  | 'LESS_THAN_OR_EQUAL'
  | 'EXISTS'
  | 'NOT_EXISTS'
  | 'IS_TRUE'
  | 'IS_FALSE'

export interface QualityControlCondition {
  condition_id: string
  control_id: string
  condition_field: string
  operator: QualityControlConditionOperator
  value: string | null
  display_order: number
  group_index: number | null
  created_at: string
}

// ── Tolerancias ────────────────────────────────────────────────────────────────

export type QualityToleranceType =
  | 'ABSOLUTE'
  | 'PERCENTAGE'
  | 'ABSOLUTE_DEVIATION'
  | 'PERCENTAGE_DEVIATION'
  | 'RANGE'

export type QualityToleranceDimension =
  | 'WEIGHT'
  | 'TEMPERATURE'
  | 'LENGTH'
  | 'WIDTH'
  | 'HEIGHT'
  | 'VOLUME'
  | 'COUNT'
  | 'OTHER'

export interface QualityTolerance {
  tolerance_id: string
  code: string
  name: string
  description: string | null
  tolerance_type: QualityToleranceType
  dimension: QualityToleranceDimension
  target_value: string
  min_value: string | null
  max_value: string | null
  lower_deviation: string | null
  upper_deviation: string | null
  lower_percentage: string | null
  upper_percentage: string | null
  unit_id: string | null
  unit_name: string | null
  inclusivity: 'INCLUSIVE' | 'EXCLUSIVE' | 'LOWER_INCLUSIVE' | 'UPPER_INCLUSIVE'
  decimal_scale: number
  rounding_mode: 'HALF_UP' | 'HALF_DOWN' | 'HALF_EVEN' | 'CEIL' | 'FLOOR'
  status: 'ACTIVE' | 'RETIRED'
  valid_from: string | null
  valid_until: string | null
  created_by: UserSummary
  created_at: string
  updated_at: string
}

// ── Muestreo ───────────────────────────────────────────────────────────────────

export type QualitySamplingType =
  | 'FIXED'
  | 'PERCENTAGE'
  | 'MIN_AND_PERCENTAGE'
  | 'ONE_PER_PACKAGE'
  | 'ONE_PER_LOT'
  | 'CUSTOM'

export type QualitySampleUnit = 'UNITS' | 'PACKAGES' | 'LOTS' | 'WEIGHT'
export type QualitySampleSelectionMethod = 'RANDOM' | 'SEQUENTIAL' | 'STRATIFIED' | 'SYSTEMATIC'

export interface QualitySamplingPlan {
  sampling_id: string
  code: string
  name: string
  description: string | null
  sampling_type: QualitySamplingType
  sample_unit: QualitySampleUnit
  fixed_quantity: string | null
  percentage: string | null
  minimum: string | null
  maximum: string | null
  rounding_mode: 'HALF_UP' | 'HALF_DOWN' | 'HALF_EVEN' | 'CEIL' | 'FLOOR'
  selection_method: QualitySampleSelectionMethod
  status: 'ACTIVE' | 'RETIRED'
  valid_from: string | null
  valid_until: string | null
  created_by: UserSummary
  created_at: string
  updated_at: string
}

export interface QualitySampleSizePreview {
  sampling_id: string | null
  population_size: string
  sample_unit: QualitySampleUnit
  calculated_size: string
  unit_name: string
  selection_method: QualitySampleSelectionMethod
  rounding_mode: string
  minimum_applied: boolean
  maximum_applied: boolean
  warnings: string[]
}

// ── Certificados ───────────────────────────────────────────────────────────────

export type QualityCertificateValidationType =
  | 'METADATA_ONLY'
  | 'EXTERNAL_FUTURE'
  | 'NONE'

export interface QualityCertificateRequirement {
  requirement_id: string
  code: string
  name: string
  description: string | null
  document_type_id: string | null
  document_type_name: string | null
  accepted_types: string[]
  required: boolean
  issuer_pattern: string | null
  issue_date_required: boolean
  expiration_required: boolean
  minimum_validity_days: number | null
  reference_number_required: boolean
  file_required: boolean
  metadata_validation: QualityCertificateValidationType
  external_validation: QualityCertificateValidationType
  instructions: string | null
  status: 'ACTIVE' | 'INACTIVE'
  created_by: UserSummary
  created_at: string
  updated_at: string
}

// ── Validación ─────────────────────────────────────────────────────────────────

export type QualityPlanValidationStatus = 'NOT_VALIDATED' | 'VALID' | 'INVALID' | 'WARNING'

export interface QualityPlanValidation {
  version_id: string
  status: QualityPlanValidationStatus
  blocking_errors: QualityPlanValidationError[]
  warnings: QualityPlanValidationWarning[]
  scopes_valid: boolean
  duplicate_controls: string[]
  invalid_units: string[]
  invalid_tolerances: string[]
  invalid_sampling: string[]
  incomplete_certificates: string[]
  conflicts: QualityPlanConflict[]
  inactive_references: string[]
  activation_options: QualityPlanActivationOptions
  server_time: string
  validation_hash: string | null
}

export interface QualityPlanValidationError {
  code: string
  message: string
  field: string | null
  scope_id: string | null
  control_id: string | null
}

export interface QualityPlanValidationWarning {
  code: string
  message: string
  field: string | null
}

export interface QualityPlanActivationOptions {
  can_activate_now: boolean
  requires_scheduling: boolean
  earliest_activation: string | null
  conflicts_to_resolve: number
}

// ── Conflictos ─────────────────────────────────────────────────────────────────

export type QualityPlanConflictLevel = 'INFO' | 'WARNING' | 'ERROR'

export interface QualityPlanConflict {
  conflict_id: string
  current_plan_id: string
  current_plan_code: string
  current_version_id: string
  conflicting_plan_id: string
  conflicting_plan_code: string
  conflicting_version_id: string
  conflict_type: 'SCOPE_OVERLAP' | 'PRIORITY_CONFLICT' | 'VALIDITY_OVERLAP' | 'PRODUCT_AMBIGUITY'
  affected_scope_type: QualityPlanScopeType
  affected_resource_id: string
  affected_resource_name: string
  branch_id: string | null
  branch_name: string | null
  warehouse_id: string | null
  warehouse_name: string | null
  current_valid_from: string | null
  current_valid_until: string | null
  conflicting_valid_from: string | null
  conflicting_valid_until: string | null
  current_priority: number
  conflicting_priority: number
  current_specificity: number
  conflicting_specificity: number
  rule_description: string
  level: QualityPlanConflictLevel
  created_at: string
}

// ── Resolución ─────────────────────────────────────────────────────────────────

export interface QualityPlanResolution {
  product_id: string
  product_name: string
  product_sku: string
  resolved_plan_id: string | null
  resolved_plan_code: string | null
  resolved_version_id: string | null
  resolved_version_number: number | null
  resolved_scope_id: string | null
  specificity: number | null
  valid_from: string | null
  valid_until: string | null
  controls: QualityControlDefinition[]
  tolerances: QualityTolerance[]
  sampling: QualitySamplingPlan | null
  certificates: QualityCertificateRequirement[]
  warnings: string[]
  conflicts: QualityPlanConflict[]
  explanation: string | null
}

// ── Preview ────────────────────────────────────────────────────────────────────

export interface QualityPlanPreview {
  plan_id: string
  plan_code: string
  plan_name: string
  version_id: string
  version_number: number
  scope: QualityPlanScope | null
  specificity: number
  controls: QualityControlDefinition[]
  tolerances: QualityTolerance[]
  sampling: QualitySamplingPlan | null
  certificates: QualityCertificateRequirement[]
  evidence_requirements: string[]
  future_responsibilities: string[]
  warnings: string[]
  exclusions: QualityPlanScope[]
  conflicts: QualityPlanConflict[]
  explanation: string | null
}

// ── Inspección futura ──────────────────────────────────────────────────────────

export interface FutureQualityInspectionTemplate {
  plan_id: string
  plan_code: string
  version_id: string
  version_number: number
  product_id: string | null
  product_name: string | null
  category_id: string | null
  category_name: string | null
  controls: QualityControlDefinition[]
  tolerances: QualityTolerance[]
  sampling: QualitySamplingPlan | null
  certificates: QualityCertificateRequirement[]
  evidence_requirements: string[]
  future_responsibilities: string[]
  estimated_duration_minutes: number | null
}

// ── Integridad ─────────────────────────────────────────────────────────────────

export interface QualityPlanIntegrity {
  version_id: string
  version_hash: string | null
  scopes_hash: string | null
  controls_hash: string | null
  tolerances_hash: string | null
  sampling_hash: string | null
  certificates_hash: string | null
  conditions_hash: string | null
  snapshot_hash: string | null
  algorithm: string
  last_verified_at: string | null
  status: 'VALID' | 'INVALID' | 'PENDING' | 'NOT_VERIFIED'
}

// ── Historial ──────────────────────────────────────────────────────────────────

export type QualityPlanEventType =
  | 'PLAN_CREATED'
  | 'PLAN_UPDATED'
  | 'VERSION_CREATED'
  | 'SCOPE_ADDED'
  | 'SCOPE_MODIFIED'
  | 'SCOPE_REMOVED'
  | 'CONTROL_ADDED'
  | 'CONTROL_MODIFIED'
  | 'CONTROL_REORDERED'
  | 'TOLERANCE_CREATED'
  | 'SAMPLING_CREATED'
  | 'CERTIFICATE_ADDED'
  | 'VALIDATION_FAILED'
  | 'PLAN_VALIDATED'
  | 'CONFLICT_DETECTED'
  | 'VERSION_ACTIVATED'
  | 'VERSION_RETIRED'
  | 'PREVIEW_GENERATED'
  | 'RESOLUTION_EXECUTED'
  | 'INTEGRITY_FAILED'

export interface QualityPlanHistoryEvent {
  event_id: string
  plan_id: string
  version_id: string | null
  event_type: QualityPlanEventType
  timestamp: string
  actor: UserSummary
  action: string
  previous_status: string | null
  new_status: string | null
  reason: string | null
  result: string | null
}

// ── Request/Query types ────────────────────────────────────────────────────────

export interface QualityPlanListQuery {
  page?: number
  page_size?: number
  status?: QualityInspectionPlanStatus | QualityInspectionPlanStatus[]
  family?: QualityInspectionPlanFamily | QualityInspectionPlanFamily[]
  search?: string
  product_id?: string
  category_id?: string
  warehouse_id?: string
  branch_id?: string
  has_conflicts?: boolean
  has_packaging?: boolean
  has_weight?: boolean
  has_temperature?: boolean
  has_certificates?: boolean
  has_sampling?: boolean
  created_by?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface CreateQualityInspectionPlanRequest {
  code: string
  name: string
  description?: string
  family: QualityInspectionPlanFamily
}

export interface UpdateQualityInspectionPlanRequest {
  name?: string
  description?: string
  family?: QualityInspectionPlanFamily
}

export interface CreateQualityPlanVersionRequest {
  valid_from?: string
  valid_until?: string
  priority?: number
}

export interface UpdateQualityPlanVersionRequest {
  valid_from?: string
  valid_until?: string
  priority?: number
}

export interface CreateQualityPlanScopeRequest {
  scope_type: QualityPlanScopeType
  action: QualityPlanApplicabilityAction
  product_id?: string
  category_id?: string
  include_descendants?: boolean
  branch_id?: string
  warehouse_id?: string
  valid_from?: string
  valid_until?: string
  priority_override?: number
}

export interface UpdateQualityPlanScopeRequest {
  include_descendants?: boolean
  branch_id?: string | null
  warehouse_id?: string | null
  valid_from?: string | null
  valid_until?: string | null
  priority_override?: number | null
}

export interface CreateQualityControlRequest {
  code: string
  name: string
  description?: string
  control_type: QualityControlType
  required?: boolean
  blocking_future?: boolean
  evidence_required?: boolean
  result_value_type: QualityControlResultValueType
  unit_id?: string
  tolerance_id?: string
  sampling_plan_id?: string
  certificate_requirement_id?: string
  configuration?: Partial<ControlConfiguration>
}

export interface UpdateQualityControlRequest {
  name?: string
  description?: string
  required?: boolean
  blocking_future?: boolean
  evidence_required?: boolean
  unit_id?: string | null
  tolerance_id?: string | null
  sampling_plan_id?: string | null
  certificate_requirement_id?: string | null
  configuration?: Partial<ControlConfiguration>
}

export interface ReorderQualityControlsRequest {
  ordered_control_ids: string[]
  row_version?: string
}

export interface CreateQualityControlConditionRequest {
  condition_field: string
  operator: QualityControlConditionOperator
  value?: string
  display_order?: number
  group_index?: number
}

export interface CreateQualityToleranceRequest {
  code: string
  name: string
  description?: string
  tolerance_type: QualityToleranceType
  dimension: QualityToleranceDimension
  target_value: string
  min_value?: string
  max_value?: string
  lower_deviation?: string
  upper_deviation?: string
  lower_percentage?: string
  upper_percentage?: string
  unit_id?: string
  inclusivity?: string
  decimal_scale?: number
  rounding_mode?: string
}

export interface CreateQualitySamplingPlanRequest {
  code: string
  name: string
  description?: string
  sampling_type: QualitySamplingType
  sample_unit: QualitySampleUnit
  fixed_quantity?: string
  percentage?: string
  minimum?: string
  maximum?: string
  rounding_mode?: string
  selection_method?: QualitySampleSelectionMethod
}

export interface PreviewSampleSizeRequest {
  sampling_id: string
  population_size: string
  sample_unit: QualitySampleUnit
  product_id?: string
  context?: string
}

export interface CreateQualityCertificateRequirementRequest {
  code: string
  name: string
  description?: string
  document_type_id?: string
  accepted_types?: string[]
  required?: boolean
  issuer_pattern?: string
  issue_date_required?: boolean
  expiration_required?: boolean
  minimum_validity_days?: number
  reference_number_required?: boolean
  file_required?: boolean
  metadata_validation?: QualityCertificateValidationType
  external_validation?: QualityCertificateValidationType
  instructions?: string
}

export interface QualityPlanPreviewRequest {
  product_id?: string
  category_id?: string
  branch_id?: string
  warehouse_id?: string
  date?: string
  quantity?: string
  unit_id?: string
  context?: string
  declared_conditions?: Record<string, string>
}

export interface ActivateQualityPlanVersionRequest {
  confirmation: boolean
  scheduled_for?: string
}

export interface RetireQualityPlanVersionRequest {
  reason: string
  effective_date?: string
  successor_version_id?: string
}
