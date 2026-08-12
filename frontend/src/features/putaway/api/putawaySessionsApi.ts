import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/sessions'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const putawaySessionsApi = {
  /** POST /putaway/sessions/{session_id}/complete */
  async completeSession(sessionId: string, data: Record<string, unknown> = {}): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${sessionId}/complete`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /putaway/sessions/{session_id}/scans */
  async createScan(sessionId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${sessionId}/scans`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/sessions/{session_id}/scans */
  async listScans(sessionId: string): Promise<unknown[]> {
    return apiRequest({ path: `${BASE}/${sessionId}/scans`, method: 'GET' })
  },

  /** POST /putaway/sessions/{session_id}/scans/{event_id}/validate-product */
  async validateProduct(sessionId: string, eventId: string, data: Record<string, unknown> = {}): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${sessionId}/scans/${eventId}/validate-product`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /putaway/sessions/{session_id}/scans/{event_id}/validate-location */
  async validateLocation(sessionId: string, eventId: string, data: Record<string, unknown> = {}): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${sessionId}/scans/${eventId}/validate-location`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
