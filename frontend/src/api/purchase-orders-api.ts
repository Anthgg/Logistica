import { apiRequest, getCsrfToken } from './api-client'
import type {
  PurchaseOrder,
  PurchaseOrderCancel,
  PurchaseOrderCreate,
  PurchaseOrderListQuery,
  PurchaseOrderUpdate,
} from '../types/purchase-orders'

const BASE = '/logistics/procurement/purchase-orders'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((token) => ({ 'X-CSRF-Token': token }))
}

function withStepUpProof(headers: Record<string, string>, stepUpProofId?: string): Record<string, string> {
  if (stepUpProofId) {
    headers['X-Step-Up-Proof-ID'] = stepUpProofId
  }
  return headers
}

export const purchaseOrdersApi = {
  async list(query?: PurchaseOrderListQuery): Promise<PurchaseOrder[]> {
    const params = new URLSearchParams()
    if (query?.status) params.set('status', query.status)
    if (query?.supplier_id) params.set('supplier_id', query.supplier_id)
    const search = params.toString()
    const res = await apiRequest<PurchaseOrder[] | { items: PurchaseOrder[] }>({
      path: `${BASE}${search ? `?${search}` : ''}`,
    })
    if (Array.isArray(res)) return res
    return (res && 'items' in res ? res.items : []) ?? []
  },

  async get(id: string): Promise<PurchaseOrder> {
    return apiRequest({ path: `${BASE}/${id}` })
  },

  async create(_data: PurchaseOrderCreate): Promise<PurchaseOrder> {
    throw new Error(
      'POST /logistics/procurement/purchase-orders no está publicado en el contrato 0.9.3. '
      + 'Usa purchaseOrdersV2Api (flujo plan-generation → submit → approve).',
    )
  },

  async update(_id: string, _data: PurchaseOrderUpdate): Promise<PurchaseOrder> {
    throw new Error(
      'PATCH /logistics/procurement/purchase-orders/{id} no está publicado en el contrato 0.9.3. '
      + 'Las OC son inmutables tras emisión; usa enmiendas si el backend las soporta.',
    )
  },

  async approve(id: string, stepUpProofId?: string): Promise<PurchaseOrder> {
    const headers = withStepUpProof(await withCsrf(), stepUpProofId)
    return apiRequest({
      path: `${BASE}/${id}/approve`,
      method: 'POST',
      headers,
    })
  },

  async issue(id: string): Promise<PurchaseOrder> {
    return apiRequest({
      path: `${BASE}/${id}/submit`,
      method: 'POST',
      headers: await withCsrf(),
    })
  },

  async cancel(id: string, data: PurchaseOrderCancel): Promise<PurchaseOrder> {
    return apiRequest({
      path: `${BASE}/${id}/cancel`,
      method: 'POST',
      headers: await withCsrf(),
      body: data,
    })
  },
}
