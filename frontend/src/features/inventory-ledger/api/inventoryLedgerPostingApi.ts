import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InventoryMovementPostingRequest,
  PreparedInventoryEvent,
  PreparedInventoryEventValidation,
  InventoryPreparedEventsBatchRequest,
  InventoryPreparedEventsBatchRequestInput,
} from '../types/inventory-ledger'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const inventoryLedgerPostingApi = {
  /** POST /inventory/ledger/posting-requests */
  async createInventoryPostingRequest(data: Record<string, unknown>): Promise<InventoryMovementPostingRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: '/logistics/inventory/ledger/posting-requests',
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /inventory/ledger/posting-requests/{request_id} */
  async getInventoryPostingRequest(requestId: string): Promise<InventoryMovementPostingRequest> {
    return apiRequest({ path: `/logistics/inventory/ledger/posting-requests/${requestId}`, method: 'GET' })
  },

  /** POST /inventory/ledger/prepared-events/{source_event_id}/validate */
  async validatePreparedInventoryEvent(sourceEventId: string): Promise<PreparedInventoryEventValidation> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/ledger/prepared-events/${sourceEventId}/validate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /inventory/ledger/prepared-events/{source_event_id}/post */
  async postPreparedInventoryEvent(sourceEventId: string, idempotencyKey: string): Promise<InventoryMovementPostingRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/ledger/prepared-events/${sourceEventId}/post`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': idempotencyKey },
      body: {},
    })
  },

  /** POST /inventory/ledger/materialize/quality-events */
  async materializeQualityInventoryEvents(data: InventoryPreparedEventsBatchRequestInput): Promise<InventoryPreparedEventsBatchRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: '/logistics/inventory/ledger/materialize/quality-events',
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /inventory/ledger/materialize/putaway-events */
  async materializePutawayInventoryEvents(data: InventoryPreparedEventsBatchRequestInput): Promise<InventoryPreparedEventsBatchRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: '/logistics/inventory/ledger/materialize/putaway-events',
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /inventory/ledger/retry-failed-posting/{request_id} */
  async retryInventoryPosting(requestId: string, idempotencyKey: string): Promise<InventoryMovementPostingRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/ledger/retry-failed-posting/${requestId}`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': idempotencyKey },
      body: {},
    })
  },

  /** Helper legacy - use API elsewhere */
  async listPreparedInventoryEvents(_filters?: Record<string, unknown>): Promise<PreparedInventoryEvent[]> {
    return []
  },
}
