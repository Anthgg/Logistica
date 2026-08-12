export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'APPROVED'
  | 'ISSUED'
  | 'CONFIRMED'
  | 'PARTIALLY_RECEIVED'
  | 'CLOSED'
  | 'ANNULLED'

export interface PurchaseOrderLine {
  id: string
  line_number: number
  product_id: string
  description: string
  unit_code: string
  quantity: string
  unit_price: string
  tax_rate: string
  subtotal_amount: string
  tax_amount: string
  total_amount: string
}

export interface PurchaseOrderLineCreate {
  product_id: string
  description?: string | null
  unit_code?: string | null
  quantity: string
  unit_price: string
  tax_rate?: string
}

export interface PurchaseOrder {
  id: string
  organization_id: string
  supplier_id: string
  supplier_name: string
  order_number: string
  currency_code: string
  subtotal_amount: string
  tax_amount: string
  total_amount: string
  status: PurchaseOrderStatus
  expected_delivery_date: string | null
  notes: string | null
  row_version: number
  approved_by: string | null
  approved_at: string | null
  issued_by: string | null
  issued_at: string | null
  annulled_by: string | null
  annulled_at: string | null
  annulment_reason: string | null
  created_at: string
  updated_at: string
  lines: PurchaseOrderLine[]
}

export type PurchaseOrderSummary = PurchaseOrder

export interface PurchaseOrderCreate {
  supplier_id: string
  currency_code?: string
  expected_delivery_date?: string | null
  notes?: string | null
  lines: PurchaseOrderLineCreate[]
}

export interface PurchaseOrderUpdate {
  expected_delivery_date?: string | null
  notes?: string | null
}

export interface PurchaseOrderListQuery {
  status?: PurchaseOrderStatus
  supplier_id?: string
}

export interface PurchaseOrderCancel {
  reason: string
}
