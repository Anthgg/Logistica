import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityCertificateRequirement,
  CreateQualityCertificateRequirementRequest,
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

export const qualityCertificateRequirementsApi = {
  /** GET /quality-inspection-plans/controls/{controlId}/certificates */
  async list(controlId: string): Promise<QualityCertificateRequirement[]> {
    return apiRequest({ path: `${BASE}/controls/${controlId}/certificates`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/controls/{controlId}/certificates */
  async create(controlId: string, data: CreateQualityCertificateRequirementRequest): Promise<QualityCertificateRequirement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/controls/${controlId}/certificates`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** PATCH /quality-inspection-plans/certificates/{certificateId} */
  async update(certificateId: string, data: CreateQualityCertificateRequirementRequest): Promise<QualityCertificateRequirement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/certificates/${certificateId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/certificates/{certificateId} */
  async delete(certificateId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/certificates/${certificateId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
