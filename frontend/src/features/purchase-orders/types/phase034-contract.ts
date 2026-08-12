/**
 * Contrato efectivo de la Fase 034 publicado por el backend 0.9.1.
 *
 * Los importes y cantidades se conservan como strings decimales. El frontend
 * nunca los convierte para tomar decisiones ni vuelve a calcular totales.
 */

export type PurchaseOrderStatus = string
export type PurchaseOrderApprovalStatus = string
export type PurchaseOrderIssuanceStatus = string
export type PurchaseOrderDispatchStatus = string
export type PurchaseOrderAcknowledgementStatus = string

export interface PurchaseOrderSummary {
  id: string
  organization_id: string
  branch_id: string
  purchase_order_code: string | null
  supplier_business_partner_id: string
  supplier_name: string | null
  currency_code: string
  status: PurchaseOrderStatus
  approval_status: PurchaseOrderApprovalStatus
  issuance_status: PurchaseOrderIssuanceStatus
  dispatch_status: PurchaseOrderDispatchStatus
  acknowledgement_status: PurchaseOrderAcknowledgementStatus
  subtotal: string
  discount_total: string
  tax_total: string
  freight_total: string
  grand_total: string
  created_at: string
  updated_at: string
}

export interface PurchaseOrderLine {
  id: string
  line_number: number
  product_id: string | null
  product_name_snapshot: string
  product_description_snapshot: string | null
  supplier_product_reference: string | null
  ordered_quantity: string
  ordered_unit_code: string
  unit_price: string
  currency_code: string
  discount_amount: string
  tax_amount: string
  freight_amount: string
  other_charges_amount: string
  line_subtotal: string
  line_total: string
  status: string
  created_at: string
}

export interface PurchaseOrderRevision {
  id: string
  revision_number: number
  status: string
  currency_code: string
  supplier_snapshot: Record<string, unknown> | null
  monetary_summary: Record<string, unknown> | null
  content_hash: string | null
  lines: PurchaseOrderLine[]
  created_at: string
  approved_at: string | null
}

export interface PurchaseOrderDetail extends PurchaseOrderSummary {
  source_decision_id: string
  buyer_user_id: string
  current_revision_number: number
  supplier_snapshot: Record<string, unknown> | null
  supplier_address_snapshot: Record<string, unknown> | null
  supplier_contact_snapshot: Record<string, unknown> | null
  buyer_snapshot: Record<string, unknown> | null
  notes: string | null
  approved_at: string | null
  approved_by: string | null
  issued_at: string | null
  dispatched_at: string | null
  acknowledged_at: string | null
  cancelled_at: string | null
  cancellation_reason: string | null
  revisions: PurchaseOrderRevision[]
}

export interface PurchaseOrderListQuery {
  branch_id?: string | null
  supplier_id?: string | null
  status?: string | null
  approval_status?: string | null
  limit?: number
  offset?: number
}

export interface PurchaseOrderGenerationPlanRequest {
  evaluation_decision_id: string
}

export interface PurchaseOrderGenerationPlanLine {
  evaluation_decision_line_id: string
  product_name_snapshot: string
  ordered_quantity: string
  ordered_unit_code: string
  unit_price: string
  currency_code: string
  source_line_total: string
}

export interface PurchaseOrderGenerationPlanEntry {
  entry_index: number
  supplier_business_partner_id: string
  supplier_name_snapshot: string
  currency_code: string
  estimated_subtotal: string
  estimated_grand_total: string
  lines?: PurchaseOrderGenerationPlanLine[]
  warnings?: string[]
}

export interface PurchaseOrderGenerationPlan {
  evaluation_decision_id: string
  evaluation_decision_status: string
  is_executable: boolean
  total_orders_to_create: number
  entries?: PurchaseOrderGenerationPlanEntry[]
  blocking_issues?: string[]
  warnings?: string[]
}

export interface PurchaseOrderRejectRequest {
  reason: string
}

export interface PurchaseOrderReturnRequest {
  reason: string
}

export interface PurchaseOrderCancelRequest {
  cancellation_reason: string
}

export type PurchaseOrderAction =
  | 'submit'
  | 'approve'
  | 'reject'
  | 'return'
  | 'cancel'

export interface Phase034BackendSupport {
  list: true
  detail: true
  generation_preview: true
  generation_execute: false
  capabilities: false
  update: false
  submit: true
  approve: true
  reject: true
  return_for_changes: true
  cancel: true
  issue: false
  document: false
  dispatch: false
  acknowledgement: false
  amendments: false
  history: false
}

export const PHASE_034_BACKEND_SUPPORT: Phase034BackendSupport = {
  list: true,
  detail: true,
  generation_preview: true,
  generation_execute: false,
  capabilities: false,
  update: false,
  submit: true,
  approve: true,
  reject: true,
  return_for_changes: true,
  cancel: true,
  issue: false,
  document: false,
  dispatch: false,
  acknowledgement: false,
  amendments: false,
  history: false,
}
