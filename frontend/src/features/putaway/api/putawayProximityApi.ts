import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { ProximityMatrix } from '../types/putaway'

const BASE = '/logistics/putaway/proximity'

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

export const putawayProximityApi = {
  /** GET /putaway/proximity/profiles */
  async getProfiles(warehouseId?: string): Promise<ProximityMatrix> {
    return apiRequest({ path: `${BASE}/profiles${buildQuery({ warehouse_id: warehouseId })}`, method: 'GET' })
  },

  /** POST /putaway/proximity/profiles */
  async createProfile(data: Record<string, unknown>): Promise<ProximityMatrix> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/profiles`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/proximity/distance */
  async getDistance(fromLocationId: string, toLocationId: string): Promise<{ distance_meters: { value: string; scale: number } }> {
    return apiRequest({ path: `${BASE}/distance${buildQuery({ from: fromLocationId, to: toLocationId })}`, method: 'GET' })
  },

  /** GET /putaway/proximity/travel-cost */
  async getTravelCost(fromLocationId: string, toLocationId: string): Promise<{ walk_time_seconds: number }> {
    return apiRequest({ path: `${BASE}/travel-cost${buildQuery({ from: fromLocationId, to: toLocationId })}`, method: 'GET' })
  },

  // Legacy helper
  async getNearbyDestinations(_warehouseId: string, _sourceLocationId: string, _limit?: number): Promise<unknown[]> {
    return []
  },
}
