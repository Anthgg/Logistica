import type {
  PurchaseOrderAcknowledgement,
  PurchaseOrderAcknowledgementCreate,
} from '../types/purchase-orders-v2'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const purchaseOrderAcknowledgementsApi = {
  async list(_purchaseOrderId: string): Promise<PurchaseOrderAcknowledgement[]> {
    return []
  },

  async create(
    _purchaseOrderId: string,
    _payload: PurchaseOrderAcknowledgementCreate,
  ): Promise<PurchaseOrderAcknowledgement> {
    return unavailable('La creación de acuses de recibo de OC')
  },

  async validate(
    _purchaseOrderId: string,
    _acknowledgementId: string,
  ): Promise<PurchaseOrderAcknowledgement> {
    return unavailable('La validación de acuses de recibo de OC')
  },
}