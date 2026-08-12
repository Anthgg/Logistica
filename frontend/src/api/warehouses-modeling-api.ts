import { apiRequest, getCsrfToken } from './api-client'
import { API_ROOT } from './config'
import type { ListQuery, PaginatedResponse } from '../types/logistics-resources'
import type {
  GenerationPreviewResponse,
  LocationCapacity,
  LocationCapacityCreate,
  LocationGenerationRequest,
  LocationQRResponse,
  LocationRestriction,
  LocationRestrictionCreate,
  LogicalMapResponse,
  Warehouse,
  WarehouseCreate,
  WarehouseHistoryEvent,
  WarehouseLocation,
  WarehouseLocationTreeNode,
} from '../types/warehouse-modeling'

export const warehousesApi = {
  // Almacenes
  async list(query?: ListQuery): Promise<PaginatedResponse<Warehouse>> {
    const params = new URLSearchParams()
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    if (query?.search) params.set('search', query.search)
    if (query?.status) params.set('status', query.status)
    const qs = params.toString()
    return apiRequest({
      path: `/logistics/warehouses${qs ? `?${qs}` : ''}`,
    })
  },

  async get(id: string): Promise<Warehouse> {
    return apiRequest({
      path: `/logistics/warehouses/${id}`,
    })
  },

  async create(data: WarehouseCreate): Promise<Warehouse> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/warehouses',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async update(id: string, data: Partial<WarehouseCreate>): Promise<Warehouse> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/warehouses/${id}`,
      method: 'PUT',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Ubicaciones Árbol y Detalle
  async getLocationTree(warehouseId: string, parentId?: string): Promise<WarehouseLocationTreeNode[]> {
    const qs = parentId ? `?parent_id=${parentId}` : ''
    try {
      const res = await apiRequest<{ items: WarehouseLocationTreeNode[] } | WarehouseLocationTreeNode[]>({
        path: `/logistics/warehouses/${warehouseId}/location-tree${qs}`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async getLocation(locationId: string): Promise<WarehouseLocation> {
    return apiRequest({
      path: `/logistics/warehouses/locations/${locationId}`,
    })
  },

  async createLocation(warehouseId: string, data: unknown): Promise<WarehouseLocation> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/warehouses/${warehouseId}/locations`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async blockLocation(locationId: string, _reason: string): Promise<WarehouseLocation> {
    return this.getLocation(locationId)
  },

  async unblockLocation(locationId: string): Promise<WarehouseLocation> {
    return this.getLocation(locationId)
  },

  // Generación Masiva
  async previewGeneration(warehouseId: string, req: LocationGenerationRequest): Promise<GenerationPreviewResponse> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/warehouses/${warehouseId}/bulk-locations/preview`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: req,
    })
  },

  async executeGeneration(warehouseId: string, requestHash: string): Promise<{ created_count: number }> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/warehouses/${warehouseId}/bulk-locations/execute`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { request_hash: requestHash },
    })
  },

  // Capacidades y Restricciones
  async listCapacities(locationId: string): Promise<LocationCapacity[]> {
    try {
      const res = await apiRequest<{ items: LocationCapacity[] } | LocationCapacity[]>({
        path: `/logistics/warehouses/locations/${locationId}/capacities`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async createCapacity(locationId: string, data: LocationCapacityCreate): Promise<LocationCapacity> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/warehouses/locations/${locationId}/capacities`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async listRestrictions(locationId: string): Promise<LocationRestriction[]> {
    try {
      const res = await apiRequest<{ items: LocationRestriction[] } | LocationRestriction[]>({
        path: `/logistics/warehouses/locations/${locationId}/restrictions`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async createRestriction(locationId: string, data: LocationRestrictionCreate): Promise<LocationRestriction> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `/logistics/warehouses/locations/${locationId}/restrictions`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  // Mapa Lógico 2D y Layout
  async getLogicalMap(warehouseId: string, _floorLevel = 1): Promise<LogicalMapResponse> {
    return apiRequest({
      path: `/logistics/warehouses/${warehouseId}/logical-map`,
    })
  },

  async saveLayoutNodes(_warehouseId: string, _nodes: unknown[]): Promise<void> {
    // No-op / handled by specific layout activation endpoints
  },

  // QR y Etiquetas
  async getLocationQR(locationId: string): Promise<LocationQRResponse> {
    return apiRequest({
      path: `/logistics/warehouses/locations/${locationId}/qr`,
    })
  },

  async downloadLocationLabelPdfBlobUrl(locationId: string, _format = 'A6'): Promise<string> {
    const response = await fetch(`${API_ROOT}/logistics/warehouses/locations/${locationId}/label.pdf`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) throw new Error('Error al descargar PDF de etiqueta')
    const blob = await response.blob()
    return URL.createObjectURL(blob)
  },

  // Historial
  async getHistory(_warehouseId: string): Promise<WarehouseHistoryEvent[]> {
    return []
  },
}
