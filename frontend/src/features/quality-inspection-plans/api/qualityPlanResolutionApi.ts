import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityPlanConflict,
  QualityPlanValidation,
  QualityPlanIntegrity,
  QualityPlanPreview,
  QualityPlanPreviewRequest,
  FutureQualityInspectionTemplate,
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

export const qualityPlanAnalyticsApi = {
  /** GET /quality-inspection-plans/conflicts */
  async getConflicts(query?: Record<string, unknown>): Promise<QualityPlanConflict[]> {
    return apiRequest({ path: `${BASE}/conflicts${query ? buildQuery(query) : ''}`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/resolve */
  async resolve(query: Record<string, unknown>): Promise<unknown> {
    return apiRequest({ path: `${BASE}/resolve${buildQuery(query)}`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/validate */
  async validate(query: Record<string, unknown>): Promise<QualityPlanValidation> {
    return apiRequest({ path: `${BASE}/validate${buildQuery(query)}`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/{planId}/snapshot */
  async getSnapshot(planId: string): Promise<unknown> {
    return apiRequest({ path: `${BASE}/${planId}/snapshot`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/{planId}/integrity */
  async getIntegrity(planId: string): Promise<QualityPlanIntegrity> {
    return apiRequest({ path: `${BASE}/${planId}/integrity`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/{planId}/metrics */
  async getMetrics(planId: string): Promise<unknown> {
    return apiRequest({ path: `${BASE}/${planId}/metrics`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/{planId}/metrics/recalculate */
  async recalculateMetrics(planId: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/metrics/recalculate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-inspection-plans/future-template-preview */
  async futureTemplatePreview(data: QualityPlanPreviewRequest): Promise<FutureQualityInspectionTemplate> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/future-template-preview`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-plans/{planId}/preview */
  async preview(planId: string, data: QualityPlanPreviewRequest): Promise<QualityPlanPreview> {
    return apiRequest({
      path: `${BASE}/${planId}/preview`,
      method: 'POST',
      body: data,
    })
  },
}
