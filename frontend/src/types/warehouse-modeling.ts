export type WarehouseType =
  | 'DISTRIBUTION_CENTER'
  | 'CROSS_DOCK'
  | 'FULFILLMENT'
  | 'COLD_STORAGE'
  | 'HAZMAT'
  | 'TRANSIT'
  | 'REGIONAL'

export type WarehouseStatus = 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE' | 'ARCHIVED'

export type LocationType =
  | 'ZONE'
  | 'AISLE'
  | 'RACK'
  | 'SHELF'
  | 'BIN'
  | 'DOCK'
  | 'STAGING'
  | 'QUARANTINE'
  | 'DAMAGED'
  | 'COLD'
  | 'VIRTUAL'

export type LocationStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'INACTIVE'
  | 'BLOCKED'
  | 'MAINTENANCE'
  | 'QUARANTINE_ONLY'
  | 'DAMAGED_ONLY'
  | 'ARCHIVED'

export type LocationUsageType =
  | 'STORAGE'
  | 'PICKING'
  | 'RECEIVING'
  | 'DISPATCH'
  | 'CROSS_DOCK'
  | 'TRANSIT'

export interface WarehouseCapabilities {
  can_create_warehouse: boolean
  can_update_warehouse: boolean
  can_activate_warehouse: boolean
  can_create_location: boolean
  can_update_location: boolean
  can_move_location: boolean
  can_block_location: boolean
  can_bulk_create: boolean
  can_manage_capacity: boolean
  can_manage_restrictions: boolean
  can_edit_layout: boolean
  can_activate_layout: boolean
  can_view_QR: boolean
  can_rotate_QR: boolean
  can_download_label: boolean
  can_export_labels: boolean
  can_view_history: boolean
}

export interface Warehouse {
  id: string
  code: string
  name: string
  description: string | null
  organization_id: string
  branch_id: string
  branch_name?: string
  warehouse_type: WarehouseType
  status: WarehouseStatus
  address_text: string
  timezone: string
  manager_user_name: string | null
  is_receiving_enabled: boolean
  is_dispatch_enabled: boolean
  is_inventory_enabled: boolean
  has_temperature_control: boolean
  has_hazmat: boolean
  total_locations: number
  active_locations: number
  blocked_locations: number
  unmapped_locations: number
  active_layout_version: number | null
  created_at: string
  updated_at: string
  capabilities: WarehouseCapabilities
}

export interface WarehouseCreate {
  code: string
  name: string
  description?: string
  branch_id: string
  warehouse_type: WarehouseType
  address_text: string
  timezone: string
  manager_user_id?: string
  is_receiving_enabled?: boolean
  is_dispatch_enabled?: boolean
  is_inventory_enabled?: boolean
  has_temperature_control?: boolean
  has_hazmat?: boolean
}

export interface WarehouseLocation {
  id: string
  warehouse_id: string
  parent_id: string | null
  location_type: LocationType
  code_segment: string
  full_code: string
  name: string
  description: string | null
  usage_type: LocationUsageType
  status: LocationStatus
  block_reason?: string | null
  block_date?: string | null
  sequence: number
  is_pickable: boolean
  is_receivable: boolean
  is_dispatchable: boolean
  is_countable: boolean
  picking_priority: number
  putaway_priority: number
  floor_level: number
  has_children: boolean
  children_count: number
  qr_code_ref: string | null
  layout_coordinates: { x: number; y: number; width: number; height: number; rotation: number } | null
  created_at: string
  updated_at: string
}

export interface WarehouseLocationTreeNode {
  id: string
  code_segment: string
  full_code: string
  name: string
  location_type: LocationType
  status: LocationStatus
  usage_type: LocationUsageType
  has_children: boolean
  children_count: number
  children?: WarehouseLocationTreeNode[]
}

export interface LocationCapacity {
  id: string
  location_id: string
  capacity_type: 'WEIGHT_KG' | 'VOLUME_M3' | 'PALLET_SLOTS' | 'BOX_SLOTS'
  max_value: number
  unit: string
  warning_threshold_pct: number
  critical_threshold_pct: number
  is_active: boolean
  created_at: string
}

export interface LocationCapacityCreate {
  capacity_type: 'WEIGHT_KG' | 'VOLUME_M3' | 'PALLET_SLOTS' | 'BOX_SLOTS'
  max_value: number
  unit: string
  warning_threshold_pct: number
  critical_threshold_pct: number
}

export interface LocationRestriction {
  id: string
  location_id: string
  restriction_type: 'MIN_TEMP' | 'MAX_TEMP' | 'MAX_WEIGHT' | 'ALLOWED_HAZMAT_CLASS' | 'EXCLUDED_CATEGORY'
  operator: 'EQ' | 'LTE' | 'GTE' | 'IN' | 'NOT_IN'
  value: string
  severity: 'WARNING' | 'BLOCKING'
  reason: string
  is_active: boolean
  created_at: string
}

export interface LocationRestrictionCreate {
  restriction_type: 'MIN_TEMP' | 'MAX_TEMP' | 'MAX_WEIGHT' | 'ALLOWED_HAZMAT_CLASS' | 'EXCLUDED_CATEGORY'
  operator: 'EQ' | 'LTE' | 'GTE' | 'IN' | 'NOT_IN'
  value: string
  severity: 'WARNING' | 'BLOCKING'
  reason: string
}

export interface GenerationPreviewItem {
  location_type: LocationType
  count: number
  sample_first_codes: string[]
  sample_last_codes: string[]
}

export interface GenerationPreviewResponse {
  total_nodes: number
  breakdown: GenerationPreviewItem[]
  conflicts: string[]
  request_hash: string
}

export interface LocationGenerationRequest {
  parent_id: string | null
  zones_count?: number
  aisles_count?: number
  racks_count?: number
  shelves_count?: number
  bins_count?: number
  prefix?: string
  padding_length?: number
  usage_type?: LocationUsageType
}

export interface LogicalMapNode {
  id: string
  location_id: string
  full_code: string
  name: string
  location_type: LocationType
  status: LocationStatus
  x: number
  y: number
  width: number
  height: number
  rotation: number
  floor_level: number
  is_mapped: boolean
}

export interface LogicalMapResponse {
  warehouse_id: string
  layout_version: number
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED'
  floor_levels: number[]
  nodes: LogicalMapNode[]
  unmapped_locations: { id: string; full_code: string; location_type: LocationType }[]
}

export interface LocationQRResponse {
  location_id: string
  full_code: string
  public_reference: string
  qr_svg_content: string
  created_at: string
}

export interface WarehouseHistoryEvent {
  id: string
  event_type: string
  actor_name: string
  description: string
  occurred_at: string
}
