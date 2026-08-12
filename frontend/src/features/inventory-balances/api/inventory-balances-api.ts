import { apiRequest } from '../../../api/api-client'
import type {
  InventoryBalanceSummary,
  InventoryPositionBalance,
  InventoryProductBalance,
  InventoryWarehouseBalance,
  InventoryLocationBalance,
  InventoryBalanceAsOfRequest,
  InventoryBalanceAsOfResponse,
  InventoryBalanceFilters,
  PaginatedResponse,
} from '../types/inventory-balances'

function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === '') continue
    if (value instanceof Date) {
      search.set(key, value.toISOString())
    } else if (Array.isArray(value)) {
      search.set(key, value.join(','))
    } else if (typeof value === 'boolean') {
      search.set(key, String(value))
    } else {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export const inventoryBalancesApi = {
  async getSummary(organizationId: string): Promise<InventoryBalanceSummary> {
    return apiRequest<InventoryBalanceSummary>({
      path: `/logistics/inventory/balances/summary${buildQuery({ organization_id: organizationId })}`,
      method: 'GET',
    })
  },

  async listBalances(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async listProductBalances(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryProductBalance>> {
    return apiRequest<PaginatedResponse<InventoryProductBalance>>({
      path: `/logistics/inventory/balances/products${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getProductBalance(
    productId: string,
    filters?: InventoryBalanceFilters,
  ): Promise<InventoryProductBalance> {
    return apiRequest<InventoryProductBalance>({
      path: `/logistics/inventory/balances/products/${productId}${buildQuery((filters ?? {}) as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async listWarehouseBalances(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryWarehouseBalance>> {
    return apiRequest<PaginatedResponse<InventoryWarehouseBalance>>({
      path: `/logistics/inventory/balances/warehouses${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getWarehouseBalance(
    warehouseId: string,
    filters?: InventoryBalanceFilters,
  ): Promise<InventoryWarehouseBalance> {
    return apiRequest<InventoryWarehouseBalance>({
      path: `/logistics/inventory/balances/warehouses/${warehouseId}${buildQuery((filters ?? {}) as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async listLocationBalances(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryLocationBalance>> {
    return apiRequest<PaginatedResponse<InventoryLocationBalance>>({
      path: `/logistics/inventory/balances/locations${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getLocationBalance(
    locationId: string,
    filters?: InventoryBalanceFilters,
  ): Promise<InventoryLocationBalance> {
    return apiRequest<InventoryLocationBalance>({
      path: `/logistics/inventory/balances/locations/${locationId}${buildQuery((filters ?? {}) as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getPositionBalance(
    positionId: string,
  ): Promise<InventoryPositionBalance> {
    return apiRequest<InventoryPositionBalance>({
      path: `/logistics/inventory/balances/positions/${positionId}`,
      method: 'GET',
    })
  },

  async getBalanceAsOf(
    request: InventoryBalanceAsOfRequest,
  ): Promise<InventoryBalanceAsOfResponse> {
    return apiRequest<InventoryBalanceAsOfResponse>({
      path: `/logistics/inventory/balances/as-of`,
      method: 'POST',
      body: request,
      requiresCsrf: true,
    })
  },

  async getPhysicalBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/physical${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getAvailableBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/available${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getReservedBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/reserved${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getBlockedBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/blocked${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getQuarantineBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/quarantine${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getTransitBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/transit${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getDamagedBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/damaged${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getExpiredBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/expired${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },

  async getPendingPutawayBalance(
    filters: InventoryBalanceFilters,
  ): Promise<PaginatedResponse<InventoryPositionBalance>> {
    return apiRequest<PaginatedResponse<InventoryPositionBalance>>({
      path: `/logistics/inventory/balances/pending-putaway${buildQuery(filters as Record<string, unknown>)}`,
      method: 'GET',
    })
  },
}
