import { apiRequest } from '../../../api/api-client'
import type {
  ApprovalAssignmentSummary,
  ApprovalAuditSealSummary,
  ApprovalDecisionRecord,
  ApprovalPolicyConditionCreate,
  ApprovalPolicyCreate,
  ApprovalPolicyStepCreate,
  ApprovalSubmitRequest,
  ProcurementApprovalPolicy,
  ProcurementApprovalRequest,
} from '../types/phase035-contract'

const BASE = '/logistics/procurement-approvals'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function readString(
  source: Record<string, unknown> | null,
  ...keys: string[]
): string | null {
  if (!source) return null
  for (const key of keys) {
    const value = source[key]
    if (typeof value === 'string' && value.trim()) return value
  }
  return null
}

function readNumber(
  source: Record<string, unknown> | null,
  ...keys: string[]
): number | null {
  if (!source) return null
  for (const key of keys) {
    const value = source[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
  }
  return null
}

function readBoolean(
  source: Record<string, unknown> | null,
  ...keys: string[]
): boolean {
  if (!source) return false
  return keys.some((key) => source[key] === true)
}

function asRecordArray(payload: unknown): Array<Record<string, unknown>> {
  if (Array.isArray(payload)) return payload.filter(isRecord)
  if (!isRecord(payload)) return []
  const items = payload.items ?? payload.assignments ?? payload.results
  return Array.isArray(items) ? items.filter(isRecord) : []
}

export function parseApprovalAssignments(
  payload: unknown,
): ApprovalAssignmentSummary[] {
  return asRecordArray(payload).flatMap((item) => {
    const request = isRecord(item.request) ? item.request : null
    const step = isRecord(item.step) ? item.step : null
    const id = readString(item, 'id', 'assignment_id')
    if (!id) return []

    return [
      {
        id,
        request_id:
          readString(item, 'request_id', 'approval_request_id') ??
          readString(request, 'id'),
        request_code:
          readString(item, 'request_code') ??
          readString(request, 'request_code'),
        subject_type:
          readString(item, 'subject_type') ??
          readString(request, 'subject_type'),
        subject_id:
          readString(item, 'subject_id') ??
          readString(request, 'subject_id'),
        subject_code:
          readString(item, 'subject_code') ??
          readString(request, 'subject_code'),
        status: readString(item, 'status', 'assignment_status'),
        step_name:
          readString(item, 'step_name') ?? readString(step, 'name'),
        step_sequence:
          readNumber(item, 'step_sequence', 'sequence') ??
          readNumber(step, 'sequence', 'order_index'),
        due_at: readString(item, 'due_at', 'deadline_at', 'expires_at'),
        amount:
          readString(item, 'amount') ?? readString(request, 'amount'),
        currency_code:
          readString(item, 'currency_code') ??
          readString(request, 'currency_code'),
        delegated: readBoolean(item, 'delegated', 'is_delegated'),
      },
    ]
  })
}

export function parseApprovalAuditSeal(
  payload: unknown,
): ApprovalAuditSealSummary {
  const source = isRecord(payload) ? payload : null
  return {
    id: readString(source, 'id', 'seal_id'),
    status: readString(source, 'status', 'integrity_status'),
    algorithm: readString(source, 'algorithm', 'signature_algorithm'),
    key_id: readString(source, 'key_id', 'kms_key_id'),
    created_at: readString(source, 'created_at', 'sealed_at'),
    verified_at: readString(source, 'verified_at'),
    verification_status: readString(
      source,
      'verification_status',
      'verification_result',
    ),
  }
}

function userQuery(userId: string): string {
  return `user_id=${encodeURIComponent(userId)}`
}

export const procurementApprovalsApi = {
  async listPolicies(
    organizationId: string,
    subjectType?: string,
  ): Promise<ProcurementApprovalPolicy[]> {
    const params = new URLSearchParams({ organization_id: organizationId })
    if (subjectType) params.set('subject_type', subjectType)
    return apiRequest({
      path: `${BASE}/policies?${params.toString()}`,
    })
  },

  async createPolicy(
    userId: string,
    payload: ApprovalPolicyCreate,
  ): Promise<ProcurementApprovalPolicy> {
    return apiRequest({
      path: `${BASE}/policies?${userQuery(userId)}`,
      method: 'POST',
      body: payload,
    })
  },

  async getPolicy(policyId: string): Promise<ProcurementApprovalPolicy> {
    return apiRequest({ path: `${BASE}/policies/${policyId}` })
  },

  async addCondition(
    versionId: string,
    payload: ApprovalPolicyConditionCreate,
  ): Promise<void> {
    await apiRequest({
      path: `${BASE}/policy-versions/${versionId}/conditions`,
      method: 'POST',
      body: payload,
    })
  },

  async addStep(
    versionId: string,
    payload: ApprovalPolicyStepCreate,
  ): Promise<void> {
    await apiRequest({
      path: `${BASE}/policy-versions/${versionId}/steps`,
      method: 'POST',
      body: payload,
    })
  },

  async activateVersion(
    versionId: string,
    userId: string,
  ): Promise<void> {
    await apiRequest({
      path: `${BASE}/policy-versions/${versionId}/activate?${userQuery(userId)}`,
      method: 'POST',
    })
  },

  async submitRequest(
    userId: string,
    payload: ApprovalSubmitRequest,
  ): Promise<ProcurementApprovalRequest> {
    return apiRequest({
      path: `${BASE}/requests?${userQuery(userId)}`,
      method: 'POST',
      body: payload,
    })
  },

  async getRequest(
    requestId: string,
  ): Promise<ProcurementApprovalRequest> {
    return apiRequest({ path: `${BASE}/requests/${requestId}` })
  },

  async listMyPendingAssignments(
    userId: string,
  ): Promise<ApprovalAssignmentSummary[]> {
    const payload = await apiRequest<unknown>({
      path: `${BASE}/assignments/my-pending?${userQuery(userId)}`,
    })
    return parseApprovalAssignments(payload)
  },

  async recordDecision(
    assignmentId: string,
    userId: string,
    payload: ApprovalDecisionRecord,
  ): Promise<void> {
    await apiRequest({
      path: `${BASE}/assignments/${assignmentId}/decision?${userQuery(userId)}`,
      method: 'POST',
      body: payload,
    })
  },

  async getAuditSeal(
    requestId: string,
  ): Promise<ApprovalAuditSealSummary> {
    const payload = await apiRequest<unknown>({
      path: `${BASE}/requests/${requestId}/audit-seal`,
    })
    return parseApprovalAuditSeal(payload)
  },
}
