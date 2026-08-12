// ─── Purchase Requisitions – Strict TypeScript Types ────────────────────────

export type PurchaseRequisitionStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'RETURNED'
  | 'APPROVED'
  | 'REJECTED'
  | 'WITHDRAWN'
  | 'CANCELLED'
  | 'ARCHIVED'

export type PurchaseRequisitionPriority =
  | 'LOW'
  | 'NORMAL'
  | 'HIGH'
  | 'URGENT'
  | 'CRITICAL'

export type CostCenterStatus = 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'

export interface CostCenter {
  id: string
  organization_id: string
  branch_id: string | null
  code: string
  normalized_code: string
  name: string
  description: string | null
  responsible_user_id: string | null
  parent_cost_center_id: string | null
  status: CostCenterStatus
  valid_from: string
  valid_until: string | null
  created_by: string
  updated_by: string
  row_version: number
  created_at: string
  updated_at: string
}

export interface CostCenterCreate {
  code: string
  name: string
  description?: string | null
  branch_id?: string | null
  responsible_user_id?: string | null
  parent_cost_center_id?: string | null
  valid_from: string
  valid_until?: string | null
}

export interface CostCenterUpdate {
  name?: string
  description?: string | null
  responsible_user_id?: string | null
  valid_until?: string | null
  row_version: number
}

export interface PurchaseRequisitionLine {
  id: string
  line_number: number
  product_id: string
  product_sku: string
  product_name: string
  product_brand_name: string | null
  requested_quantity: string // decimal string, e.g. "10.5"
  unit_of_measure_id: string
  unit_of_measure_code: string
  base_quantity: string | null // decimal string returned by backend
  base_unit_code: string | null
  conversion_rule_summary: string | null
  required_date: string // ISO date
  destination_warehouse_id: string
  destination_warehouse_name: string
  justification: string | null
  notes: string | null
}

export interface PurchaseRequisitionLineCreate {
  product_id: string
  requested_quantity: string // decimal string
  unit_of_measure_id: string
  required_date: string
  destination_warehouse_id: string
  justification?: string
  notes?: string
}

export interface PurchaseRequisitionRevision {
  id: string
  requisition_id: string
  revision_number: number
  status: PurchaseRequisitionStatus
  summary_justification: string
  lines_count: number
  created_by_user_name: string
  partial_hash: string
  is_current: boolean
  created_at: string
}

export interface PurchaseRequisitionDecision {
  id: string
  requisition_id: string
  revision_number: number
  decision_type: 'APPROVE' | 'REJECT' | 'RETURN' | 'START_REVIEW' | 'WITHDRAW' | 'CANCEL'
  decided_by_user_name: string
  comments: string
  conditions: string | null
  decided_at: string
}

export interface PurchaseRequisitionComment {
  id: string
  requisition_id: string
  revision_number: number
  user_name: string
  comment_type: 'ORDINARY' | 'DECISION' | 'SYSTEM'
  content: string
  created_at: string
}

export interface PurchaseRequisitionValidation {
  is_valid: boolean
  blocking_errors: string[]
  warnings: string[]
  duplicate_candidates_count: number
  evaluated_at: string
}

export interface PurchaseRequisitionDuplicateCandidate {
  id: string
  requisition_code: string
  applicant_name: string
  cost_center_name: string
  created_at: string
  status: PurchaseRequisitionStatus
  similarity_score: number
  matching_products: string[]
}

export interface PurchaseRequisitionCapabilities {
  can_view: boolean
  can_update: boolean
  can_validate: boolean
  can_submit: boolean
  can_start_review: boolean
  can_approve: boolean
  can_reject: boolean
  can_return: boolean
  can_withdraw: boolean
  can_cancel: boolean
  can_copy: boolean
  can_comment: boolean
  can_manage_lines: boolean
  can_manage_files: boolean
  can_preview: boolean
  can_download: boolean
  can_view_history: boolean
  can_view_revisions: boolean
}

// ─── Main Entities ──────────────────────────────────────────────────────────

export interface PurchaseRequisition {
  id: string
  requisition_code: string
  active_revision_number: number
  applicant_user_id: string
  applicant_user_name: string
  branch_id: string
  branch_name: string
  cost_center_id: string
  cost_center_code: string
  cost_center_name: string
  priority: PurchaseRequisitionPriority
  required_date: string // ISO date
  destination_warehouse_id: string
  destination_warehouse_name: string
  summary_justification: string
  business_purpose: string | null
  priority_reason: string | null
  delivery_instructions: string | null
  status: PurchaseRequisitionStatus
  lines: PurchaseRequisitionLine[]
  revisions: PurchaseRequisitionRevision[]
  decisions: PurchaseRequisitionDecision[]
  capabilities: PurchaseRequisitionCapabilities
  created_at: string
  updated_at: string
}

export interface PurchaseRequisitionSummary {
  id: string
  requisition_code: string
  active_revision_number: number
  applicant_user_name: string
  cost_center_name: string
  priority: PurchaseRequisitionPriority
  required_date: string
  destination_warehouse_name: string
  lines_count: number
  products_summary: string
  status: PurchaseRequisitionStatus
  last_decision_summary: string | null
  submitted_at: string | null
  updated_at: string
}

export interface PurchaseRequisitionCreate {
  branch_id: string
  cost_center_id: string
  priority: PurchaseRequisitionPriority
  required_date: string
  destination_warehouse_id: string
  summary_justification: string
  business_purpose?: string
  priority_reason?: string
  delivery_instructions?: string
  lines: PurchaseRequisitionLineCreate[]
}

export interface PurchaseRequisitionUpdate {
  cost_center_id?: string
  priority?: PurchaseRequisitionPriority
  required_date?: string
  destination_warehouse_id?: string
  summary_justification?: string
  business_purpose?: string
  priority_reason?: string
  delivery_instructions?: string
  lines?: PurchaseRequisitionLineCreate[]
}

export interface PurchaseRequisitionListQuery {
  page?: number
  page_size?: number
  search?: string
  status?: PurchaseRequisitionStatus
  priority?: PurchaseRequisitionPriority
  cost_center_id?: string
  applicant_user_id?: string
  destination_warehouse_id?: string
  product_id?: string
  mine_only?: boolean
  pending_my_review?: boolean
  urgent_only?: boolean
}

export interface PurchaseRequisitionStats {
  total_requisitions: number
  draft_count: number
  submitted_count: number
  under_review_count: number
  approved_count: number
  rejected_count: number
  returned_count: number
  urgent_count: number
  pending_my_review_count: number
}
