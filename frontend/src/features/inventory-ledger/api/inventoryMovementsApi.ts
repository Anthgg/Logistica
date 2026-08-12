import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InventoryMovement,
  InventoryMovementSummary,
  InventoryMovementLine,
  InventoryMovementSource,
  InventoryMovementSnapshot,
  InventoryMovementIntegrity,
  InventoryMovementCapabilities,
  InventoryMovementHistoryEvent,
  InventoryMovementCompensationRequest,
  InventoryLedgerDashboardSummary,
  InventoryMovementListFilters,
} from '../types/inventory-ledger'

const BASE = '/logistics/inventory/movements'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function buildQuery(filters?: Record<string, unknown>): string {
  if (!filters) return ''
  const entries: [string, string][] = []
  for (const [k, v] of Object.entries(filters)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) {
      for (const item of v) entries.push([k, String(item)])
    } else {
      entries.push([k, String(v)])
    }
  }
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : ''
}

export const inventoryMovementsApi = {
  /** GET /inventory/movements */
  async listInventoryMovements(filters?: InventoryMovementListFilters): Promise<InventoryMovementSummary[]> {
    return apiRequest({ path: `${BASE}${buildQuery(filters as Record<string, unknown>)}`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id} */
  async getInventoryMovement(movementId: string): Promise<InventoryMovement> {
    return apiRequest({ path: `${BASE}/${movementId}`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/lines */
  async listInventoryMovementLines(movementId: string): Promise<InventoryMovementLine[]> {
    return apiRequest({ path: `${BASE}/${movementId}/lines`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/sources */
  async listInventoryMovementSources(movementId: string): Promise<InventoryMovementSource[]> {
    return apiRequest({ path: `${BASE}/${movementId}/sources`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/snapshot */
  async getInventoryMovementSnapshot(movementId: string): Promise<InventoryMovementSnapshot> {
    return apiRequest({ path: `${BASE}/${movementId}/snapshot`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/history */
  async getInventoryMovementHistory(movementId: string): Promise<InventoryMovementHistoryEvent[]> {
    return apiRequest({ path: `${BASE}/${movementId}/history`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/integrity */
  async getInventoryMovementIntegrity(movementId: string): Promise<InventoryMovementIntegrity> {
    return apiRequest({ path: `${BASE}/${movementId}/integrity`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/capabilities */
  async getInventoryMovementCapabilities(movementId: string): Promise<InventoryMovementCapabilities> {
    return apiRequest({ path: `${BASE}/${movementId}/capabilities`, method: 'GET' })
  },

  /** GET /inventory/movements/{movement_id}/compensations */
  async listInventoryMovementCompensations(movementId: string): Promise<InventoryMovementCompensationRequest[]> {
    return apiRequest({ path: `${BASE}/${movementId}/compensations`, method: 'GET' })
  },

  async getDashboardSummary(warehouseId?: string): Promise<InventoryLedgerDashboardSummary> {
    const qs = warehouseId ? `?warehouse_id=${warehouseId}` : ''
    return apiRequest({ path: `${BASE}/dashboard${qs}`, method: 'GET' })
  },

  async requestStepUp(action: string, payload: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/step-up`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { action, ...payload },
    })
  },
}
