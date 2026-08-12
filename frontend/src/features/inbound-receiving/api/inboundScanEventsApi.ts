import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InboundScanEvent,
  InboundCodeResolution,
  CreateInboundScanEventRequest,
  CreateInboundScanEventBatchRequest,
  CompensateScanRequest,
  ResolveUnknownScanRequest,
  ManualEntryRequest,
  PaginatedResponse,
} from '../types/inbound-receiving'

const BASE = '/logistics/inbound-receipts'

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const inboundScanEventsApi = {
  async create(receiptId: string, data: CreateInboundScanEventRequest): Promise<InboundScanEvent> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-events`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async createBatch(receiptId: string, data: CreateInboundScanEventBatchRequest): Promise<InboundScanEvent[]> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-events/batch`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async list(receiptId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<InboundScanEvent>> {
    return apiRequest({ path: `${BASE}/${receiptId}/scan-events?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  async get(receiptId: string, eventId: string): Promise<InboundScanEvent> {
    return apiRequest({ path: `${BASE}/${receiptId}/scan-events/${eventId}`, method: 'GET' })
  },

  async compensate(receiptId: string, data: CompensateScanRequest): Promise<InboundScanEvent> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-events/${data.event_id}/compensate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async resolve(receiptId: string, eventId: string): Promise<InboundCodeResolution> {
    return apiRequest({ path: `${BASE}/${receiptId}/scan-events/${eventId}/resolve`, method: 'GET' })
  },

  async listUnresolved(receiptId: string): Promise<InboundScanEvent[]> {
    return apiRequest({ path: `${BASE}/${receiptId}/unresolved-scans`, method: 'GET' })
  },

  async resolveUnknown(receiptId: string, eventId: string, data: ResolveUnknownScanRequest): Promise<InboundScanEvent> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/unresolved-scans/${eventId}/resolve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async manualEntry(receiptId: string, data: ManualEntryRequest): Promise<InboundScanEvent> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/manual-entry`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
