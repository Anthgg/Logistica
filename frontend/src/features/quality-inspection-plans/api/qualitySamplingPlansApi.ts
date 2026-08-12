import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualitySamplingPlan,
  CreateQualitySamplingPlanRequest,
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

export const qualitySamplingPlansApi = {
  /** GET /quality-inspection-plans/controls/{controlId}/samplings */
  async list(controlId: string): Promise<QualitySamplingPlan[]> {
    return apiRequest({ path: `${BASE}/controls/${controlId}/samplings`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/controls/{controlId}/samplings */
  async create(controlId: string, data: CreateQualitySamplingPlanRequest): Promise<QualitySamplingPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/controls/${controlId}/samplings`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** PATCH /quality-inspection-plans/samplings/{samplingId} */
  async update(samplingId: string, data: CreateQualitySamplingPlanRequest): Promise<QualitySamplingPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/samplings/${samplingId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/samplings/{samplingId} */
  async delete(samplingId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/samplings/${samplingId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
