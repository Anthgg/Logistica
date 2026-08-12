import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/putaway/overrides'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const putawayOverridesApi = {
  /** POST /putaway/overrides/{override_id}/approve */
  async approveOverride(overrideId: string, data: Record<string, unknown> = {}): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${overrideId}/approve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
