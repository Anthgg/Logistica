import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityControlDefinition,
  CreateQualityControlRequest,
  UpdateQualityControlRequest,
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

export const qualityControlsApi = {
  /** GET /quality-inspection-plans/{planId}/controls */
  async list(planId: string): Promise<QualityControlDefinition[]> {
    return apiRequest({ path: `${BASE}/${planId}/controls`, method: 'GET' })
  },

  /** GET /quality-inspection-plans/controls/{controlId} */
  async get(controlId: string): Promise<QualityControlDefinition> {
    return apiRequest({ path: `${BASE}/controls/${controlId}`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/{planId}/controls */
  async create(planId: string, data: CreateQualityControlRequest): Promise<QualityControlDefinition> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/controls`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** PATCH /quality-inspection-plans/controls/{controlId} */
  async update(controlId: string, data: UpdateQualityControlRequest): Promise<QualityControlDefinition> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/controls/${controlId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/controls/{controlId} */
  async delete(controlId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/controls/${controlId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
