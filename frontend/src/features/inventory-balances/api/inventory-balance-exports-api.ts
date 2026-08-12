import { apiRequest } from '../../../api/api-client'
import type {
  InventoryBalanceExport,
  InventoryBalanceExportRequest,
} from '../types/inventory-balances'

export const inventoryBalanceExportsApi = {
  async createExport(
    request: InventoryBalanceExportRequest,
  ): Promise<InventoryBalanceExport> {
    return apiRequest<InventoryBalanceExport>({
      path: '/logistics/inventory/balances/exports',
      method: 'POST',
      body: request,
      requiresCsrf: true,
    })
  },

  async getExport(exportId: string): Promise<InventoryBalanceExport> {
    return apiRequest<InventoryBalanceExport>({
      path: `/logistics/inventory/balances/exports/${exportId}`,
      method: 'GET',
    })
  },

  async downloadExport(exportId: string): Promise<Blob> {
    const response = await fetch(
      `/logistics/inventory/balances/exports/${exportId}/download`,
      { credentials: 'include' },
    )
    if (!response.ok) throw new Error('Error downloading export')
    return response.blob()
  },
}
