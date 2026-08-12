import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InventoryMovementCompensationRequest,
  CreateInventoryCompensationRequestRequest,
  SubmitInventoryCompensationRequestRequest,
  ApproveInventoryCompensationRequestRequest,
  RejectInventoryCompensationRequestRequest,
  ExecuteInventoryCompensationRequestRequest,
  CancelInventoryCompensationRequestRequest,
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

export const inventoryMovementCompensationsApi = {
  /** POST /inventory/movements/{movement_id}/compensation-requests */
  async createInventoryCompensationRequest(
    movementId: string,
    data: Omit<CreateInventoryCompensationRequestRequest, 'original_movement_id'>,
  ): Promise<InventoryMovementCompensationRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/movements/${movementId}/compensation-requests`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /inventory/movement-compensation-requests/{request_id} */
  async getInventoryCompensationRequest(requestId: string): Promise<InventoryMovementCompensationRequest> {
    return apiRequest({ path: `/logistics/inventory/movement-compensation-requests/${requestId}`, method: 'GET' })
  },

  /** POST /inventory/movement-compensation-requests/{request_id}/submit */
  async submitInventoryCompensationRequest(data: SubmitInventoryCompensationRequestRequest): Promise<InventoryMovementCompensationRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/movement-compensation-requests/${data.compensation_id}/submit`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /inventory/movement-compensation-requests/{request_id}/approve */
  async approveInventoryCompensationRequest(data: ApproveInventoryCompensationRequestRequest): Promise<InventoryMovementCompensationRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/movement-compensation-requests/${data.compensation_id}/approve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { approval_notes: data.approval_notes },
    })
  },

  /** POST /inventory/movement-compensation-requests/{request_id}/reject */
  async rejectInventoryCompensationRequest(data: RejectInventoryCompensationRequestRequest): Promise<InventoryMovementCompensationRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/movement-compensation-requests/${data.compensation_id}/reject`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { rejection_reason: data.rejection_reason },
    })
  },

  /** POST /inventory/movement-compensation-requests/{request_id}/execute */
  async executeInventoryCompensationRequest(data: ExecuteInventoryCompensationRequestRequest): Promise<InventoryMovementCompensationRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/movement-compensation-requests/${data.compensation_id}/execute`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /inventory/movement-compensation-requests/{request_id}/cancel */
  async cancelInventoryCompensationRequest(data: CancelInventoryCompensationRequestRequest): Promise<InventoryMovementCompensationRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/movement-compensation-requests/${data.compensation_id}/cancel`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { cancellation_reason: data.cancellation_reason },
    })
  },

  // Legacy helper kept for backward compatibility
  async listInventoryMovementCompensations(_filters?: Record<string, unknown>): Promise<InventoryMovementCompensationRequest[]> {
    return []
  },
}
