import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceItem,
  ReceptionDifferenceEvidence,
  CreateManualDifferenceItemRequest,
  UpdateReceptionDifferenceItemRequest,
  DismissItemRequest,
  SupersedeItemRequest,
  LinkEvidenceToItemRequest,
  PaginatedResponse,
} from '../types/reception-differences'

const CASES_BASE = '/logistics/reception-difference-cases'
const ITEMS_BASE = '/logistics/reception-difference-items'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceItemsApi = {
  // ── Items (10) ────────────────────────────────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/items */
  async list(caseId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<ReceptionDifferenceItem>> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/items?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/items */
  async create(caseId: string, data: CreateManualDifferenceItemRequest): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/items`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /reception-difference-items/{item_id} */
  async get(itemId: string): Promise<ReceptionDifferenceItem> {
    return apiRequest({ path: `${ITEMS_BASE}/${itemId}`, method: 'GET' })
  },

  /** PATCH /reception-difference-items/{item_id} */
  async update(itemId: string, data: UpdateReceptionDifferenceItemRequest): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${ITEMS_BASE}/${itemId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-items/{item_id}/validate */
  async validate(itemId: string): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${ITEMS_BASE}/${itemId}/validate`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },

  /** POST /reception-difference-items/{item_id}/dismiss */
  async dismiss(itemId: string, data: DismissItemRequest): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${ITEMS_BASE}/${itemId}/dismiss`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-items/{item_id}/mark-follow-up-required */
  async markFollowUpRequired(itemId: string, recommendation: string): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${ITEMS_BASE}/${itemId}/mark-follow-up-required`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { recommendation },
    })
  },

  /** POST /reception-difference-items/{item_id}/supersede */
  async supersede(itemId: string, data: SupersedeItemRequest): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${ITEMS_BASE}/${itemId}/supersede`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-items/{item_id}/evidence-links */
  async linkEvidence(itemId: string, data: LinkEvidenceToItemRequest): Promise<ReceptionDifferenceEvidence> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${ITEMS_BASE}/${itemId}/evidence-links`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /reception-difference-items/{item_id}/evidence */
  async listEvidence(itemId: string): Promise<ReceptionDifferenceEvidence[]> {
    return apiRequest({ path: `${ITEMS_BASE}/${itemId}/evidence`, method: 'GET' })
  },
}
