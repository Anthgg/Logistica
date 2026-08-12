import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityInspectionPlan,
  QualityPlanListQuery,
  CreateQualityInspectionPlanRequest,
  UpdateQualityInspectionPlanRequest,
  PaginatedResponse,
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

function buildQuery(params: Record<string, unknown>): string {
  const entries: [string, string][] = []
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue
    if (Array.isArray(v)) {
      for (const item of v) entries.push([k, String(item)])
    } else {
      entries.push([k, String(v)])
    }
  }
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : ''
}

export const qualityInspectionPlansApi = {
  /** GET /quality-inspection-plans */
  async list(query: QualityPlanListQuery = {}): Promise<PaginatedResponse<QualityInspectionPlan>> {
    return apiRequest({ path: `${BASE}${buildQuery(query as Record<string, unknown>)}`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/{planId} */
  async get(planId: string): Promise<QualityInspectionPlan> {
    return apiRequest({ path: `${BASE}/${planId}`, method: 'GET' })
  },

  /** POST /quality-inspection-plans */
  async create(data: CreateQualityInspectionPlanRequest): Promise<QualityInspectionPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** PATCH /quality-inspection-plans/{planId} */
  async update(planId: string, data: UpdateQualityInspectionPlanRequest): Promise<QualityInspectionPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/{planId} */
  async delete(planId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },

  /** POST /quality-inspection-plans/{planId}/activate */
  async activate(planId: string): Promise<QualityInspectionPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/activate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-inspection-plans/{planId}/deactivate */
  async deactivate(planId: string): Promise<QualityInspectionPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/deactivate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-inspection-plans/{planId}/archive */
  async archive(planId: string): Promise<QualityInspectionPlan> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/archive`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
