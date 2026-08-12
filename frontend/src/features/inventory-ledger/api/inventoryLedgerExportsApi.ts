import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { InventoryKardexExportApi } from '../types/inventory-ledger-api'

export interface CreateInventoryKardexExportApiRequest {
  format: string
  filters: Record<string, unknown>
  timezone: string
}

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function organizationQuery(organizationId: string): string {
  return `?${new URLSearchParams({ organization_id: organizationId }).toString()}`
}

export const inventoryLedgerExportsApi = {
  async createExport(
    organizationId: string,
    data: CreateInventoryKardexExportApiRequest,
  ): Promise<InventoryKardexExportApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/kardex/exports${organizationQuery(organizationId)}`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async getExport(organizationId: string, exportId: string): Promise<InventoryKardexExportApi> {
    return apiRequest({
      path: `/logistics/inventory/kardex/exports/${exportId}${organizationQuery(organizationId)}`,
      method: 'GET',
    })
  },

  downloadPath(organizationId: string, exportId: string): string {
    return `/logistics/inventory/kardex/exports/${exportId}/download${organizationQuery(organizationId)}`
  },
}
