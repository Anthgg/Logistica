import { apiRequest } from '../../../api/api-client'
import type {
  InventoryBalanceReconciliationJob,
  InventoryBalanceReconciliationDifference,
} from '../types/inventory-balances'

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

export interface CreateReconciliationRequest {
  organization_id: string
  warehouse_id?: string
  product_id?: string
  partition_key?: string
  period_start?: string
  period_end?: string
}

export const inventoryBalanceReconciliationApi = {
  async createReconciliation(
    request: CreateReconciliationRequest,
  ): Promise<InventoryBalanceReconciliationJob> {
    return apiRequest<InventoryBalanceReconciliationJob>({
      path: '/logistics/inventory/balances/reconciliation',
      method: 'POST',
      body: request,
      requiresCsrf: true,
    })
  },

  async listReconciliations(
    organizationId: string,
    params?: Record<string, unknown>,
  ): Promise<{ items: InventoryBalanceReconciliationJob[]; total: number }> {
    return apiRequest({
      path: `/logistics/inventory/balances/reconciliation${buildQuery({ organization_id: organizationId, ...params })}`,
      method: 'GET',
    })
  },

  async getReconciliation(
    jobId: string,
  ): Promise<InventoryBalanceReconciliationJob> {
    return apiRequest<InventoryBalanceReconciliationJob>({
      path: `/logistics/inventory/balances/reconciliation/${jobId}`,
      method: 'GET',
    })
  },

  async listDifferences(
    jobId: string,
    params?: Record<string, unknown>,
  ): Promise<{ items: InventoryBalanceReconciliationDifference[]; total: number }> {
    return apiRequest({
      path: `/logistics/inventory/balances/reconciliation/${jobId}/differences${buildQuery(params ?? {})}`,
      method: 'GET',
    })
  },

  async requestRebuild(
    jobId: string,
    differenceId: string,
  ): Promise<void> {
    return apiRequest<void>({
      path: `/logistics/inventory/balances/reconciliation/${jobId}/differences/${differenceId}/rebuild`,
      method: 'POST',
      requiresCsrf: true,
    })
  },

  async reviewDifference(
    jobId: string,
    differenceId: string,
    notes: string,
  ): Promise<void> {
    return apiRequest<void>({
      path: `/logistics/inventory/balances/reconciliation/${jobId}/differences/${differenceId}/review`,
      method: 'POST',
      body: { notes },
      requiresCsrf: true,
    })
  },

  async resolveDifference(
    jobId: string,
    differenceId: string,
  ): Promise<void> {
    return apiRequest<void>({
      path: `/logistics/inventory/balances/reconciliation/${jobId}/differences/${differenceId}/resolve`,
      method: 'POST',
      requiresCsrf: true,
    })
  },
}
