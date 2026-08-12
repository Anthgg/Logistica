export interface PutawayOrderApi {
  id: string
  organization_id: string
  branch_id: string
  warehouse_id: string
  order_code: string
  status: string
  source_type: string
  priority: number
  task_count: number
  completed_task_count: number
  exception_task_count: number
  issued_at: string | null
  issued_by: string | null
  started_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  cancellation_reason: string | null
  current_revision_number: number
  created_by: string
  created_at: string
  updated_at: string
  row_version: number
}

export interface PutawayTaskApi {
  id: string
  organization_id: string
  warehouse_id: string
  putaway_order_id: string
  task_number: string
  source_allocation_id: string
  recommendation_run_id: string | null
  recommended_location_id: string | null
  selected_location_id: string | null
  source_stage_location_id: string | null
  status: string
  priority: number
  assignment_status: string
  assigned_user_id: string | null
  assigned_team_id: string | null
  assigned_at: string | null
  required_quantity: string | number
  required_unit_id: string
  required_base_quantity: string | number
  placed_quantity: string | number
  placed_base_quantity: string | number
  remaining_quantity: string | number
  remaining_base_quantity: string | number
  scan_policy: string
  expected_product_id: string
  started_at: string | null
  paused_at: string | null
  completed_at: string | null
  exception_count: number
  created_at: string
  updated_at: string
  row_version: number
}

export interface PutawayListApi<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PutawayCapacityProjectionApi {
  organization_id: string
  warehouse_id: string
  location_id: string
  capacity_profile_id: string
  capacity_type: string
  maximum_value: string | number
  safety_margin_value: string | number
  operational_occupied_value: string | number
  active_reserved_value: string | number
  projected_free_value: string | number
  unit_id: string
  data_quality_status: string
  last_placement_at: string | null
  calculated_at: string
  projection_version: number
}
