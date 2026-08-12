import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InboundLotObservation,
  InboundSerialObservation,
  InboundExpirationObservation,
  CreateLotObservationRequest,
  CreateSerialObservationRequest,
  CreateSerialBatchRequest,
  CreateExpirationObservationRequest,
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

export const inboundObservationsApi = {
  // ── Lotes ───────────────────────────────────────────────────────────────────
  async listLots(receiptId: string, lineId: string): Promise<InboundLotObservation[]> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}/lot-observations`, method: 'GET' })
  },

  async createLot(receiptId: string, data: CreateLotObservationRequest): Promise<InboundLotObservation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/lot-observations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  // ── Series ──────────────────────────────────────────────────────────────────
  async listSerials(receiptId: string, lineId: string, page = 1, pageSize = 100): Promise<PaginatedResponse<InboundSerialObservation>> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}/serial-observations?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  async createSerial(receiptId: string, data: CreateSerialObservationRequest): Promise<InboundSerialObservation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/serial-observations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  async createSerialBatch(receiptId: string, data: CreateSerialBatchRequest): Promise<InboundSerialObservation[]> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/serial-observations/batch`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  // ── Vencimientos ────────────────────────────────────────────────────────────
  async listExpirations(receiptId: string, lineId: string): Promise<InboundExpirationObservation[]> {
    return apiRequest({ path: `${BASE}/${receiptId}/lines/${lineId}/expiration-observations`, method: 'GET' })
  },

  async createExpiration(receiptId: string, data: CreateExpirationObservationRequest): Promise<InboundExpirationObservation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${receiptId}/expiration-observations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
