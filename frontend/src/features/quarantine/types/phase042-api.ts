export interface QualityQuarantineCaseSummaryApi {
  id: string
  quarantine_code: string
  status: string
  severity: string
  quality_result: string | null
  release_status: string
}

export interface QualityQuarantineCaseDetailApi extends QualityQuarantineCaseSummaryApi {
  source_type: string
  inbound_receipt_id: string
  product_id: string
  quarantine_reason: string | null
  quality_decision_status: string
  physical_segregation_status: string
  opened_at: string | null
  created_at: string
}

export interface QualityInspectionSummaryApi {
  id: string
  inspection_code: string
  status: string
  overall_result: string
}

export interface QualityInspectionDetailApi extends QualityInspectionSummaryApi {
  quarantine_case_id: string
  allocation_id: string
  required_control_count: number
  completed_control_count: number
  failed_control_count: number
  evidence_count: number
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface QualityInspectionControlApi {
  id: string
  inspection_id: string
  control_code: string
  name_snapshot: string
  control_type: string
  order_index: number
  required: boolean
  blocking_on_fail: boolean
  status: string
}

export interface MaterializeQualityInspectionRequestApi {
  quarantine_case_id: string
  allocation_id: string
}

export interface QualityDecisionRequestApi {
  inspection_id?: string
  allocation_id: string
  decision_type: string
  quantity: string
  unit_id: string
  base_quantity: string
  reason_code?: string
  reason?: string
}

export interface QualityDecisionApi {
  id: string
  quarantine_case_id: string
  decision_type: string
  decision_status: string
  quantity: string
  unit_id: string
  base_quantity: string
  reason: string | null
  proposed_by: string
  proposed_at: string
  approved_by: string | null
  approved_at: string | null
  created_at: string
}

export interface QualityReleaseRequestApi {
  allocation_id: string
  quality_decision_id: string
  release_type: string
  quantity: string
  unit_id: string
  base_quantity: string
  release_reason?: string
}

export interface QualityReleaseApi {
  id: string
  quarantine_case_id: string
  allocation_id: string
  release_type: string
  quantity: string
  unit_id: string
  base_quantity: string
  status: string
  requested_by: string
  requested_at: string
  approved_by: string | null
  approved_at: string | null
  executed_by: string | null
  executed_at: string | null
  created_at: string
}

export interface QualityRejectionRequestApi {
  allocation_id: string
  quality_decision_id: string
  rejection_type: string
  quantity: string
  unit_id: string
  base_quantity: string
  reason_code?: string
  reason?: string
  future_disposition_recommendation?: string
}

export interface QualityRejectionApi {
  id: string
  quarantine_case_id: string
  allocation_id: string
  rejection_type: string
  quantity: string
  unit_id: string
  base_quantity: string
  status: string
  reason: string | null
  future_disposition_recommendation: string | null
  requested_by: string
  requested_at: string
  created_at: string
}

export interface QualityIntegrityApi {
  case_id: string
  overall_hash: string
  verified: boolean
  components: Record<string, string | number>
}

export interface QuarantineZoneApi {
  id: string
  code: string
  name: string
  status: string
  warehouse_id: string
  warehouse_location_id: string
  priority: number
  hazardous_declared_capable: boolean
}

export interface QualityAvailabilityApi {
  allocation_id: string
  product_id: string
  quantity: string
  unit_id: string
  base_quantity: string
  availability_class: string
  quality_status: string
  quarantine_case_id: string | null
  inspection_id: string | null
  decision_id: string | null
}
