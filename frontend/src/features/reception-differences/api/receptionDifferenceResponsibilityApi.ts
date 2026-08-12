import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceResponsibleParty,
  CreateResponsiblePartyRequest,
  UpdateResponsiblePartyRequest,
  PaginatedResponse,
} from '../types/reception-differences'

const CASES_BASE = '/logistics/reception-difference-cases'
const PARTIES_BASE = '/logistics/reception-difference-responsible-parties'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceResponsibilityApi = {
  // ── Responsibility (7) ────────────────────────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/responsible-parties */
  async list(caseId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<ReceptionDifferenceResponsibleParty>> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/responsible-parties?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/responsible-parties */
  async create(caseId: string, data: CreateResponsiblePartyRequest): Promise<ReceptionDifferenceResponsibleParty> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/responsible-parties`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** PATCH /reception-difference-responsible-parties/{responsibility_id} */
  async update(responsibilityId: string, data: UpdateResponsiblePartyRequest): Promise<ReceptionDifferenceResponsibleParty> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${PARTIES_BASE}/${responsibilityId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-responsible-parties/{responsibility_id}/review */
  async review(responsibilityId: string, data: { approved: boolean; comments?: string }): Promise<ReceptionDifferenceResponsibleParty> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${PARTIES_BASE}/${responsibilityId}/review`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-responsible-parties/{responsibility_id}/acknowledge */
  async acknowledge(responsibilityId: string, data?: { comment?: string }): Promise<ReceptionDifferenceResponsibleParty> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${PARTIES_BASE}/${responsibilityId}/acknowledge`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /reception-difference-responsible-parties/{responsibility_id}/dispute */
  async dispute(responsibilityId: string, data: { reason: string; dispute_type?: 'FACTS' | 'RESPONSIBILITY' | string; evidence_file_ids?: string[] }): Promise<ReceptionDifferenceResponsibleParty> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${PARTIES_BASE}/${responsibilityId}/dispute`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-responsible-parties/{responsibility_id}/supersede */
  async supersede(responsibilityId: string, data: CreateResponsiblePartyRequest): Promise<ReceptionDifferenceResponsibleParty> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${PARTIES_BASE}/${responsibilityId}/supersede`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
