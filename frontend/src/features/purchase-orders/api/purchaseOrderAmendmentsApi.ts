import type {
  PurchaseOrderAmendment,
  PurchaseOrderAmendmentCreate,
} from '../types/purchase-orders-v2'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const purchaseOrderAmendmentsApi = {
  async list(_purchaseOrderId: string): Promise<PurchaseOrderAmendment[]> {
    return []
  },

  async create(
    _purchaseOrderId: string,
    _payload: PurchaseOrderAmendmentCreate,
  ): Promise<PurchaseOrderAmendment> {
    return unavailable('La creación de enmiendas de OC')
  },

  async validate(
    _purchaseOrderId: string,
    _amendmentId: string,
  ): Promise<PurchaseOrderAmendment> {
    return unavailable('La validación de enmiendas de OC')
  },

  async submit(
    _purchaseOrderId: string,
    _amendmentId: string,
  ): Promise<PurchaseOrderAmendment> {
    return unavailable('El envío de enmiendas de OC')
  },

  async approve(
    _purchaseOrderId: string,
    _amendmentId: string,
    _idempotencyKey?: string,
  ): Promise<PurchaseOrderAmendment> {
    return unavailable('La aprobación de enmiendas de OC')
  },

  async issue(
    _purchaseOrderId: string,
    _amendmentId: string,
    _idempotencyKey?: string,
  ): Promise<PurchaseOrderAmendment> {
    return unavailable('La emisión de enmiendas de OC')
  },
}