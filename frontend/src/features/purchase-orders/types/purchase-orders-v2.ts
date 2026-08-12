/**
 * Tipos del dominio de órdenes de compra (Fase 034).
 *
 * Reglas:
 * - Montos, cantidades y porcentajes como `string`. No se usa `number` para
 *   valores de negocio autoritativos.
 * - No se envían `grand_total`, `approved_by`, `organization_id` ni flags de
 *   aprobación calculados localmente.
 * - No se usa `any`.
 */

export interface MoneyValue {
  amount: string
  currency: string
}

export interface DecimalValue {
  value: string
  scale: number
}

export interface FileAssetSummary {
  id: string
  name: string
  content_type: string | null
  size: number | null
  partial_hash: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ApiError {
  code: string
  message: string
  status: number | null
  details?: unknown
}

// ── Estados separados ───────────────────────────────────────────────────────

export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'PENDING_APPROVAL'
  | 'RETURNED'
  | 'APPROVED'
  | 'ISSUED'
  | 'SENT'
  | 'ACKNOWLEDGED'
  | 'CANCELLED'
  | 'CLOSED'
  | 'ARCHIVED'

export type PurchaseOrderApprovalStatus =
  | 'NOT_SUBMITTED'
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'RETURNED'

export type PurchaseOrderIssuanceStatus =
  | 'NOT_ISSUED'
  | 'IN_PROGRESS'
  | 'ISSUED'
  | 'FAILED'
  | 'CANCELLED'

export type PurchaseOrderDispatchStatus =
  | 'NOT_SENT'
  | 'QUEUED'
  | 'SENDING'
  | 'SENT'
  | 'DELIVERED'
  | 'FAILED'
  | 'MANUAL_DELIVERY'

export type PurchaseOrderAcknowledgementStatus =
  | 'NONE'
  | 'PENDING'
  | 'RECEIVED'
  | 'VALIDATED'
  | 'REJECTED'

export type PurchaseOrderFulfilmentStatus =
  | 'NOT_STARTED'
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'PARTIALLY_RECEIVED'
  | 'RECEIVED'
  | 'CLOSED'
  | 'NOT_IMPLEMENTED'

// ── Capabilities ───────────────────────────────────────────────────────────

export interface PurchaseOrderCapabilities {
  purchase_order_id: string
  can_view: boolean
  can_generate: boolean
  can_update: boolean
  can_manage_lines: boolean
  can_manage_terms: boolean
  can_manage_schedules: boolean
  can_manage_files: boolean
  can_validate: boolean
  can_submit_for_approval: boolean
  can_approve_transitional: boolean
  can_reject: boolean
  can_return: boolean
  can_issue: boolean
  can_preview: boolean
  can_download: boolean
  can_reprint: boolean
  can_create_dispatch: boolean
  can_send: boolean
  can_retry_dispatch: boolean
  can_mark_manual_delivery: boolean
  can_create_acknowledgement: boolean
  can_cancel: boolean
  can_create_amendment: boolean
  can_view_history: boolean
}

// ── Origen (decisión) ───────────────────────────────────────────────────────

export interface PurchaseOrderSourceAllocation {
  decision_id: string
  decision_type: string
  cco_code: string
  requisition_code: string
  evaluation_code: string
  round_number: number
  line_id: string
  product_id: string
  product_name: string
  awarded_candidate_id: string
  awarded_supplier_id: string
  awarded_supplier_name: string
  awarded_quantity: string
  awarded_unit: string
  awarded_unit_price: string
  awarded_currency: string
  allocated_quantity: string
  remaining_quantity: string
  is_consumed: boolean
}

// ── Generación desde decisión ───────────────────────────────────────────────

export type GenerationGroupingRule =
  | 'BY_SUPPLIER'
  | 'BY_SUPPLIER_AND_CURRENCY'
  | 'BY_SUPPLIER_CURRENCY_DESTINATION'

export interface PurchaseOrderGenerationOrder {
  index: number
  supplier_id: string
  supplier_name: string
  currency: string
  destination_warehouse_id: string | null
  destination_warehouse_name: string | null
  line_count: number
  total: string
  lines: Array<{
    allocation_id: string
    line_id: string
    product_name: string
    quantity: string
    unit: string
    unit_price: string
  }>
  warnings: string[]
  blocks: string[]
}

export interface PurchaseOrderGenerationPlan {
  decision_id: string
  request_hash: string
  grouping_rule: GenerationGroupingRule
  orders: PurchaseOrderGenerationOrder[]
  excluded_lines: Array<{
    allocation_id: string
    line_id: string
    product_name: string
    reason: string
  }>
  pending_quantity_by_line: Array<{
    line_id: string
    product_name: string
    remaining_quantity: string
  }>
  warnings: string[]
  blocks: string[]
}

export interface PurchaseOrderGenerationPlanRequest {
  decision_id: string
  grouping_rule: GenerationGroupingRule
  destination_warehouse_id?: string | null
}

export interface PurchaseOrderGenerationExecuteRequest {
  plan_hash: string
  decision_id: string
  grouping_rule: GenerationGroupingRule
  destination_warehouse_id?: string | null
}

// ── Líneas ─────────────────────────────────────────────────────────────────

export interface PurchaseOrderTaxComponent {
  id: string
  code: string
  name: string
  base_amount: string
  rate: string
  amount: string
  is_included_in_price: boolean
  source: string
  warnings: string[]
}

export type ChargeType =
  | 'FREIGHT'
  | 'INSURANCE'
  | 'PACKAGING'
  | 'HANDLING'
  | 'INSTALLATION'
  | 'SERVICE'
  | 'OTHER'

export interface PurchaseOrderCharge {
  id: string
  type: ChargeType
  description: string
  amount: string
  tax_code: string | null
  source: string
  scope: 'LINE' | 'HEADER'
  warnings: string[]
}

export interface PurchaseOrderLine {
  id: string
  purchase_order_id: string
  line_number: number
  source_allocation_id: string | null
  product_id: string
  product_name: string
  sku: string | null
  awarded_quantity: string
  ordered_quantity: string
  unit: string
  offer_unit_price: string
  unit_price: string
  discount_type: 'NONE' | 'PERCENTAGE' | 'AMOUNT' | null
  discount_value: string | null
  discount_amount: string | null
  taxes: PurchaseOrderTaxComponent[]
  charges: PurchaseOrderCharge[]
  freight_amount: string | null
  line_total: string | null
  destination_warehouse_id: string | null
  delivery_date: string | null
  has_variance: boolean
  variance_reason: string | null
  is_readonly: boolean
  row_version: number
}

export interface PurchaseOrderLineCreate {
  source_allocation_id: string
  ordered_quantity: string
  unit_price: string
  discount_type?: 'NONE' | 'PERCENTAGE' | 'AMOUNT'
  discount_value?: string | null
  freight_amount?: string | null
  destination_warehouse_id?: string | null
  delivery_date?: string | null
  variance_reason?: string | null
}

export interface PurchaseOrderLineUpdate {
  ordered_quantity?: string
  unit_price?: string
  discount_type?: 'NONE' | 'PERCENTAGE' | 'AMOUNT'
  discount_value?: string | null
  freight_amount?: string | null
  destination_warehouse_id?: string | null
  delivery_date?: string | null
  variance_reason?: string | null
  row_version: number
}

// ── Revisión ───────────────────────────────────────────────────────────────

export interface PurchaseOrderRevision {
  id: string
  purchase_order_id: string
  revision_number: number
  status: 'DRAFT' | 'FROZEN' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED'
  row_version: number
  created_at: string
  updated_at: string
}

// ── Resumen monetario ───────────────────────────────────────────────────────

export interface PurchaseOrderMonetarySummary {
  purchase_order_id: string
  currency: string
  subtotal: string
  total_discounts: string
  taxable_base: string
  total_taxes: string
  total_freight: string
  total_other_charges: string
  rounding_difference: string
  grand_total: string
  calculation_version: string | null
  reconciliation_status: 'OK' | 'PENDING' | 'MISMATCH'
  warnings: string[]
}

// ── Variaciones ────────────────────────────────────────────────────────────

export type VarianceType =
  | 'PRICE'
  | 'QUANTITY'
  | 'DISCOUNT'
  | 'TAX'
  | 'FREIGHT'
  | 'CHARGE'
  | 'DELIVERY_DATE'
  | 'DESTINATION'

export type VarianceStatus = 'DETECTED' | 'JUSTIFIED' | 'APPROVED' | 'REJECTED'

export interface PurchaseOrderSourceVariance {
  id: string
  purchase_order_id: string
  line_id: string | null
  type: VarianceType
  original_value: string
  proposed_value: string
  impact: string
  reason: string | null
  evidence_id: string | null
  evidence_name: string | null
  requested_by: string | null
  reviewed_by: string | null
  status: VarianceStatus
  created_at: string
  updated_at: string
}

export interface PurchaseOrderVarianceCreate {
  line_id: string
  type: VarianceType
  proposed_value: string
  reason: string
  evidence_id?: string | null
}

// ── Términos ───────────────────────────────────────────────────────────────

export type PaymentMethod = 'BANK_TRANSFER' | 'CHECK' | 'CASH' | 'CREDIT' | 'LETTER_OF_CREDIT' | 'OTHER'
export type PaymentTermsType = 'IMMEDIATE' | 'NET_DAYS' | 'ADVANCE_PLUS_BALANCE' | 'MILESTONE' | 'CONSIGNMENT'

export interface PurchaseOrderPaymentTerms {
  type: PaymentTermsType
  method: PaymentMethod
  credit_days: number | null
  advance_percentage: string | null
  balance_percentage: string | null
  milestones: Array<{ label: string; percentage: string; description: string | null }>
  reference: string | null
  retention_percentage: string | null
  notes: string | null
  offer_differs: boolean
  differences_summary: string | null
}

export interface PurchaseOrderPaymentTermsUpdate {
  type?: PaymentTermsType
  method?: PaymentMethod
  credit_days?: number | null
  advance_percentage?: string | null
  balance_percentage?: string | null
  milestones?: PurchaseOrderPaymentTerms['milestones']
  reference?: string | null
  retention_percentage?: string | null
  notes?: string | null
}

export type DeliveryModality = 'DELIVERY' | 'PICKUP' | 'FCA' | 'FAS' | 'FOB' | 'CIF' | 'DAP' | 'DDP' | 'OTHER'
export type FreightResponsibility = 'SUPPLIER' | 'BUYER' | 'SHARED'

export interface PurchaseOrderDeliveryTerms {
  modality: DeliveryModality
  freight_responsibility: FreightResponsibility
  destination_warehouse_id: string | null
  partial_deliveries_allowed: boolean
  early_delivery_allowed: boolean
  tolerance_percentage: string | null
  schedule_window: string | null
  appointment_required: boolean
  packaging: string | null
  labelling: string | null
  required_documents: string[]
  incoterm: string | null
  notes: string | null
}

export interface PurchaseOrderDeliveryTermsUpdate {
  modality?: DeliveryModality
  freight_responsibility?: FreightResponsibility
  destination_warehouse_id?: string | null
  partial_deliveries_allowed?: boolean
  early_delivery_allowed?: boolean
  tolerance_percentage?: string | null
  schedule_window?: string | null
  appointment_required?: boolean
  packaging?: string | null
  labelling?: string | null
  required_documents?: string[]
  incoterm?: string | null
  notes?: string | null
}

// ── Entregas parciales ──────────────────────────────────────────────────────

export interface PurchaseOrderDeliveryScheduleLine {
  line_id: string
  product_name: string
  ordered_quantity: string
  already_scheduled: string
  available: string
  quantity_this_delivery: string
  pending: string
}

export interface PurchaseOrderDeliverySchedule {
  id: string
  purchase_order_id: string
  schedule_number: number
  date: string
  time_start: string | null
  time_end: string | null
  timezone: string
  destination_warehouse_id: string | null
  destination_address: string | null
  instructions: string | null
  status: 'DRAFT' | 'VALIDATED' | 'CANCELLED'
  lines: PurchaseOrderDeliveryScheduleLine[]
  created_at: string
  updated_at: string
}

export interface PurchaseOrderDeliveryScheduleCreate {
  date: string
  time_start?: string | null
  time_end?: string | null
  timezone: string
  destination_warehouse_id?: string | null
  instructions?: string | null
  lines: Array<{ line_id: string; quantity_this_delivery: string }>
}

export interface PurchaseOrderDeliveryScheduleUpdate {
  date?: string
  time_start?: string | null
  time_end?: string | null
  timezone?: string
  destination_warehouse_id?: string | null
  instructions?: string | null
  lines?: Array<{ line_id: string; quantity_this_delivery: string }>
}

// ── Anexos ─────────────────────────────────────────────────────────────────

export type PurchaseOrderFileClassification =
  | 'PROPOSAL'
  | 'SPECIFICATION'
  | 'TERMS'
  | 'BLUEPRINT'
  | 'CERTIFICATE'
  | 'SCHEDULE'
  | 'WARRANTY'
  | 'SUPPORT'

export type PurchaseOrderFileVisibility =
  | 'INTERNAL_ONLY'
  | 'VISIBLE_TO_SUPPLIER'
  | 'VISIBLE_TO_RECEPTION'
  | 'AUDIT_ONLY'

export interface PurchaseOrderFile {
  id: string
  purchase_order_id: string
  file: FileAssetSummary
  classification: PurchaseOrderFileClassification
  visibility: PurchaseOrderFileVisibility
  version: number
  status: 'PENDING' | 'ACCEPTED' | 'QUARANTINE' | 'REVOKED'
  created_at: string
}

export interface PurchaseOrderFileAttach {
  file_id: string
  classification: PurchaseOrderFileClassification
  visibility: PurchaseOrderFileVisibility
}

// ── Aprobación ─────────────────────────────────────────────────────────────

export type ApprovalDecision = 'APPROVED' | 'REJECTED' | 'RETURNED'

export interface PurchaseOrderApprovalDecision {
  id: string
  purchase_order_id: string
  revision_number: number
  policy: 'TRANSITIONAL' | 'MULTILEVEL_NOT_IMPLEMENTED'
  status: PurchaseOrderApprovalStatus
  requested_by: string | null
  requested_at: string | null
  decided_by: string | null
  decided_at: string | null
  decision: ApprovalDecision | null
  reason: string | null
  conditions: string | null
  note_phase_035: string
  can_self_approve: boolean
  created_at: string
}

export interface PurchaseOrderApprovalCreate {
  decision: ApprovalDecision
  reason?: string | null
  conditions?: string | null
}

// ── Documento ──────────────────────────────────────────────────────────────

export interface PurchaseOrderDocument {
  id: string
  purchase_order_id: string
  code: string
  status: 'DRAFT' | 'PREVIEW' | 'ISSUED' | 'VOID' | 'SUPERSEDED'
  version: number
  issued_at: string | null
  partial_hash: string | null
  integrity_ok: boolean
  file: FileAssetSummary | null
  cancellations: number
  reprints: number
  can_preview: boolean
  can_download: boolean
  can_reprint: boolean
  snapshot_authorized: boolean
  created_at: string
  updated_at: string
}

// ── Envío ──────────────────────────────────────────────────────────────────

export type DispatchChannel = 'EMAIL' | 'PORTAL' | 'EDI' | 'MANUAL'

export interface PurchaseOrderDispatch {
  id: string
  purchase_order_id: string
  channel: DispatchChannel
  contact_reference: string
  contact_masked: string
  message: string | null
  status: PurchaseOrderDispatchStatus
  requested_at: string | null
  sent_at: string | null
  delivered_at: string | null
  error_code: string | null
  error_message: string | null
  acknowledgement_expected: boolean
  created_at: string
}

export interface PurchaseOrderDispatchCreate {
  channel: DispatchChannel
  contact_reference: string
  message?: string | null
  include_internal_files: boolean
}

export interface PurchaseOrderDeliveryAttempt {
  id: string
  dispatch_id: string
  attempt_number: number
  channel: DispatchChannel
  technology_provider: string | null
  status: 'QUEUED' | 'SENDING' | 'ACCEPTED' | 'DELIVERED' | 'FAILED'
  requested_at: string | null
  accepted_at: string | null
  delivered_at: string | null
  error_code: string | null
  message_id_partial: string | null
}

export interface PurchaseOrderManualDelivery {
  channel: DispatchChannel
  delivered_at: string
  responsible: string
  reference: string | null
  reason: string
  evidence_id?: string | null
}

// ── Acuse ──────────────────────────────────────────────────────────────────

export type AcknowledgementType = 'EMAIL_REPLY' | 'PORTAL_CONFIRM' | 'SIGNED_DOCUMENT' | 'MANUAL'

export interface PurchaseOrderAcknowledgement {
  id: string
  purchase_order_id: string
  type: AcknowledgementType
  status: PurchaseOrderAcknowledgementStatus
  reference: string | null
  received_at: string | null
  channel: DispatchChannel | null
  name: string | null
  comment: string | null
  file: FileAssetSummary | null
  validated: boolean
  created_at: string
}

export interface PurchaseOrderAcknowledgementCreate {
  type: AcknowledgementType
  reference?: string | null
  received_at?: string | null
  channel?: DispatchChannel | null
  name?: string | null
  comment?: string | null
  file_id?: string | null
}

// ── Enmiendas ───────────────────────────────────────────────────────────────

export type AmendmentType =
  | 'QUANTITY_REDUCTION'
  | 'RESCHEDULE'
  | 'DESTINATION_CHANGE'
  | 'TERMS_CHANGE'
  | 'PRICE_CHANGE_WITH_NEW_DECISION'
  | 'CANCELLATION'
  | 'OTHER'

export type AmendmentStatus = 'DRAFT' | 'VALIDATED' | 'SUBMITTED' | 'APPROVED' | 'ISSUED' | 'CANCELLED'

export interface PurchaseOrderAmendment {
  id: string
  purchase_order_id: string
  amendment_number: number
  type: AmendmentType
  reason: string
  impact_summary: string | null
  status: AmendmentStatus
  approval_status: PurchaseOrderApprovalStatus | null
  document_id: string | null
  document_code: string | null
  created_at: string
  updated_at: string
}

export interface PurchaseOrderAmendmentCreate {
  type: AmendmentType
  reason: string
  impact_summary?: string | null
}

// ── Oferta vencida ─────────────────────────────────────────────────────────

export interface ExpiredOfferInfo {
  is_expired: boolean
  valid_until: string | null
  server_date: string | null
  days_expired: number | null
  supplier_name: string | null
  impact: string | null
  action_allowed: boolean
}

export interface SupplierRatificationInput {
  ratification_date: string
  reference: string | null
  file_id: string | null
  reason: string
  new_validity: string | null
}

// ── Cumplimiento ───────────────────────────────────────────────────────────

export interface PurchaseOrderFulfilment {
  purchase_order_id: string
  ordered_quantity: string
  scheduled_quantity: string
  pending_schedule_quantity: string
  received_quantity: string | null
  source_status: 'BACKEND' | 'NOT_IMPLEMENTED'
  note: string
}

// ── Validación ─────────────────────────────────────────────────────────────

export interface PurchaseOrderValidation {
  purchase_order_id: string
  is_valid: boolean
  errors: Array<{ code: string; message: string; field: string | null }>
  warnings: Array<{ code: string; message: string }>
  checks: Array<{
    code: string
    label: string
    status: 'PASS' | 'FAIL' | 'WARN'
    detail: string | null
  }>
}

// ── Historial ──────────────────────────────────────────────────────────────

export interface PurchaseOrderHistoryEvent {
  id: string
  purchase_order_id: string
  action: string
  previous_state: string | null
  new_state: string | null
  reason: string | null
  revision_number: number | null
  result: string
  actor_display_name: string | null
  occurred_at: string
}

// ── OC raíz ────────────────────────────────────────────────────────────────

export interface PurchaseOrder {
  id: string
  code: string
  status: PurchaseOrderStatus
  approval_status: PurchaseOrderApprovalStatus
  issuance_status: PurchaseOrderIssuanceStatus
  dispatch_status: PurchaseOrderDispatchStatus
  acknowledgement_status: PurchaseOrderAcknowledgementStatus
  fulfilment_status: PurchaseOrderFulfilmentStatus
  source_decision_id: string | null
  source_cco_code: string | null
  requisition_code: string | null
  supplier_id: string
  supplier_name: string
  supplier_code: string | null
  currency: string
  branch_id: string | null
  branch_name: string | null
  cost_center_id: string | null
  cost_center_name: string | null
  destination_warehouse_id: string | null
  destination_warehouse_name: string | null
  buyer_id: string | null
  buyer_name: string | null
  expected_delivery_date_initial: string | null
  expected_delivery_date_final: string | null
  notes: string | null
  row_version: number
  issued_at: string | null
  sent_at: string | null
  cancelled_at: string | null
  cancellation_reason: string | null
  has_variances: boolean
  has_partial_deliveries: boolean
  has_acknowledgement: boolean
  line_count: number
  created_at: string
  updated_at: string
}

export type PurchaseOrderSummary = PurchaseOrder

export interface PurchaseOrderListQuery {
  page?: number
  page_size?: number
  search?: string
  status?: PurchaseOrderStatus | null
  approval_status?: PurchaseOrderApprovalStatus | null
  issuance_status?: PurchaseOrderIssuanceStatus | null
  dispatch_status?: PurchaseOrderDispatchStatus | null
  supplier_id?: string | null
  branch_id?: string | null
  cost_center_id?: string | null
  currency?: string | null
  destination_warehouse_id?: string | null
  date_from?: string | null
  date_to?: string | null
  expected_from?: string | null
  expected_to?: string | null
  with_variances?: boolean
  with_partial_deliveries?: boolean
  without_acknowledgement?: boolean
  pending_my_approval?: boolean
  created_by_me?: boolean
  tab?: 'drafts' | 'pending' | 'issued' | 'sent' | 'cancelled' | null
}

export interface PurchaseOrderHeaderUpdate {
  branch_id?: string | null
  cost_center_id?: string | null
  destination_warehouse_id?: string | null
  buyer_id?: string | null
  expected_delivery_date_initial?: string | null
  expected_delivery_date_final?: string | null
  notes?: string | null
  row_version: number
}