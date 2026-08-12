export interface ProcurementApprovalPolicy {
  id: string
  organization_id: string
  code: string
  normalized_code: string
  name: string
  description: string | null
  subject_type: string
  priority: number
  status: string
  active_version_id: string | null
  effective_scope: string
  is_fallback: boolean
  created_at: string
  updated_at: string
}

export interface ApprovalPolicyCreate {
  organization_id: string
  code: string
  name: string
  subject_type: string
  description?: string | null
  priority?: number
  effective_scope?: string
  is_fallback?: boolean
}

export interface ApprovalPolicyConditionCreate {
  condition_group?: string
  field_code: string
  operator: string
  value_data: Record<string, unknown>
  order_index?: number
}

export interface ApprovalPolicyStepCreate {
  step_code: string
  name: string
  order_index?: number
  execution_mode?: string
  completion_mode?: string
  minimum_approvals?: number
  required_approvals?: number
  approver_source_type: string
  approver_source_config: Record<string, unknown>
  step_up_level?: string
  distinct_from_creator?: boolean
}

export interface ApprovalSubmitRequest {
  organization_id: string
  subject_type: string
  subject_id: string
  subject_revision_id?: string | null
  subject_code?: string | null
  subject_snapshot: Record<string, unknown>
  amount: string
  currency_code: string
  creator_user_id: string
  requester_user_id: string
  cost_center_snapshot?: Record<string, unknown> | null
  category_snapshots?: Array<Record<string, unknown>> | null
  branch_snapshot?: Record<string, unknown> | null
}

export interface ProcurementApprovalRequest {
  id: string
  organization_id: string
  request_code: string
  subject_type: string
  subject_id: string
  subject_revision_id: string | null
  subject_code: string | null
  status: string
  current_sequence: number
  amount: string
  currency_code: string
  submitted_at: string
  completed_at: string | null
  final_decision: string | null
  audit_seal_id: string | null
}

export type ApprovalDecisionType = 'APPROVE' | 'REJECT' | 'RETURN'

export interface ApprovalDecisionRecord {
  decision_type: ApprovalDecisionType
  reason?: string | null
  conditions?: Record<string, unknown> | null
  step_up_assurance_level?: string
}

/**
 * El OpenAPI 0.9.1 no define un schema para la bandeja. Solo se exponen los
 * campos seguros que el parser puede reconocer; el payload completo no se
 * conserva ni se muestra.
 */
export interface ApprovalAssignmentSummary {
  id: string
  request_id: string | null
  request_code: string | null
  subject_type: string | null
  subject_id: string | null
  subject_code: string | null
  status: string | null
  step_name: string | null
  step_sequence: number | null
  due_at: string | null
  amount: string | null
  currency_code: string | null
  delegated: boolean
}

export interface ApprovalAuditSealSummary {
  id: string | null
  status: string | null
  algorithm: string | null
  key_id: string | null
  created_at: string | null
  verified_at: string | null
  verification_status: string | null
}

export interface Phase035BackendSupport {
  dashboard_counts: false
  inbox: true
  created_by_me: false
  request_detail: true
  request_history: false
  request_capabilities: false
  policies_list: true
  policies_create: true
  policies_detail: true
  policy_update: false
  policy_versions_list: false
  policy_version_create: false
  policy_condition_create: true
  policy_step_create: true
  policy_version_activate: true
  policy_validate: false
  policy_simulate: false
  assignments_decide: true
  information_requests: false
  delegations: false
  audit_seal_read: true
  audit_seal_verify: false
}

export const PHASE_035_BACKEND_SUPPORT: Phase035BackendSupport = {
  dashboard_counts: false,
  inbox: true,
  created_by_me: false,
  request_detail: true,
  request_history: false,
  request_capabilities: false,
  policies_list: true,
  policies_create: true,
  policies_detail: true,
  policy_update: false,
  policy_versions_list: false,
  policy_version_create: false,
  policy_condition_create: true,
  policy_step_create: true,
  policy_version_activate: true,
  policy_validate: false,
  policy_simulate: false,
  assignments_decide: true,
  information_requests: false,
  delegations: false,
  audit_seal_read: true,
  audit_seal_verify: false,
}
