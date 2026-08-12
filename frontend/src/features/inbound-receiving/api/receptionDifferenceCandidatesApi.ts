import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceCandidate,
  DismissCandidateRequest,
  PaginatedResponse,
} from '../types/inbound-receiving'

const BASE = '/logistics/inbound-receipts'

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const receptionDifferenceCandidatesApi = {
  async list(receiptId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<ReceptionDifferenceCandidate>> {
    return apiRequest({ path: `${BASE}/${receiptId}/difference-candidates?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  async get(receiptId: string, candidateId: string): Promise<ReceptionDifferenceCandidate> {
    return apiRequest({ path: `${BASE}/${receiptId}/difference-candidates/${candidateId}`, method: 'GET' })
  },

  async acknowledge(receiptId: string, candidateId: string): Promise<ReceptionDifferenceCandidate> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/difference-candidates/${candidateId}/acknowledge`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  async dismiss(receiptId: string, candidateId: string, data: DismissCandidateRequest): Promise<ReceptionDifferenceCandidate> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/difference-candidates/${candidateId}/dismiss`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
