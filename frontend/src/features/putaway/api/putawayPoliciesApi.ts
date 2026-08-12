import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/policies'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const putawayPoliciesApi = {
  /** GET /putaway/policies */
  async listPolicies(warehouseId?: string): Promise<unknown[]> {
    const qs = warehouseId ? `?warehouse_id=${warehouseId}` : ''
    return apiRequest({ path: `${BASE}${qs}`, method: 'GET' })
  },

  /** POST /putaway/policies */
  async createPolicy(data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /putaway/policies/{policy_id}/activate */
  async activatePolicy(policyId: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${policyId}/activate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** GET /putaway/policies/{policy_id}/versions */
  async getVersions(policyId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${policyId}/versions`, method: 'GET' })
  },

  /** POST /putaway/policies/{policy_id}/versions */
  async createVersion(policyId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${policyId}/versions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /putaway/policies/versions/{version_id}/activate */
  async activateVersion(versionId: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/versions/${versionId}/activate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
