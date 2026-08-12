import type {
  PurchaseOrderDeliveryAttempt,
  PurchaseOrderDispatch,
  PurchaseOrderDispatchCreate,
  PurchaseOrderManualDelivery,
} from '../types/purchase-orders-v2'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const purchaseOrderDispatchApi = {
  async list(_purchaseOrderId: string): Promise<PurchaseOrderDispatch[]> {
    return []
  },

  async create(
    _purchaseOrderId: string,
    _payload: PurchaseOrderDispatchCreate,
  ): Promise<PurchaseOrderDispatch> {
    return unavailable('La creación de despachos de OC')
  },

  async send(
    _purchaseOrderId: string,
    _dispatchId: string,
    _idempotencyKey?: string,
  ): Promise<PurchaseOrderDispatch> {
    return unavailable('El envío de despachos de OC')
  },

  async retry(
    _purchaseOrderId: string,
    _dispatchId: string,
  ): Promise<PurchaseOrderDispatch> {
    return unavailable('El reintento de despacho de OC')
  },

  async markManualDelivery(
    _purchaseOrderId: string,
    _dispatchId: string,
    _payload: PurchaseOrderManualDelivery,
  ): Promise<PurchaseOrderDispatch> {
    return unavailable('El registro de entrega manual de OC')
  },

  async cancelAttempt(
    _purchaseOrderId: string,
    _dispatchId: string,
  ): Promise<PurchaseOrderDispatch> {
    return unavailable('La cancelación de intento de despacho de OC')
  },

  async listAttempts(
    _purchaseOrderId: string,
    _dispatchId: string,
  ): Promise<PurchaseOrderDeliveryAttempt[]> {
    return []
  },
}