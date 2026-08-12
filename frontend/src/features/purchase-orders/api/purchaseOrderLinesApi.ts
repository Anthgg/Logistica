import { purchaseOrdersV2Api } from './purchaseOrdersV2Api'
import type {
  PurchaseOrderLine,
  PurchaseOrderLineCreate,
  PurchaseOrderLineUpdate,
  PurchaseOrderMonetarySummary,
  PurchaseOrderSourceVariance,
  PurchaseOrderVarianceCreate,
} from '../types/purchase-orders-v2'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const purchaseOrderLinesApi = {
  async list(purchaseOrderId: string): Promise<PurchaseOrderLine[]> {
    try {
      const po = await purchaseOrdersV2Api.get(purchaseOrderId)
      const lines = po.revisions?.[0]?.lines ?? []
      return lines.map((l, index) => ({
        id: l.id || `line-${index}`,
        purchase_order_id: purchaseOrderId,
        line_number: index + 1,
        source_allocation_id: null,
        product_id: l.product_id || '',
        product_name: l.product_name_snapshot || '',
        sku: l.supplier_product_reference || null,
        awarded_quantity: l.ordered_quantity || '0',
        ordered_quantity: l.ordered_quantity || '0',
        unit: l.ordered_unit_code || 'UND',
        offer_unit_price: l.unit_price || '0',
        unit_price: l.unit_price || '0',
        discount_type: null,
        discount_value: null,
        discount_amount: l.discount_amount || '0',
        taxes: [],
        charges: [],
        freight_amount: l.freight_amount || '0',
        line_total: l.line_total || '0',
        destination_warehouse_id: null,
        delivery_date: null,
        has_variance: false,
        variance_reason: null,
        is_readonly: true,
        row_version: 1,
      }))
    } catch {
      return []
    }
  },

  async create(
    _purchaseOrderId: string,
    _payload: PurchaseOrderLineCreate,
  ): Promise<PurchaseOrderLine> {
    return unavailable('La creación directa de líneas de OC')
  },

  async update(
    _purchaseOrderId: string,
    _lineId: string,
    _payload: PurchaseOrderLineUpdate,
  ): Promise<PurchaseOrderLine> {
    return unavailable('La modificación de líneas de OC')
  },

  async cancel(_purchaseOrderId: string, _lineId: string): Promise<PurchaseOrderLine> {
    return unavailable('La cancelación de líneas de OC')
  },

  async reorder(
    _purchaseOrderId: string,
    _orderedIds: string[],
  ): Promise<PurchaseOrderLine[]> {
    return unavailable('La reordenación de líneas de OC')
  },

  async recalculate(purchaseOrderId: string): Promise<PurchaseOrderMonetarySummary> {
    return this.getMonetarySummary(purchaseOrderId)
  },

  async getMonetarySummary(
    purchaseOrderId: string,
  ): Promise<PurchaseOrderMonetarySummary> {
    try {
      const po = await purchaseOrdersV2Api.get(purchaseOrderId)
      const ms = po.revisions?.[0]?.monetary_summary as Record<string, unknown> | null
      const total = typeof ms?.grand_total === 'string' ? ms.grand_total : String(ms?.grand_total ?? '0')
      return {
        purchase_order_id: purchaseOrderId,
        currency: po.revisions?.[0]?.currency_code || 'PEN',
        subtotal: typeof ms?.subtotal === 'string' ? ms.subtotal : '0',
        total_discounts: typeof ms?.total_discounts === 'string' ? ms.total_discounts : '0',
        taxable_base: typeof ms?.taxable_base === 'string' ? ms.taxable_base : '0',
        total_taxes: typeof ms?.total_taxes === 'string' ? ms.total_taxes : '0',
        total_freight: typeof ms?.total_freight === 'string' ? ms.total_freight : '0',
        total_other_charges: typeof ms?.total_other_charges === 'string' ? ms.total_other_charges : '0',
        rounding_difference: typeof ms?.rounding_difference === 'string' ? ms.rounding_difference : '0',
        grand_total: total,
        calculation_version: null,
        reconciliation_status: 'OK',
        warnings: [],
      }
    } catch {
      return {
        purchase_order_id: purchaseOrderId,
        currency: 'PEN',
        subtotal: '0',
        total_discounts: '0',
        taxable_base: '0',
        total_taxes: '0',
        total_freight: '0',
        total_other_charges: '0',
        rounding_difference: '0',
        grand_total: '0',
        calculation_version: null,
        reconciliation_status: 'OK',
        warnings: [],
      }
    }
  },

  // ── Variaciones ───────────────────────────────────────────────────────────────

  async listVariances(
    _purchaseOrderId: string,
  ): Promise<PurchaseOrderSourceVariance[]> {
    return []
  },

  async createVariance(
    _purchaseOrderId: string,
    _payload: PurchaseOrderVarianceCreate,
  ): Promise<PurchaseOrderSourceVariance> {
    return unavailable('El registro de variaciones de OC')
  },

  async justifyVariance(
    _purchaseOrderId: string,
    _varianceId: string,
    _reason: string,
  ): Promise<PurchaseOrderSourceVariance> {
    return unavailable('La justificación de variaciones de OC')
  },

  async approveVariance(
    _purchaseOrderId: string,
    _varianceId: string,
  ): Promise<PurchaseOrderSourceVariance> {
    return unavailable('La aprobación de variaciones de OC')
  },

  async rejectVariance(
    _purchaseOrderId: string,
    _varianceId: string,
    _reason: string,
  ): Promise<PurchaseOrderSourceVariance> {
    return unavailable('El rechazo de variaciones de OC')
  },
}