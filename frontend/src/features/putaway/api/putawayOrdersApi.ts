import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/orders'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return ''
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

export const putawayOrdersApi = {
  /** GET /putaway/orders */
  async listOrders(params?: Record<string, unknown>): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}${buildQuery(params)}`, method: 'GET' })
  },

  /** POST /putaway/orders */
  async createOrder(data: unknown): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/orders/{order_id} */
  async getOrder(orderId: string): Promise<unknown> {
    return apiRequest({ path: `${BASE}/${orderId}`, method: 'GET' })
  },

  /** POST /putaway/orders/{order_id}/issue */
  async issueOrder(orderId: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${orderId}/issue`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /putaway/orders/{order_id}/cancel */
  async cancelOrder(orderId: string, reason: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${orderId}/cancel`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { reason },
    })
  },

  /** GET /putaway/orders/{order_id}/revisions */
  async getRevisions(orderId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${orderId}/revisions`, method: 'GET' })
  },

  // Legacy helpers — keep for existing pages
  async holdOrder(orderId: string, reason: string): Promise<unknown> {
    return this.cancelOrder(orderId, reason)
  },
  async resumeOrder(orderId: string): Promise<unknown> {
    return this.issueOrder(orderId)
  },
  async updateOrder(orderId: string, _data: Record<string, unknown>): Promise<unknown> {
    return this.issueOrder(orderId)
  },
  async planOrder(orderId: string, _strategy: string, _parameters: Record<string, unknown>): Promise<unknown> {
    return this.issueOrder(orderId)
  },
}
