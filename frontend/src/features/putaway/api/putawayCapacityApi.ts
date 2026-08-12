import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { LocationCapacity, WarehouseCapacitySummary } from '../types/putaway'

const BASE = '/logistics/putaway/capacity'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const putawayCapacityApi = {
  /** POST /putaway/capacity/profiles */
  async createProfile(data: Record<string, unknown>): Promise<LocationCapacity> {
    const csrf = await getCsrfToken().then((token) => ({ 'X-CSRF-Token': token }))
    return apiRequest({
      path: `${BASE}/profiles`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /putaway/capacity/profiles/{location_id} */
  async getProfile(locationId: string): Promise<LocationCapacity> {
    return apiRequest({ path: `${BASE}/profiles/${locationId}`, method: 'GET' })
  },

  /** GET /putaway/capacity/projections */
  async getProjections(warehouseId?: string): Promise<WarehouseCapacitySummary> {
    const qs = warehouseId ? `?warehouse_id=${warehouseId}` : ''
    return apiRequest({ path: `${BASE}/projections${qs}`, method: 'GET' })
  },
}
