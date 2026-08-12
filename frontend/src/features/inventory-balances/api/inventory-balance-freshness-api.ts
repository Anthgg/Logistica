import { apiRequest } from '../../../api/api-client'
import type { InventoryBalanceFreshness } from '../types/inventory-balances'

function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === '') continue
    if (value instanceof Date) {
      search.set(key, value.toISOString())
    } else if (typeof value === 'boolean') {
      search.set(key, String(value))
    } else {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export const inventoryBalanceFreshnessApi = {
  async getFreshness(
    organizationId: string,
    warehouseId?: string,
  ): Promise<InventoryBalanceFreshness[]> {
    return apiRequest<InventoryBalanceFreshness[]>({
      path: `/logistics/inventory/balances/freshness${buildQuery({
        organization_id: organizationId,
        warehouse_id: warehouseId,
      })}`,
      method: 'GET',
    })
  },

  async listProjectionCursors(
    organizationId: string,
  ): Promise<InventoryBalanceFreshness[]> {
    return apiRequest<InventoryBalanceFreshness[]>({
      path: `/logistics/inventory/balances/freshness/cursors${buildQuery({ organization_id: organizationId })}`,
      method: 'GET',
    })
  },
}
