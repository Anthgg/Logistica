import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QuarantineReleaseAuthorization,
  RequestQuarantineReleaseRequest,
} from '../types/quarantine'

const BASE = '/logistics/quarantine-release-authorizations'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const quarantineReleaseApi = {
  /** POST /quality-quarantine-cases/{caseId}/release-authorizations */
  async createAuthorization(caseId: string, data: RequestQuarantineReleaseRequest): Promise<QuarantineReleaseAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-quarantine-cases/${caseId}/release-authorizations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quarantine-release-authorizations/{releaseId}/approve */
  async approveAuthorization(releaseId: string, data?: { decision?: string; comments?: string }): Promise<QuarantineReleaseAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${releaseId}/approve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /quarantine-release-authorizations/{releaseId}/execute */
  async execute(releaseId: string): Promise<QuarantineReleaseAuthorization> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${releaseId}/execute`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** Alias executeRelease to execute */
  async executeRelease(releaseId: string): Promise<QuarantineReleaseAuthorization> {
    return this.execute(releaseId)
  },
}
