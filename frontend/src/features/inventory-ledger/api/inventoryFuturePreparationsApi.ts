import { apiRequest } from '../../../api/api-client'
import type {
  InventoryBalancePreparationRow,
  InventoryTraceabilityPreparationRow,
} from '../types/inventory-ledger'

function buildQuery(filters?: Record<string, unknown>): string {
  if (!filters) return ''
  const entries: [string, string][] = []
  for (const [k, v] of Object.entries(filters)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) {
      for (const item of v) entries.push([k, String(item)])
    } else {
      entries.push([k, String(v)])
    }
  }
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : ''
}

export const inventoryFuturePreparationsApi = {
  /** GET /inventory/movements/{movement_id}/balance-preparation */
  async getBalancePreparation(movementId: string, filters?: Record<string, unknown>): Promise<InventoryBalancePreparationRow[]> {
    return apiRequest({
      path: `/logistics/inventory/movements/${movementId}/balance-preparation${buildQuery(filters)}`,
      method: 'GET',
    })
  },

  /** GET /inventory/movements/{movement_id}/traceability-preparation */
  async getTraceabilityPreparation(movementId: string, filters?: Record<string, unknown>): Promise<InventoryTraceabilityPreparationRow[]> {
    return apiRequest({
      path: `/logistics/inventory/movements/${movementId}/traceability-preparation${buildQuery(filters)}`,
      method: 'GET',
    })
  },

  /** GET /inventory/ledger/balance-preparation */
  async getLedgerBalancePreparation(filters?: Record<string, unknown>): Promise<InventoryBalancePreparationRow[]> {
    return apiRequest({
      path: `/logistics/inventory/ledger/balance-preparation${buildQuery(filters)}`,
      method: 'GET',
    })
  },

  /** GET /inventory/ledger/traceability-preparation */
  async getLedgerTraceabilityPreparation(filters?: Record<string, unknown>): Promise<InventoryTraceabilityPreparationRow[]> {
    return apiRequest({
      path: `/logistics/inventory/ledger/traceability-preparation${buildQuery(filters)}`,
      method: 'GET',
    })
  },
}
