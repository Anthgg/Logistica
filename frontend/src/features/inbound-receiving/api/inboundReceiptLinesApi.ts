import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InboundReceiptExpectedLine,
  InboundReceivedLine,
  InboundLineComparison,
  InboundReceiptHistoryEvent,
  ApplyQuantityRequest,
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

export const inboundReceiptLinesApi = {
  async listExpected(receiptId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<InboundReceiptExpectedLine>> {
    return apiRequest({ path: `${BASE}/${receiptId}/expected-lines?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  async listReceived(receiptId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<InboundReceivedLine>> {
    return apiRequest({ path: `${BASE}/${receiptId}/received-lines?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  async getLine(receiptId: string, lineId: string): Promise<InboundReceivedLine> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}`, method: 'GET' })
  },

  async getComparison(receiptId: string, lineId: string): Promise<InboundLineComparison> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}/comparison`, method: 'GET' })
  },

  async getIdentifiers(receiptId: string, lineId: string): Promise<{ barcodes: string[]; packaging: string[] }> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}/identifiers`, method: 'GET' })
  },

  async getHistory(receiptId: string, lineId: string): Promise<InboundReceiptHistoryEvent[]> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}/history`, method: 'GET' })
  },

  async applyQuantity(receiptId: string, data: ApplyQuantityRequest): Promise<InboundReceivedLine> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/apply-quantity`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async validateLine(receiptId: string, lineId: string): Promise<InboundReceivedLine> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/lines/${lineId}/validate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
