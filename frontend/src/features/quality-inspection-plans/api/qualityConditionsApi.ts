import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { QualityControlCondition } from '../types/quality-inspection-plans'

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

export interface CreateQualityConditionRequest {
  condition_field: string
  operator: string
  value?: string
  display_order?: number
  group_index?: number
}

export interface UpdateQualityConditionRequest {
  condition_field?: string
  operator?: string
  value?: string | null
  display_order?: number
  group_index?: number | null
}

export const qualityConditionsApi = {
  /** GET /quality-inspection-plans/controls/{controlId}/conditions */
  async list(controlId: string): Promise<QualityControlCondition[]> {
    return apiRequest({ path: `${BASE}/controls/${controlId}/conditions`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/controls/{controlId}/conditions */
  async create(controlId: string, data: CreateQualityConditionRequest): Promise<QualityControlCondition> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/controls/${controlId}/conditions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** PATCH /quality-inspection-plans/conditions/{conditionId} */
  async update(conditionId: string, data: UpdateQualityConditionRequest): Promise<QualityControlCondition> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/conditions/${conditionId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/conditions/{conditionId} */
  async delete(conditionId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/conditions/${conditionId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
