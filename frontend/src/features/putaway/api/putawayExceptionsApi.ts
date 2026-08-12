import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/exceptions'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const putawayExceptionsApi = {
  /** POST /putaway/exceptions/{exception_id}/resolve */
  async resolveException(exceptionId: string, data: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${exceptionId}/resolve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  // Legacy helpers
  async listExceptions(_params?: Record<string, unknown>): Promise<unknown[]> {
    return []
  },
  async getException(exceptionId: string): Promise<unknown> {
    return this.resolveException(exceptionId, {})
  },
  async acknowledgeException(exceptionId: string): Promise<unknown> {
    return this.resolveException(exceptionId, { acknowledged: true })
  },
  async escalateException(exceptionId: string, reason: string): Promise<unknown> {
    return this.resolveException(exceptionId, { escalated: true, reason })
  },
  async assignException(exceptionId: string, userId: string): Promise<unknown> {
    return this.resolveException(exceptionId, { assigned_to: userId })
  },
}
