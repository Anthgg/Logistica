import type {
  PurchaseOrderDeliverySchedule,
  PurchaseOrderDeliveryScheduleCreate,
  PurchaseOrderDeliveryScheduleUpdate,
  PurchaseOrderDeliveryTerms,
  PurchaseOrderDeliveryTermsUpdate,
  PurchaseOrderPaymentTerms,
  PurchaseOrderPaymentTermsUpdate,
} from '../types/purchase-orders-v2'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const purchaseOrderSchedulesApi = {
  // ── Términos de pago ─────────────────────────────────────────────────────────

  async getPaymentTerms(
    _purchaseOrderId: string,
  ): Promise<PurchaseOrderPaymentTerms | null> {
    return null
  },

  async updatePaymentTerms(
    _purchaseOrderId: string,
    _payload: PurchaseOrderPaymentTermsUpdate,
  ): Promise<PurchaseOrderPaymentTerms> {
    return unavailable('La actualización de términos de pago')
  },

  // ── Condiciones de entrega ───────────────────────────────────────────────────

  async getDeliveryTerms(
    _purchaseOrderId: string,
  ): Promise<PurchaseOrderDeliveryTerms | null> {
    return null
  },

  async updateDeliveryTerms(
    _purchaseOrderId: string,
    _payload: PurchaseOrderDeliveryTermsUpdate,
  ): Promise<PurchaseOrderDeliveryTerms> {
    return unavailable('La actualización de condiciones de entrega')
  },

  // ── Entregas parciales ────────────────────────────────────────────────────────

  async list(_purchaseOrderId: string): Promise<PurchaseOrderDeliverySchedule[]> {
    return []
  },

  async create(
    _purchaseOrderId: string,
    _payload: PurchaseOrderDeliveryScheduleCreate,
  ): Promise<PurchaseOrderDeliverySchedule> {
    return unavailable('La creación de cronogramas de entrega')
  },

  async update(
    _purchaseOrderId: string,
    _scheduleId: string,
    _payload: PurchaseOrderDeliveryScheduleUpdate,
  ): Promise<PurchaseOrderDeliverySchedule> {
    return unavailable('La actualización de cronogramas de entrega')
  },

  async validate(
    _purchaseOrderId: string,
    _scheduleId: string,
  ): Promise<PurchaseOrderDeliverySchedule> {
    return unavailable('La validación de cronogramas de entrega')
  },

  async cancel(
    _purchaseOrderId: string,
    _scheduleId: string,
  ): Promise<PurchaseOrderDeliverySchedule> {
    return unavailable('La cancelación de cronogramas de entrega')
  },
}