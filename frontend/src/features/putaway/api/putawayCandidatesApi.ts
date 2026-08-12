import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/recommendations'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const putawayCandidatesApi = {
  /** POST /putaway/recommendations */
  async createRecommendations(data: Record<string, unknown>): Promise<{ run_id: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/recommendations/{run_id} */
  async getRecommendations(runId: string): Promise<unknown> {
    return apiRequest({ path: `${BASE}/${runId}`, method: 'GET' })
  },

  /** GET /putaway/recommendations/{run_id}/candidates */
  async getCandidates(runId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${runId}/candidates`, method: 'GET' })
  },

  /** GET /putaway/recommendations/{run_id}/best */
  async getBestCandidate(runId: string): Promise<unknown> {
    return apiRequest({ path: `${BASE}/${runId}/best`, method: 'GET' })
  },

  // Legacy helpers
  async getCandidatesForOrderLine(_orderId: string, _lineId: string): Promise<unknown> {
    return this.createRecommendations({ order_id: _orderId, line_id: _lineId })
  },
}
