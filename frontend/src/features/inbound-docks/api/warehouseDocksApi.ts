import { apiRequest } from '../../../api/api-client'
import { getCsrfToken } from '../../../api/csrf'
import type {
  WarehouseDock,
  WarehouseDockSummary,
  WarehouseDockCreate,
  WarehouseDockUpdate,
  WarehouseDockListQuery,
  WarehouseDockAvailability,
  WarehouseDockBlackout,
  WarehouseDockOperatingWindow,
  WarehouseDockBlockRequest,
  WarehouseDockMaintenanceRequest,
  CreateBlackoutRequest,
  PaginatedResponse,
} from '../types/inbound-docks'

const BASE = '/logistics/warehouse-docks'

function withCsrf() {
  return getCsrfToken().then((t) => ({ 'X-CSRF-Token': t }))
}

function withIdempotency(
  headers: Record<string, string>,
  key?: string,
): Record<string, string> {
  if (key) headers['X-Idempotency-Key'] = key
  return headers
}

function generateKey(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const warehouseDocksApi = {
  async list(query: WarehouseDockListQuery = {}): Promise<PaginatedResponse<WarehouseDockSummary>> {
    const params = new URLSearchParams()
    if (query.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query.status) params.set('status', query.status)
    if (query.operational_status) params.set('operational_status', query.operational_status)
    if (query.type) params.set('type', query.type)
    if (query.direction) params.set('direction', query.direction)
    if (query.search) params.set('search', query.search)
    if (query.page != null) params.set('page', String(query.page))
    if (query.page_size != null) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest<PaginatedResponse<WarehouseDockSummary>>({
      path: `${BASE}${qs ? `?${qs}` : ''}`,
      method: 'GET',
    })
  },

  async get(dockId: string): Promise<WarehouseDock> {
    return apiRequest<WarehouseDock>({
      path: `${BASE}/${dockId}`,
      method: 'GET',
    })
  },

  async getAvailability(dockId: string): Promise<WarehouseDockAvailability> {
    return apiRequest<WarehouseDockAvailability>({
      path: `${BASE}/${dockId}/availability`,
      method: 'GET',
    })
  },

  async getBlackouts(dockId: string): Promise<WarehouseDockBlackout[]> {
    const res = await apiRequest<{ items: WarehouseDockBlackout[] } | WarehouseDockBlackout[]>({
      path: `${BASE}/${dockId}/blackouts`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async getOperatingWindows(dockId: string): Promise<WarehouseDockOperatingWindow[]> {
    const res = await apiRequest<{ items: WarehouseDockOperatingWindow[] } | WarehouseDockOperatingWindow[]>({
      path: `${BASE}/${dockId}/operating-windows`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async create(data: WarehouseDockCreate): Promise<WarehouseDock> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<WarehouseDock>({
      path: BASE,
      method: 'POST',
      headers,
      body: data,
    })
  },

  async update(dockId: string, data: WarehouseDockUpdate): Promise<WarehouseDock> {
    const csrf = await withCsrf()
    return apiRequest<WarehouseDock>({
      path: `${BASE}/${dockId}`,
      method: 'PATCH',
      headers: csrf,
      body: data,
    })
  },

  async block(dockId: string, data: WarehouseDockBlockRequest): Promise<WarehouseDock> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<WarehouseDock>({
      path: `${BASE}/${dockId}/block`,
      method: 'POST',
      headers,
      body: { reason: data.reason },
    })
  },

  async unblock(dockId: string): Promise<WarehouseDock> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<WarehouseDock>({
      path: `${BASE}/${dockId}/unblock`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async setMaintenance(dockId: string, data: WarehouseDockMaintenanceRequest): Promise<WarehouseDock> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<WarehouseDock>({
      path: `${BASE}/${dockId}/mark-maintenance`,
      method: 'POST',
      headers,
      body: data,
    })
  },

  async endMaintenance(dockId: string): Promise<WarehouseDock> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<WarehouseDock>({
      path: `${BASE}/${dockId}/activate`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async createBlackout(data: CreateBlackoutRequest): Promise<WarehouseDockBlackout> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<WarehouseDockBlackout>({
      path: `${BASE}/${data.dock_id}/blackouts`,
      method: 'POST',
      headers,
      body: {
        starts_at: data.starts_at,
        ends_at: data.ends_at,
        reason: data.reason,
      },
    })
  },

  async deleteBlackout(dockId: string, blackoutId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest<void>({
      path: `${BASE}/${dockId}/blackouts/${blackoutId}/cancel`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },
}
