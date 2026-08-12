import { apiRequest } from '../../../api/api-client'

export const putawayProjectionsApi = {
  /** GET /putaway/projections/location/{location_id} */
  async getLocationProjection(locationId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/projections/location/${locationId}`, method: 'GET' })
  },

  /** GET /putaway/projections/product/{product_id} */
  async getProductProjection(productId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/projections/product/${productId}`, method: 'GET' })
  },
}
