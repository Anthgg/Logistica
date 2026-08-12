import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { PaginatedResponse } from '../../../types/logistics-resources'
import type {
  GateTodaySummary,
  GateCheckIn,
  GateCheckInListQuery,
  WarehouseGate,
  WarehouseGateCreate,
  WarehouseGateUpdate,
} from '../types/gate-control'

const BASE = '/logistics/warehouse-gates'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((t) => ({ 'X-CSRF-Token': t }))
}

export const warehouseGatesApi = {
  async list(query?: { warehouse_id?: string; status?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<WarehouseGate>> {
    const params = new URLSearchParams()
    if (query?.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query?.status) params.set('status', query.status)
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest({ path: `${BASE}${qs ? `?${qs}` : ''}` })
  },

  async get(id: string): Promise<WarehouseGate> {
    return apiRequest({ path: `${BASE}/${id}` })
  },

  async create(payload: WarehouseGateCreate): Promise<WarehouseGate> {
    return apiRequest({ path: BASE, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async update(id: string, payload: WarehouseGateUpdate): Promise<WarehouseGate> {
    return apiRequest({ path: `${BASE}/${id}`, method: 'PATCH', headers: await withCsrf(), body: payload })
  },

  async activate(id: string): Promise<WarehouseGate> {
    return apiRequest({ path: `${BASE}/${id}/activate`, method: 'POST', headers: await withCsrf(), body: {} })
  },

  async deactivate(id: string): Promise<WarehouseGate> {
    return apiRequest({ path: `${BASE}/${id}/deactivate`, method: 'POST', headers: await withCsrf(), body: {} })
  },

  async archive(id: string): Promise<WarehouseGate> {
    return apiRequest({ path: `${BASE}/${id}/archive`, method: 'POST', headers: await withCsrf(), body: {} })
  },

  async getQueue(gateId: string, query?: GateCheckInListQuery): Promise<PaginatedResponse<GateCheckIn>> {
    const params = new URLSearchParams()
    if (query?.status) params.set('status', query.status)
    if (query?.tab) params.set('tab', query.tab)
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest({ path: `${BASE}/${gateId}/current-queue${qs ? `?${qs}` : ''}` })
  },

  async getTodaySummary(gateId: string): Promise<GateTodaySummary> {
    return apiRequest({ path: `${BASE}/${gateId}/today-summary` })
  },

  // Alias para compatibilidad con nombres del spec
  async listWarehouseGates(query?: { warehouse_id?: string }): Promise<WarehouseGate[]> {
    const res = await this.list(query)
    return res.items ?? []
  },

  async getWarehouseGateQueue(gateId: string, query?: GateCheckInListQuery): Promise<GateCheckIn[]> {
    const res = await this.getQueue(gateId, query)
    return res.items ?? []
  },

  async getWarehouseGateTodaySummary(gateId: string): Promise<GateTodaySummary> {
    return this.getTodaySummary(gateId)
  },
}