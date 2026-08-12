import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityPlanScope,
  CreateQualityPlanScopeRequest,
  UpdateQualityPlanScopeRequest,
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

export const qualityPlanScopesApi = {
  /** GET /quality-inspection-plans/{planId}/scopes */
  async list(planId: string): Promise<QualityPlanScope[]> {
    return apiRequest({ path: `${BASE}/${planId}/scopes`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/{planId}/scopes */
  async create(planId: string, data: CreateQualityPlanScopeRequest): Promise<QualityPlanScope> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/scopes`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /quality-inspection-plans/scopes/{scopeId} */
  async get(scopeId: string): Promise<QualityPlanScope> {
    return apiRequest({ path: `${BASE}/scopes/${scopeId}`, method: 'GET' })
  },

  /** PATCH /quality-inspection-plans/scopes/{scopeId} */
  async update(scopeId: string, data: UpdateQualityPlanScopeRequest): Promise<QualityPlanScope> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/scopes/${scopeId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/scopes/{scopeId} */
  async delete(scopeId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/scopes/${scopeId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
