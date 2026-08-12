import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceAcknowledgement,
  CreateAcknowledgementRequest,
  AcknowledgeCopyRequest,
  AcknowledgeFactsRequest,
  AcknowledgeResponsibilityAckRequest,
  DisputeFactsRequest,
  DisputeResponsibilityAckRequest,
  PaginatedResponse,
} from '../types/reception-differences'

const BASE = '/logistics/reception-difference-cases'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceAcknowledgementsApi = {
  // ── Acknowledgements (7) ──────────────────────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/acknowledgements */
  async list(caseId: string): Promise<PaginatedResponse<ReceptionDifferenceAcknowledgement>> {
    return apiRequest({ path: `${BASE}/${caseId}/acknowledgements`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/acknowledgements */
  async create(caseId: string, data: CreateAcknowledgementRequest): Promise<ReceptionDifferenceAcknowledgement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/acknowledgements`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/acknowledge-copy */
  async acknowledgeCopy(caseId: string, data?: AcknowledgeCopyRequest): Promise<ReceptionDifferenceAcknowledgement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/acknowledge-copy`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /reception-difference-cases/{case_id}/acknowledge-facts */
  async acknowledgeFacts(caseId: string, data?: AcknowledgeFactsRequest): Promise<ReceptionDifferenceAcknowledgement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/acknowledge-facts`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /reception-difference-cases/{case_id}/acknowledge-responsibility */
  async acknowledgeResponsibility(caseId: string, data?: AcknowledgeResponsibilityAckRequest): Promise<ReceptionDifferenceAcknowledgement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/acknowledge-responsibility`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /reception-difference-cases/{case_id}/dispute-facts */
  async disputeFacts(caseId: string, data: DisputeFactsRequest): Promise<ReceptionDifferenceAcknowledgement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/dispute-facts`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/dispute-responsibility */
  async disputeResponsibility(caseId: string, data: DisputeResponsibilityAckRequest): Promise<ReceptionDifferenceAcknowledgement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/dispute-responsibility`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
