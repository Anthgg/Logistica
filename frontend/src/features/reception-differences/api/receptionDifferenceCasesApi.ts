import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceCase,
  ReceptionDifferenceCaseDetail,
  ReceptionDifferenceCaseCapabilities,
  ReceptionDifferenceCaseQuery,
  ReceptionDifferenceHistoryEvent,
  ReceptionDifferenceIntegrity,
  ReceptionDifferenceValidation,
  CreateReceptionDifferenceCaseRequest,
  UpdateReceptionDifferenceCaseRequest,
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

function buildQuery(params: Record<string, any> = {}): string {
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

export const receptionDifferenceCasesApi = {
  // ── Cases (16) ────────────────────────────────────────────────────────────────

  /** GET /reception-difference-cases */
  async list(query: ReceptionDifferenceCaseQuery = {}): Promise<PaginatedResponse<ReceptionDifferenceCase>> {
    return apiRequest({ path: `${BASE}${buildQuery(query)}`, method: 'GET' })
  },

  /** POST /reception-difference-cases */
  async create(data: CreateReceptionDifferenceCaseRequest): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/from-receipt */
  async createFromReceipt(data: { receipt_id: string; candidate_ids?: string[] }): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/from-receipt`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /reception-difference-cases/{case_id} */
  async get(caseId: string): Promise<ReceptionDifferenceCaseDetail> {
    return apiRequest({ path: `${BASE}/${caseId}`, method: 'GET' })
  },

  /** PATCH /reception-difference-cases/{case_id} */
  async update(caseId: string, data: UpdateReceptionDifferenceCaseRequest): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}`,
      method: 'PATCH',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/validate */
  async validate(caseId: string): Promise<ReceptionDifferenceValidation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/validate`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },

  /** POST /reception-difference-cases/{case_id}/submit */
  async submit(caseId: string): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/submit`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { confirmation: true },
    })
  },

  /** POST /reception-difference-cases/{case_id}/start-review */
  async startReview(caseId: string): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/start-review`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /reception-difference-cases/{case_id}/request-changes */
  async requestChanges(caseId: string, data: { reason: string; sections?: string[]; items_affected?: string[]; evidence_missing?: string[]; responsible_missing?: boolean }): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/request-changes`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/mark-ready-for-approval */
  async markReadyForApproval(caseId: string): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/mark-ready-for-approval`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /reception-difference-cases/{case_id}/approve */
  async approve(caseId: string, data: { decision: string; comments?: string }): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/approve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/cancel */
  async cancel(caseId: string, reason: string): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/cancel`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { reason },
    })
  },

  /** POST /reception-difference-cases/{case_id}/close */
  async close(caseId: string): Promise<ReceptionDifferenceCase> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/close`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** GET /reception-difference-cases/{case_id}/history */
  async getHistory(caseId: string): Promise<ReceptionDifferenceHistoryEvent[]> {
    return apiRequest({ path: `${BASE}/${caseId}/history`, method: 'GET' })
  },

  /** GET /reception-difference-cases/{case_id}/capabilities */
  async getCapabilities(caseId: string): Promise<ReceptionDifferenceCaseCapabilities> {
    return apiRequest({ path: `${BASE}/${caseId}/capabilities`, method: 'GET' })
  },

  /** GET /reception-difference-cases/{case_id}/integrity */
  async getIntegrity(caseId: string): Promise<ReceptionDifferenceIntegrity> {
    return apiRequest({ path: `${BASE}/${caseId}/integrity`, method: 'GET' })
  },
}
