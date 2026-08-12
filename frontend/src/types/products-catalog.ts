export type ProductType =
  | 'FINISHED_GOOD'
  | 'RAW_MATERIAL'
  | 'PACKAGING'
  | 'SPARE_PART'
  | 'MERCHANDISE'
  | 'SUPPLY'

export type ProductStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'SUSPENDED'
  | 'DISCONTINUED'
  | 'ARCHIVED'

export type TrackingType = 'NONE' | 'LOT' | 'SERIAL' | 'LOT_AND_SERIAL'

export interface ProductCapabilities {
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_activate: boolean
  can_suspend: boolean
  can_discontinue: boolean
  can_archive: boolean
  can_manage_identifiers: boolean
  can_manage_tracking: boolean
  can_manage_conditions: boolean
  can_view_history: boolean
  can_create_version: boolean
  can_activate_version: boolean
}

export interface ProductCategory {
  id: string
  code: string
  name: string
  description: string | null
  parent_id: string | null
  parent_name?: string | null
  hierarchy_path: string
  is_active: boolean
  subcategories_count: number
  created_at: string
}

export interface ProductCategoryCreate {
  code: string
  name: string
  description?: string
  parent_id?: string | null
}

export interface ProductBrand {
  id: string
  code: string
  name: string
  manufacturer_ref: string | null
  country_code: string | null
  is_active: boolean
  products_count: number
  created_at: string
}

export interface ProductBrandCreate {
  code: string
  name: string
  manufacturer_ref?: string
  country_code?: string
}

export interface ProductIdentifier {
  id: string
  product_id: string
  identifier_type: 'SKU' | 'EAN13' | 'UPCA' | 'CODE128' | 'GTIN14' | 'INTERNAL'
  value: string
  symbology: 'BARCODE_128' | 'EAN_13' | 'QR_CODE'
  issuer: string | null
  is_primary: boolean
  is_active: boolean
  created_at: string
}

export interface ProductIdentifierCreate {
  identifier_type: 'SKU' | 'EAN13' | 'UPCA' | 'CODE128' | 'GTIN14' | 'INTERNAL'
  value: string
  symbology: 'BARCODE_128' | 'EAN_13' | 'QR_CODE'
  issuer?: string
  is_primary?: boolean
}

export interface ProductPhysicalProfile {
  product_id: string
  net_weight_kg: string
  gross_weight_kg: string
  length_cm: string
  width_cm: string
  height_cm: string
  reported_volume_m3: string
  calculated_volume_m3: string
  measurement_source: string
  verified_at: string | null
}

export interface ProductPhysicalProfileUpdate {
  net_weight_kg: string
  gross_weight_kg: string
  length_cm: string
  width_cm: string
  height_cm: string
  reported_volume_m3: string
}

export interface ProductTrackingPolicy {
  product_id: string
  tracking_type: TrackingType
  requires_expiration: boolean
  requires_manufacturing_date: boolean
  total_shelf_life_days: number | null
  min_remaining_shelf_life_days: number | null
  allow_mixed_lots: boolean
  require_supplier_lot: boolean
}

export interface ProductTrackingPolicyUpdate {
  tracking_type: TrackingType
  requires_expiration: boolean
  requires_manufacturing_date: boolean
  total_shelf_life_days?: number | null
  min_remaining_shelf_life_days?: number | null
  allow_mixed_lots?: boolean
  require_supplier_lot?: boolean
}

export interface ProductStorageCondition {
  id: string
  product_id: string
  condition_type: 'TEMPERATURE' | 'HUMIDITY' | 'COLD_CHAIN' | 'STACKING'
  min_value: string | null
  max_value: string | null
  unit: string
  is_mandatory: boolean
  severity: 'WARNING' | 'BLOCKING'
  instruction: string
  is_active: boolean
}

export interface ProductHandlingCondition {
  id: string
  product_id: string
  handling_type: 'FRAGILE' | 'KEEP_DRY' | 'THIS_SIDE_UP' | 'TWO_PERSON_LIFT' | 'PPE_REQUIRED'
  instruction: string
  severity: 'WARNING' | 'BLOCKING'
  is_active: boolean
}

export interface Product {
  id: string
  sku: string
  name: string
  short_name: string | null
  description: string | null
  product_type: ProductType
  category_id: string
  category_name?: string
  brand_id: string | null
  brand_name?: string
  base_unit: string
  status: ProductStatus
  active_version: number
  primary_identifier_value: string | null
  tracking_type: TrackingType
  requires_expiration: boolean
  is_fragile: boolean
  has_cold_chain: boolean
  has_hazmat: boolean
  is_high_value: boolean
  created_at: string
  updated_at: string
  capabilities: ProductCapabilities
}

export interface ProductCreate {
  sku: string
  name: string
  short_name?: string
  description?: string
  product_type: ProductType
  category_id: string
  brand_id?: string
  base_unit: string
  is_fragile?: boolean
  has_cold_chain?: boolean
  has_hazmat?: boolean
  is_high_value?: boolean
}

export interface ProductHistoryEvent {
  id: string
  event_type: string
  actor_name: string
  description: string
  occurred_at: string
}
