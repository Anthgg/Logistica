import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InventoryKardexRow,
  InventoryKardexRunningQuantityRow,
  InventoryKardexScope,
  InventoryKardexQuery,
  InventoryKardexExportRequest,
  CreateInventoryKardexExportRequest,
} from '../types/inventory-ledger'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

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

export const inventoryKardexApi = {
  /** GET /inventory/kardex */
  async getInventoryKardex(query: InventoryKardexQuery): Promise<{ rows: InventoryKardexRow[]; scope: InventoryKardexScope }> {
    return apiRequest({ path: `/logistics/inventory/kardex${buildQuery(query as unknown as Record<string, unknown>)}`, method: 'GET' })
  },

  /** GET /inventory/kardex/technical-running-quantity */
  async getInventoryKardexRunningQuantity(query: InventoryKardexQuery): Promise<{
    rows: InventoryKardexRunningQuantityRow[]
    scope: InventoryKardexScope
  }> {
    return apiRequest({
      path: `/logistics/inventory/kardex/technical-running-quantity${buildQuery(query as unknown as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  /** GET /inventory/kardex/movement-types */
  async listInventoryMovementTypes(): Promise<{ type: string; label: string; family: string }[]> {
    return apiRequest({ path: '/logistics/inventory/kardex/movement-types', method: 'GET' })
  },

  /** GET /inventory/kardex/source-types */
  async listInventorySourceTypes(): Promise<{ system: string; label: string }[]> {
    return apiRequest({ path: '/logistics/inventory/kardex/source-types', method: 'GET' })
  },

  /** GET /inventory/kardex/state-transitions */
  async listInventoryStateTransitions(): Promise<{ from: string; to: string; label: string }[]> {
    return apiRequest({ path: '/logistics/inventory/kardex/state-transitions', method: 'GET' })
  },

  /** POST /inventory/kardex/exports */
  async createInventoryKardexExport(data: CreateInventoryKardexExportRequest): Promise<InventoryKardexExportRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: '/logistics/inventory/kardex/exports',
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /inventory/kardex/exports/{export_id} */
  async getInventoryKardexExport(exportId: string): Promise<InventoryKardexExportRequest> {
    return apiRequest({ path: `/logistics/inventory/kardex/exports/${exportId}`, method: 'GET' })
  },

  /** GET /inventory/kardex/exports/{export_id}/download */
  async downloadInventoryKardexExport(exportId: string): Promise<Blob> {
    return apiRequest({ path: `/logistics/inventory/kardex/exports/${exportId}/download`, method: 'GET' })
  },

  /** GET /inventory/kardex/scope (helper) */
  async getInventoryKardexScope(query: InventoryKardexQuery): Promise<InventoryKardexScope> {
    return apiRequest({ path: `/logistics/inventory/kardex${buildQuery(query as unknown as Record<string, unknown>)}`, method: 'GET' })
  },

  /** List exports (helper) */
  async listExports(_filters?: Record<string, unknown>): Promise<InventoryKardexExportRequest[]> {
    return []
  },
}
