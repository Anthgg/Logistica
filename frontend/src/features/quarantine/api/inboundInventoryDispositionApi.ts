import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InboundInventoryDispositionAllocation,
  InventoryDispositionSplit,
} from '../types/quarantine'

const BASE = '/logistics/inbound-inventory-disposition-allocations'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function buildQuery(params: Record<string, unknown>): string {
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

export const inboundInventoryDispositionApi = {
  /** GET /inbound-inventory-disposition-allocations */
  async listAllocations(query?: Record<string, unknown>): Promise<InboundInventoryDispositionAllocation[]> {
    return apiRequest({ path: `${BASE}${query ? buildQuery(query) : ''}`, method: 'GET' })
  },

  /** POST /inbound-inventory-disposition-allocations/from-receipt */
  async createFromReceipt(data: { receipt_id: string; receipt_line_id?: string; quantity?: string; unit_id?: string }): Promise<InboundInventoryDispositionAllocation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/from-receipt`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /inbound-inventory-disposition-allocations/{allocationId} */
  async getAllocation(allocationId: string): Promise<InboundInventoryDispositionAllocation> {
    return apiRequest({ path: `${BASE}/${allocationId}`, method: 'GET' })
  },

  /** POST /inbound-inventory-disposition-allocations/{allocationId}/evaluate */
  async evaluate(allocationId: string): Promise<InboundInventoryDispositionAllocation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${allocationId}/evaluate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /inbound-inventory-disposition-allocations/{allocationId}/split */
  async split(allocationId: string, data: Record<string, unknown>): Promise<InventoryDispositionSplit> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${allocationId}/split`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
