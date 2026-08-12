import { apiRequest } from '../../../api/api-client'
import type { InventoryBalanceRebuildJob } from '../types/inventory-balances'

function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === '') continue
    if (typeof value === 'boolean') {
      search.set(key, String(value))
    } else {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export interface CreateRebuildRequest {
  organization_id: string
  rebuild_type: 'FULL' | 'PARTITION' | 'WAREHOUSE' | 'PRODUCT' | 'POSITION'
  scope: string
  checkpoint_id?: string
}

export const inventoryBalanceRebuildApi = {
  async createRebuild(
    request: CreateRebuildRequest,
  ): Promise<InventoryBalanceRebuildJob> {
    return apiRequest<InventoryBalanceRebuildJob>({
      path: '/logistics/inventory/balances/rebuilds',
      method: 'POST',
      body: request,
      requiresCsrf: true,
    })
  },

  async listRebuilds(
    organizationId: string,
    params?: Record<string, unknown>,
  ): Promise<{ items: InventoryBalanceRebuildJob[]; total: number }> {
    return apiRequest({
      path: `/logistics/inventory/balances/rebuilds${buildQuery({ organization_id: organizationId, ...params })}`,
      method: 'GET',
    })
  },

  async getRebuild(jobId: string): Promise<InventoryBalanceRebuildJob> {
    return apiRequest<InventoryBalanceRebuildJob>({
      path: `/logistics/inventory/balances/rebuilds/${jobId}`,
      method: 'GET',
    })
  },

  async cancelRebuild(jobId: string): Promise<void> {
    return apiRequest<void>({
      path: `/logistics/inventory/balances/rebuilds/${jobId}/cancel`,
      method: 'POST',
      requiresCsrf: true,
    })
  },

  async listRebuildDifferences(
    jobId: string,
  ): Promise<{ items: Record<string, unknown>[]; total: number }> {
    return apiRequest({
      path: `/logistics/inventory/balances/rebuilds/${jobId}/differences`,
      method: 'GET',
    })
  },
}
