import { apiRequest } from '../../../api/api-client'
import type { InventoryBalanceCheckpoint } from '../types/inventory-balances'

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

export const inventoryBalanceCheckpointsApi = {
  async listCheckpoints(
    organizationId: string,
    params?: Record<string, unknown>,
  ): Promise<{ items: InventoryBalanceCheckpoint[]; total: number }> {
    return apiRequest({
      path: `/logistics/inventory/balances/checkpoints${buildQuery({ organization_id: organizationId, ...params })}`,
      method: 'GET',
    })
  },

  async createCheckpoint(
    organizationId: string,
    partitionKey?: string,
  ): Promise<InventoryBalanceCheckpoint> {
    return apiRequest<InventoryBalanceCheckpoint>({
      path: '/logistics/inventory/balances/checkpoints',
      method: 'POST',
      body: { organization_id: organizationId, partition_key: partitionKey },
      requiresCsrf: true,
    })
  },

  async getCheckpoint(
    checkpointId: string,
  ): Promise<InventoryBalanceCheckpoint> {
    return apiRequest<InventoryBalanceCheckpoint>({
      path: `/logistics/inventory/balances/checkpoints/${checkpointId}`,
      method: 'GET',
    })
  },

  async getCheckpointIntegrity(
    checkpointId: string,
  ): Promise<{ valid: boolean; details: Record<string, unknown> }> {
    return apiRequest({
      path: `/logistics/inventory/balances/checkpoints/${checkpointId}/integrity`,
      method: 'GET',
    })
  },
}
