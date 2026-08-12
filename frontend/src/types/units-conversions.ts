export type MeasurementDimensionCode = 'COUNT' | 'MASS' | 'LENGTH' | 'AREA' | 'VOLUME'

export type UnitScope = 'SYSTEM' | 'ORGANIZATION' | 'PRODUCT'

export type UnitStatus = 'ACTIVE' | 'INACTIVE' | 'DEPRECATED'

export interface UnitCapabilities {
  can_view_units: boolean
  can_create_unit: boolean
  can_update_unit: boolean
  can_activate_unit: boolean
  can_deprecate_unit: boolean
  can_view_conversion_rules: boolean
  can_create_conversion_rule: boolean
  can_update_conversion_rule: boolean
  can_activate_conversion_rule: boolean
  can_retire_conversion_rule: boolean
  can_explain_conversion: boolean
  can_evaluate_conversion: boolean
  can_manage_product_units: boolean
  can_activate_product_units: boolean
  can_manage_packaging: boolean
  can_activate_packaging: boolean
  can_change_base_unit: boolean
  can_view_history: boolean
}

export interface UnitOfMeasure {
  id: string
  code: string
  name: string
  plural_name: string | null
  symbol: string
  dimension: MeasurementDimensionCode
  scope: UnitScope
  status: UnitStatus
  decimal_precision: number
  minimum_increment: string
  is_integer_only: boolean
  is_canonical: boolean
  is_system_protected: boolean
  created_at: string
  updated_at: string
}

export interface UnitOfMeasureCreate {
  code: string
  name: string
  plural_name?: string
  symbol: string
  dimension: MeasurementDimensionCode
  scope: UnitScope
  decimal_precision: number
  minimum_increment: string
  is_integer_only: boolean
}

export interface UnitConversionRule {
  id: string
  source_unit_code: string
  target_unit_code: string
  dimension: MeasurementDimensionCode
  scope: UnitScope
  product_id: string | null
  product_sku?: string
  product_name?: string
  multiplier: string
  numerator: string | null
  denominator: string | null
  allow_inverse: boolean
  rounding_policy: 'HALF_UP' | 'FLOOR' | 'CEIL' | 'EXACT_ONLY'
  status: 'ACTIVE' | 'DRAFT' | 'RETIRED'
  created_at: string
}

export interface UnitConversionRuleCreate {
  source_unit_code: string
  target_unit_code: string
  dimension: MeasurementDimensionCode
  scope: UnitScope
  product_id?: string | null
  multiplier: string
  allow_inverse: boolean
  rounding_policy: 'HALF_UP' | 'FLOOR' | 'CEIL' | 'EXACT_ONLY'
}

export interface ConversionEvaluationRequest {
  quantity: string
  source_unit_code: string
  target_unit_code: string
  product_id?: string
}

export interface ConversionPathStep {
  step_number: number
  source_unit: string
  target_unit: string
  multiplier_used: string
  is_inverse: boolean
}

export interface ConversionEvaluationResponse {
  input_quantity: string
  exact_result: string
  rounded_result: string
  target_unit_code: string
  effective_factor: string
  residual_quantity: string
  is_exact: boolean
  path_steps: ConversionPathStep[]
  evaluated_at: string
}

export interface QuantityDecompositionResult {
  input_quantity: string
  product_sku: string
  levels: {
    packaging_level: string
    unit_code: string
    count: string
    items_contained_per_unit: string
  }[]
  residual_units: string
}

export interface ProductUnitConfiguration {
  product_id: string
  base_unit_code: string
  purchasing_unit_code: string
  receiving_unit_code: string
  storage_unit_code: string
  picking_unit_code: string
  dispatch_unit_code: string
  counting_unit_code: string
  version: number
  status: 'ACTIVE' | 'DRAFT'
}

export interface ProductPackagingDefinition {
  id: string
  product_id: string
  packaging_level: 'PALLET' | 'BOX' | 'PACKAGE' | 'INNER'
  packaging_unit_code: string
  contained_unit_code: string
  contained_quantity: string
  base_equivalency: string
  barcode?: string
  is_active: boolean
}
