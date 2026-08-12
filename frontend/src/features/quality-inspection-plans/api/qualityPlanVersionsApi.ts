import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityInspectionPlanVersion,
  CreateQualityPlanVersionRequest,
  ActivateQualityPlanVersionRequest,
  RetireQualityPlanVersionRequest,
} from '../types/quality-inspection-plans'

const BASE = '/logistics/quality-inspection-plans'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const qualityPlanVersionsApi = {
  /** GET /quality-inspection-plans/{planId}/versions */
  async list(planId: string): Promise<QualityInspectionPlanVersion[]> {
    return apiRequest({ path: `${BASE}/${planId}/versions`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/versions/{versionId} */
  async get(versionId: string): Promise<QualityInspectionPlanVersion> {
    return apiRequest({ path: `${BASE}/versions/${versionId}`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/{planId}/versions */
  async create(planId: string, data: CreateQualityPlanVersionRequest): Promise<QualityInspectionPlanVersion> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/versions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-plans/versions/{versionId}/activate */
  async activate(versionId: string, data: ActivateQualityPlanVersionRequest): Promise<QualityInspectionPlanVersion> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/versions/${versionId}/activate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-plans/versions/{versionId}/retire */
  async retire(versionId: string, data: RetireQualityPlanVersionRequest): Promise<QualityInspectionPlanVersion> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/versions/${versionId}/retire`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-plans/versions/{versionId}/hash */
  async hash(versionId: string): Promise<{ hash: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/versions/${versionId}/hash`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
