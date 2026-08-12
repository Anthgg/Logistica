import { apiRequest } from '../../../api/api-client'


export interface RotationDirective {
  directive_id: string
  product_id: string
  warehouse_id: string
  method: string
  lot_id: string | null
  expiration_date: string | null
  current_location_id: string | null
  quantity_available: { value: string; scale: number }
}

export const putawayRotationApi = {
  async getDirectives(warehouseId: string): Promise<RotationDirective[]> {
    return apiRequest({ path: `/logistics/putaway/rotation/warehouses/${warehouseId}`, method: 'GET' })
  },

  async getComplianceReport(warehouseId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/rotation/warehouses/${warehouseId}/compliance`, method: 'GET' })
  },

  async getProductRotationDirective(warehouseId: string, productId: string): Promise<RotationDirective | null> {
    return apiRequest({ path: `/logistics/putaway/rotation/warehouses/${warehouseId}/products/${productId}`, method: 'GET' })
  },

  async getExpiringItems(warehouseId: string, withinDays?: number): Promise<RotationDirective[]> {
    const qs = withinDays ? `?within_days=${withinDays}` : ''
    return apiRequest({ path: `/logistics/putaway/rotation/warehouses/${warehouseId}/expiring${qs}`, method: 'GET' })
  },
}
