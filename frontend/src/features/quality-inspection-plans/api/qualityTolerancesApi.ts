import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityTolerance,
  CreateQualityToleranceRequest,
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

export const qualityTolerancesApi = {
  /** GET /quality-inspection-plans/controls/{controlId}/tolerances */
  async list(controlId: string): Promise<QualityTolerance[]> {
    return apiRequest({ path: `${BASE}/controls/${controlId}/tolerances`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/controls/{controlId}/tolerances */
  async create(controlId: string, data: CreateQualityToleranceRequest): Promise<QualityTolerance> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/controls/${controlId}/tolerances`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /quality-inspection-plans/tolerances/{toleranceId} */
  async get(toleranceId: string): Promise<QualityTolerance> {
    return apiRequest({ path: `${BASE}/tolerances/${toleranceId}`, method: 'GET' })
  },

  /** PATCH /quality-inspection-plans/tolerances/{toleranceId} */
  async update(toleranceId: string, data: CreateQualityToleranceRequest): Promise<QualityTolerance> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/tolerances/${toleranceId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/tolerances/{toleranceId} */
  async delete(toleranceId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/tolerances/${toleranceId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
