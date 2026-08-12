import { apiRequest } from '../../../api/api-client'
import { getCsrfToken } from '../../../api/csrf'
import type {
  InboundDockQueueEntry,
  InboundDockQueueSummary,
  InboundDockQueueListQuery,
  ChangePriorityRequest,
  PaginatedResponse,
} from '../types/inbound-docks'

const BASE = '/logistics/inbound-dock-queue'

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

export const inboundDockQueueApi = {
  async list(query: InboundDockQueueListQuery = {}): Promise<PaginatedResponse<InboundDockQueueEntry>> {
    const params = new URLSearchParams()
    if (query.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query.dock_id) params.set('dock_id', query.dock_id)
    if (query.status) params.set('status', query.status)
    if (query.priority) params.set('priority', query.priority)
    if (query.supplier_id) params.set('supplier_id', query.supplier_id)
    if (query.carrier_id) params.set('carrier_id', query.carrier_id)
    if (query.search) params.set('search', query.search)
    if (query.date_from) params.set('date_from', query.date_from)
    if (query.date_to) params.set('date_to', query.date_to)
    if (query.with_anomalies != null) params.set('with_anomalies', String(query.with_anomalies))
    if (query.with_reassignment != null) params.set('with_reassignment', String(query.with_reassignment))
    if (query.page != null) params.set('page', String(query.page))
    if (query.page_size != null) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest<PaginatedResponse<InboundDockQueueEntry>>({
      path: `${BASE}${qs ? `?${qs}` : ''}`,
      method: 'GET',
    })
  },

  async get(entryId: string): Promise<InboundDockQueueEntry> {
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/${entryId}`,
      method: 'GET',
    })
  },

  async getSummary(warehouseId: string): Promise<InboundDockQueueSummary> {
    return apiRequest<InboundDockQueueSummary>({
      path: `${BASE}/summary?warehouse_id=${encodeURIComponent(warehouseId)}`,
      method: 'GET',
    })
  },

  async getOrdered(warehouseId: string): Promise<InboundDockQueueEntry[]> {
    const res = await apiRequest<{ items: InboundDockQueueEntry[] } | InboundDockQueueEntry[]>({
      path: `${BASE}/ordered?warehouse_id=${encodeURIComponent(warehouseId)}`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async fromGateCheckIn(data: { gate_check_in_id: string; warehouse_id: string }): Promise<InboundDockQueueEntry> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/from-gate-check-in`,
      method: 'POST',
      headers,
      body: data,
    })
  },

  async changePriority(entryId: string, data: ChangePriorityRequest): Promise<InboundDockQueueEntry> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/${entryId}/change-priority`,
      method: 'POST',
      headers,
      body: {
        priority: data.priority,
        reason: data.reason,
        evidence_file_id: data.evidence_file_id ?? null,
      },
    })
  },

  async markReady(entryId: string): Promise<InboundDockQueueEntry> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/${entryId}/mark-ready`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async hold(entryId: string, reason: string): Promise<InboundDockQueueEntry> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/${entryId}/hold`,
      method: 'POST',
      headers,
      body: { reason },
    })
  },

  async release(entryId: string): Promise<InboundDockQueueEntry> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/${entryId}/resume`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async cancel(entryId: string, reason: string): Promise<InboundDockQueueEntry> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockQueueEntry>({
      path: `${BASE}/${entryId}/remove`,
      method: 'POST',
      headers,
      body: { reason },
    })
  },

  async getHistory(entryId: string): Promise<unknown[]> {
    const res = await apiRequest<{ items: unknown[] } | unknown[]>({
      path: `${BASE}/${entryId}/history`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },
}
