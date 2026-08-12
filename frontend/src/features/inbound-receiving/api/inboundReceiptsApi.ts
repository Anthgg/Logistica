import { apiRequest, getCsrfToken } from '../../../api/api-client'

import type {
  InboundReceipt,
  InboundReceiptDetail,
  InboundReceiptSummary,
  InboundReceiptProgress,
  InboundReceiptComparison,
  InboundReceiptCapabilities,
  InboundReceiptIntegrity,
  InboundReceiptHistoryEvent,
  InboundReceiptQuery,
  CreateInboundReceiptFromUnloadingRequest,
  PauseReceiptRequest,
  CompleteReceiptRequest,
  EligibleUnloadingOperation,
  ReceptionDifferencePreparation,
  PaginatedResponse,
} from '../types/inbound-receiving'

const BASE = '/logistics/inbound-receipts'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function buildQuery(params: InboundReceiptQuery): string {
  const entries: [string, string][] = []
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue
    if (Array.isArray(v)) {
      for (const item of v) entries.push([k, String(item)])
    } else {
      entries.push([k, String(v)])
    }
  }
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : ''
}

export const inboundReceiptsApi = {
  async list(query: InboundReceiptQuery = {}): Promise<PaginatedResponse<InboundReceipt>> {
    return apiRequest({ path: `${BASE}${buildQuery(query)}`, method: 'GET' })
  },

  async get(receiptId: string): Promise<InboundReceiptDetail> {
    return apiRequest({ path: `${BASE}/${receiptId}`, method: 'GET' })
  },

  async getSummary(): Promise<InboundReceiptSummary> {
    return apiRequest({ path: `${BASE}/summary`, method: 'GET' })
  },

  async getProgress(receiptId: string): Promise<InboundReceiptProgress> {
    return apiRequest({ path: `${BASE}/${receiptId}/progress`, method: 'GET' })
  },

  async getComparison(receiptId: string): Promise<InboundReceiptComparison> {
    return apiRequest({ path: `${BASE}/${receiptId}/comparison`, method: 'GET' })
  },

  async getCapabilities(receiptId: string): Promise<InboundReceiptCapabilities> {
    return apiRequest({ path: `${BASE}/${receiptId}/capabilities`, method: 'GET' })
  },

  async getHistory(receiptId: string): Promise<InboundReceiptHistoryEvent[]> {
    return apiRequest({ path: `${BASE}/${receiptId}/history`, method: 'GET' })
  },

  async getIntegrity(receiptId: string): Promise<InboundReceiptIntegrity> {
    return apiRequest({ path: `${BASE}/${receiptId}/integrity`, method: 'GET' })
  },

  async getDifferencePreparation(receiptId: string): Promise<ReceptionDifferencePreparation> {
    return apiRequest({ path: `${BASE}/${receiptId}/difference-preparation`, method: 'GET' })
  },

  async listEligibleUnloadings(): Promise<EligibleUnloadingOperation[]> {
    return apiRequest({ path: `${BASE}/eligible-unloadings`, method: 'GET' })
  },

  async createFromUnloading(data: CreateInboundReceiptFromUnloadingRequest): Promise<InboundReceipt> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async prepare(receiptId: string): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/prepare`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  async start(receiptId: string): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/start`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  async pause(receiptId: string, data: PauseReceiptRequest): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/pause`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async resume(receiptId: string): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/resume`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  async validate(receiptId: string): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/validate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  async complete(receiptId: string, data: CompleteReceiptRequest): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/complete`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async cancel(receiptId: string, reason: string): Promise<InboundReceiptDetail> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/cancel`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { reason },
    })
  },
}
