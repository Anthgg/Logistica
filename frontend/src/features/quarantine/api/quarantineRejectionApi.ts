import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QuarantineRejectionAuthorization,
  RequestQuarantineRejectionRequest,
} from '../types/quarantine'

const BASE = '/logistics/quarantine-rejection-authorizations'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function buildQuery(params: Record<string, unknown>): string {
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

export const quarantineRejectionApi = {
  /** GET /quarantine-rejection-authorizations */
  async list(query?: Record<string, unknown>): Promise<QuarantineRejectionAuthorization[]> {
    return apiRequest({ path: `${BASE}${query ? buildQuery(query) : ''}`, method: 'GET' })
  },

  /** GET /quarantine-rejection-authorizations/{authorizationId} */
  async get(authorizationId: string): Promise<QuarantineRejectionAuthorization> {
    return apiRequest({ path: `${BASE}/${authorizationId}`, method: 'GET' })
  },

  /** POST /quarantine-rejection-authorizations */
  async create(data: RequestQuarantineRejectionRequest): Promise<QuarantineRejectionAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-quarantine-cases/{caseId}/rejection-authorizations */
  async createAuthorization(caseId: string, data: RequestQuarantineRejectionRequest): Promise<QuarantineRejectionAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-quarantine-cases/${caseId}/rejection-authorizations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quarantine-rejection-authorizations/{rejectionId}/approve */
  async approveAuthorization(rejectionId: string, data?: { decision?: string; comments?: string }): Promise<QuarantineRejectionAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${rejectionId}/approve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /quarantine-rejection-authorizations/{rejectionId}/execute */
  async execute(rejectionId: string): Promise<QuarantineRejectionAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${rejectionId}/execute`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** Alias executeRejection to execute */
  async executeRejection(rejectionId: string): Promise<QuarantineRejectionAuthorization> {
    return this.execute(rejectionId)
  },
}
