import { apiRequest, getCsrfToken } from '../../../api/api-client'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export interface QualityNonConformityDocument {
  nc_id: string
  case_id: string
  nc_code: string
  status: 'DRAFT' | 'EMITTED' | 'DOWNLOADED' | 'REPRINTED' | 'CANCELLED'
  product_id: string
  product_name: string
  quantity: string
  unit_name: string
  inspection_id: string | null
  failed_controls: string[]
  measurements: string[]
  tolerances: string[]
  certificates: string[]
  evidence: string[]
  decision_type: string | null
  rejection_type: string | null
  hash: string | null
  created_at: string
  updated_at: string
}

export const qualityNonConformitiesApi = {
  /** GET /quality-non-conformities/preview?case_id={caseId} */
  async preview(caseId: string): Promise<QualityNonConformityDocument> {
    return apiRequest({ path: `/logistics/quality-non-conformities/preview?case_id=${caseId}`, method: 'GET' })
  },

  /** POST /quality-non-conformities/issue?case_id={caseId} */
  async issue(caseId: string): Promise<QualityNonConformityDocument> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-non-conformities/issue?case_id=${caseId}`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** GET /quality-non-conformities/{ncId} */
  async getDocument(ncId: string): Promise<QualityNonConformityDocument> {
    return apiRequest({ path: `/logistics/quality-non-conformities/${ncId}`, method: 'GET' })
  },

  /** POST /quality-non-conformities/{ncId}/reprint */
  async reprint(ncId: string): Promise<QualityNonConformityDocument> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-non-conformities/${ncId}/reprint`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-non-conformities/{ncId}/cancel */
  async cancel(ncId: string, data: { reason: string }): Promise<QualityNonConformityDocument> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-non-conformities/${ncId}/cancel`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
