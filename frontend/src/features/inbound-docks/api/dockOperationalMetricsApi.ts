import { apiRequest } from '../../../api/api-client'
import type {
  DockOperationalMetrics,
  DockOperationalTimes,
  InboundDockQueueSummary,
  OperationalTimeQualityStatus,
  PaginatedResponse,
} from '../types/inbound-docks'

const BASE = '/logistics/dock-operation-metrics'

export interface DockMetricsSummary {
  warehouse_id: string
  period_from: string
  period_to: string
  total_assignments: number
  total_completed: number
  total_aborted: number
  avg_wait_seconds: number | null
  avg_movement_seconds: number | null
  avg_unloading_net_seconds: number | null
  avg_dock_occupancy_seconds: number | null
  avg_total_cycle_seconds: number | null
  data_quality: OperationalTimeQualityStatus
  dock_breakdown: DockMetricsDockEntry[]
}

export interface DockMetricsDockEntry {
  dock_id: string
  dock_code: string
  dock_name: string
  total_assignments: number
  total_completed: number
  avg_occupancy_seconds: number | null
  data_quality: OperationalTimeQualityStatus
}

export interface DockMetricsListQuery {
  warehouse_id?: string
  dock_id?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export const dockOperationalMetricsApi = {
  async getSummary(query: {
    warehouse_id: string
    date_from?: string
    date_to?: string
  }): Promise<DockMetricsSummary> {
    const params = new URLSearchParams()
    params.set('warehouse_id', query.warehouse_id)
    const raw = await apiRequest<Record<string, unknown>>({
      path: `${BASE}?${params.toString()}`,
      method: 'GET',
    })
    return {
      warehouse_id: query.warehouse_id,
      period_from: query.date_from ?? new Date().toISOString(),
      period_to: query.date_to ?? new Date().toISOString(),
      total_assignments: Number(raw?.total_assignments ?? 0),
      total_completed: Number(raw?.total_completed ?? 0),
      total_aborted: Number(raw?.total_aborted ?? 0),
      avg_wait_seconds: typeof raw?.avg_wait_seconds === 'number' ? raw.avg_wait_seconds : null,
      avg_movement_seconds: typeof raw?.avg_movement_seconds === 'number' ? raw.avg_movement_seconds : null,
      avg_unloading_net_seconds: typeof raw?.avg_unloading_net_seconds === 'number' ? raw.avg_unloading_net_seconds : null,
      avg_dock_occupancy_seconds: typeof raw?.avg_dock_occupancy_seconds === 'number' ? raw.avg_dock_occupancy_seconds : null,
      avg_total_cycle_seconds: typeof raw?.avg_total_cycle_seconds === 'number' ? raw.avg_total_cycle_seconds : null,
      data_quality: 'COMPLETE',
      dock_breakdown: [],
    }
  },

  async listByAssignment(query: DockMetricsListQuery = {}): Promise<PaginatedResponse<DockOperationalMetrics>> {
    const params = new URLSearchParams()
    if (query.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query.dock_id) params.set('dock_id', query.dock_id)
    const raw = await apiRequest<unknown>({
      path: `${BASE}?${params.toString()}`,
      method: 'GET',
    })
    const items = Array.isArray(raw) ? raw : []
    return {
      items: items as DockOperationalMetrics[],
      page: query.page ?? 1,
      page_size: query.page_size ?? 20,
      total: items.length,
      total_pages: 1,
    }
  },

  async getForAssignment(assignmentId: string): Promise<DockOperationalMetrics> {
    return apiRequest<DockOperationalMetrics>({
      path: `/logistics/inbound-dock-assignments/${assignmentId}/metrics`,
      method: 'GET',
    })
  },

  async getOperationalTimes(assignmentId: string): Promise<DockOperationalTimes> {
    return apiRequest<DockOperationalTimes>({
      path: `/logistics/unloading-operations/${assignmentId}/operational-times`,
      method: 'GET',
    })
  },

  async getQueueSummary(warehouseId: string): Promise<InboundDockQueueSummary> {
    return apiRequest<InboundDockQueueSummary>({
      path: `/logistics/inbound-dock-queue/summary?warehouse_id=${encodeURIComponent(warehouseId)}`,
      method: 'GET',
    })
  },
}
