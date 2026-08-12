import { apiRequest } from '../../../api/api-client'

export const putawayHistoryApi = {
  async getDashboard(warehouseId?: string): Promise<unknown> {
    const qs = warehouseId ? `?warehouse_id=${warehouseId}` : ''
    return apiRequest({ path: `/logistics/putaway/dashboard${qs}`, method: 'GET' })
  },

  async getOrderHistory(orderId: string): Promise<unknown[]> {
    return apiRequest({ path: `/logistics/putaway/orders/${orderId}/revisions`, method: 'GET' })
  },

  async getTaskHistory(taskId: string): Promise<unknown[]> {
    return apiRequest({ path: `/logistics/putaway/tasks/${taskId}`, method: 'GET' })
  },

  async getIntegrityReport(orderId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/orders/${orderId}/integrity`, method: 'GET' })
  },
}
