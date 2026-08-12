import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { InboundScanSession, InboundScannerType } from '../types/inbound-receiving'

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

export const inboundScanSessionsApi = {
  async list(receiptId: string): Promise<InboundScanSession[]> {
    return apiRequest({ path: `${BASE}/${receiptId}/scan-sessions`, method: 'GET' })
  },

  async create(receiptId: string, scannerType: InboundScannerType): Promise<InboundScanSession> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-sessions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { scanner_type: scannerType },
    })
  },

  async pause(receiptId: string, sessionId: string): Promise<InboundScanSession> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-sessions/${sessionId}/pause`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },

  async resume(receiptId: string, sessionId: string): Promise<InboundScanSession> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-sessions/${sessionId}/resume`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },

  async complete(receiptId: string, sessionId: string): Promise<InboundScanSession> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-sessions/${sessionId}/complete`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },

  async cancel(receiptId: string, sessionId: string): Promise<InboundScanSession> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/scan-sessions/${sessionId}/cancel`,
      method: 'POST',
      headers: csrf,
      body: {},
    })
  },
}
