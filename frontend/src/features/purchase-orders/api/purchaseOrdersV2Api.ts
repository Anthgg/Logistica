import { apiRequest } from '../../../api/api-client'
import type { PurchaseOrderDocument } from '../types/purchase-orders-v2'
import type {
  PurchaseOrderCancelRequest,
  PurchaseOrderDetail,
  PurchaseOrderGenerationPlan,
  PurchaseOrderGenerationPlanRequest,
  PurchaseOrderListQuery,
  PurchaseOrderRejectRequest,
  PurchaseOrderReturnRequest,
  PurchaseOrderSummary,
} from '../types/phase034-contract'

const BASE = '/logistics/procurement/purchase-orders'

function mutationHeaders(idempotencyKey?: string): HeadersInit | undefined {
  if (!idempotencyKey) return undefined
  return { 'X-Idempotency-Key': idempotencyKey }
}

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado por el backend 0.9.1. La acción se mantiene deshabilitada para no simular datos.`,
  )
}

function normalizeDetail(
  response: PurchaseOrderDetail,
): PurchaseOrderDetail {
  return {
    ...response,
    revisions: (response.revisions ?? []).map((revision) => ({
      ...revision,
      lines: revision.lines ?? [],
    })),
  }
}

export const purchaseOrdersV2Api = {
  async list(
    query: PurchaseOrderListQuery = {},
  ): Promise<PurchaseOrderSummary[]> {
    const params = new URLSearchParams()
    if (query.branch_id) params.set('branch_id', query.branch_id)
    if (query.supplier_id) params.set('supplier_id', query.supplier_id)
    if (query.status) params.set('status', query.status)
    if (query.approval_status) {
      params.set('approval_status', query.approval_status)
    }
    if (query.limit !== undefined) params.set('limit', String(query.limit))
    if (query.offset !== undefined) params.set('offset', String(query.offset))

    const search = params.toString()
    return apiRequest({
      path: `${BASE}${search ? `?${search}` : ''}`,
    })
  },

  async get(id: string): Promise<PurchaseOrderDetail> {
    const response = await apiRequest<PurchaseOrderDetail>({
      path: `${BASE}/${id}`,
    })
    return normalizeDetail(response)
  },

  async createGenerationPlan(
    payload: PurchaseOrderGenerationPlanRequest,
  ): Promise<PurchaseOrderGenerationPlan> {
    return apiRequest({
      path: `${BASE}/plan-generation`,
      method: 'POST',
      body: payload,
    })
  },

  async submitForApproval(
    id: string,
    idempotencyKey?: string,
  ): Promise<PurchaseOrderDetail> {
    const response = await apiRequest<PurchaseOrderDetail>({
      path: `${BASE}/${id}/submit`,
      method: 'POST',
      headers: mutationHeaders(idempotencyKey),
    })
    return normalizeDetail(response)
  },

  async approve(
    id: string,
    idempotencyKey?: string,
  ): Promise<PurchaseOrderDetail> {
    const response = await apiRequest<PurchaseOrderDetail>({
      path: `${BASE}/${id}/approve`,
      method: 'POST',
      headers: mutationHeaders(idempotencyKey),
    })
    return normalizeDetail(response)
  },

  async reject(
    id: string,
    payload: PurchaseOrderRejectRequest,
    idempotencyKey?: string,
  ): Promise<PurchaseOrderDetail> {
    const response = await apiRequest<PurchaseOrderDetail>({
      path: `${BASE}/${id}/reject`,
      method: 'POST',
      headers: mutationHeaders(idempotencyKey),
      body: payload,
    })
    return normalizeDetail(response)
  },

  async returnForChanges(
    id: string,
    payload: PurchaseOrderReturnRequest,
    idempotencyKey?: string,
  ): Promise<PurchaseOrderDetail> {
    const response = await apiRequest<PurchaseOrderDetail>({
      path: `${BASE}/${id}/return-for-changes`,
      method: 'POST',
      headers: mutationHeaders(idempotencyKey),
      body: payload,
    })
    return normalizeDetail(response)
  },

  async cancel(
    id: string,
    payload: PurchaseOrderCancelRequest,
    idempotencyKey?: string,
  ): Promise<PurchaseOrderDetail> {
    const response = await apiRequest<PurchaseOrderDetail>({
      path: `${BASE}/${id}/cancel`,
      method: 'POST',
      headers: mutationHeaders(idempotencyKey),
      body: payload,
    })
    return normalizeDetail(response)
  },

  // Estos métodos permanecen solo para que los paneles adelantados de la
  // maqueta compilen. No hacen solicitudes a endpoints inexistentes.
  async previewDocument(
    _purchaseOrderId: string,
    _idempotencyKey?: string,
  ): Promise<PurchaseOrderDocument> {
    return unavailable('La previsualización del documento de OC')
  },

  async reprintDocument(
    _purchaseOrderId: string,
  ): Promise<PurchaseOrderDocument> {
    return unavailable('La reimpresión del documento de OC')
  },

  async downloadDocument(
    _purchaseOrderId: string,
    _documentId: string,
  ): Promise<Blob> {
    return unavailable('La descarga del documento de OC')
  },
}
