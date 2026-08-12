export interface InventoryMovementApi {
  id: string
  organization_id: string
  branch_id: string
  warehouse_scope_id: string | null
  movement_code: string
  normalized_movement_code: string
  ledger_partition_key: string
  ledger_sequence: number
  movement_type: string
  movement_family: string
  status: string
  occurred_at: string
  posted_at: string
  reason_code: string | null
  reason_description: string | null
  line_count: number
  total_base_quantity_reference: string | number | null
  currency_code: string | null
  valuation_status: string
  previous_movement_hash: string | null
  movement_hash: string
  canonicalization_version: string
  schema_version: string
  compensation_for_movement_id: string | null
  compensated_by_movement_id: string | null
}

export interface InventoryMovementLineApi {
  id: string
  line_number: number
  product_id: string
  product_version_id: string | null
  product_snapshot: Record<string, unknown>
  quantity: string | number
  unit_id: string
  base_quantity: string | number
  base_unit_id: string
  source_position_id: string | null
  destination_position_id: string | null
  quantity_direction: string
  reason_code: string | null
  content_hash: string
}

export interface InventoryMovementSourceApi {
  id: string
  source_system: string
  source_module: string
  source_event_type: string
  source_event_id: string
  source_event_version: number
  source_document_type: string | null
  source_document_id: string | null
  source_document_code: string | null
  source_entity_type: string
  source_entity_id: string
  source_hash: string
  source_occurred_at: string
  adapter_name: string
  adapter_version: string
}

export interface InventoryPositionApi {
  id: string
  warehouse_id: string | null
  warehouse_location_id: string | null
  boundary_type: string
  product_id: string
  availability_state: string
  quality_state: string
  transit_state: string
  damage_state: string
  expiration_state: string
  dimension_key: string
}

export interface InventoryMovementCapabilitiesApi {
  can_read: boolean
  can_read_sources: boolean
  can_read_snapshot: boolean
  can_read_history: boolean
  can_read_integrity: boolean
}

export interface InventoryMovementDetailApi {
  movement: InventoryMovementApi
  lines: InventoryMovementLineApi[]
  sources: InventoryMovementSourceApi[]
  positions: InventoryPositionApi[]
  compensation: InventoryMovementApi | null
  capabilities: InventoryMovementCapabilitiesApi
  balance_preparation_summary: Record<string, unknown> | null
  traceability_preparation_summary: Record<string, unknown> | null
}

export interface InventoryMovementIntegrityApi {
  verification_status: string
  first_hash: string | null
  last_hash: string | null
  last_sequence: number | null
  algorithm_version: string
  hash_algorithm: string
}

export interface InventoryKardexRowApi {
  movement_id: string
  movement_code: string
  ledger_sequence: number
  movement_type: string
  movement_family: string
  status: string
  occurred_at: string
  posted_at: string
  warehouse_id: string | null
  product_id: string
  product_version_id: string | null
  quantity: string | number
  base_quantity: string | number
  unit_id: string
  base_unit_id: string
  source_position_id: string | null
  destination_position_id: string | null
  source_document_code: string | null
  reason_code: string | null
  source_event_id: string
  movement_hash_partial: string
  compensation_status: string | null
  line_number: number | null
  signed_quantity_display: string | number | null
  signed_base_quantity_display: string | number | null
  quantity_direction: string | null
}

export interface InventoryKardexResponseApi {
  items: InventoryKardexRowApi[]
  total: number
  page: number
  page_size: number
  filters: Record<string, unknown>
}

export interface InventoryKardexRunningQuantityRowApi {
  ledger_sequence: number
  movement_id: string
  movement_code: string
  line_number: number
  signed_delta: string | number
  running_quantity_reference: string | number
  data_quality_status: string
  calculation_scope: string
}

export interface InventoryLedgerVerificationApi {
  verification_status: string
  last_sequence: number | null
  first_hash: string | null
  last_hash: string | null
  algorithm_version: string
}

export interface InventoryLedgerCheckpointApi {
  id: string
  organization_id: string
  ledger_partition_key: string
  from_sequence: number
  to_sequence: number
  movement_count: number
  first_hash: string
  last_hash: string
  manifest_hash: string
  verification_status: string
  verified_at: string | null
  algorithm_version: string
}

export interface InventoryLedgerReconciliationJobApi {
  id: string
  organization_id: string
  scope: Record<string, unknown>
  status: string
  triggered_by: string
  requested_by_user_id: string | null
  started_at: string | null
  completed_at: string | null
  total_events_seen: number
  total_movements_seen: number
  issue_count: number
  summary: Record<string, unknown> | null
}

export interface InventoryLedgerReconciliationResultApi {
  id: string
  job_id: string
  result_code: string
  source_system: string | null
  source_event_type: string | null
  source_event_id: string | null
  movement_id: string | null
  movement_code: string | null
  severity: string
  description: string
  detected_at: string
}

export interface InventoryKardexExportApi {
  id: string
  format: string
  status: string
  row_count: number
  file_path: string | null
  manifest_hash: string | null
  requested_at: string
  completed_at: string | null
  expires_at: string | null
  download_url: string | null
  warnings: Array<Record<string, unknown>>
}
