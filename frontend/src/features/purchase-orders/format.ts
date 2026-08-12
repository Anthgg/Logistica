import type {
  AmendmentType,
  ChargeType,
  DispatchChannel,
  PaymentMethod,
  PaymentTermsType,
  PurchaseOrderAcknowledgementStatus,
  PurchaseOrderApprovalStatus,
  PurchaseOrderDispatchStatus,
  PurchaseOrderFulfilmentStatus,
  PurchaseOrderFileClassification,
  PurchaseOrderFileVisibility,
  PurchaseOrderIssuanceStatus,
  PurchaseOrderStatus,
  VarianceStatus,
  VarianceType,
  DeliveryModality,
  FreightResponsibility,
  AcknowledgementType,
  AmendmentStatus,
  ApprovalDecision,
  GenerationGroupingRule,
} from './types/purchase-orders-v2'

export function formatDecimal(value: string | null, maxDecimals = 2): string {
  if (value === null || value === '') return '—'
  const normalized = value.trim()
  const match = /^([+-]?)(\d+)(?:\.(\d+))?$/.exec(normalized)
  if (!match) return value

  const sign = match[1] === '-' ? '-' : ''
  const decimalPlaces = Math.max(0, maxDecimals)
  let integer = (match[2] ?? '0').replace(/^0+(?=\d)/, '')
  const rawFraction = match[3] ?? ''
  let fraction = rawFraction.slice(0, decimalPlaces)

  if (
    rawFraction.length > decimalPlaces &&
    rawFraction.charAt(decimalPlaces) >= '5'
  ) {
    const digits = `${integer}${fraction}`.split('')
    let cursor = digits.length - 1
    let carry = true
    while (cursor >= 0 && carry) {
      if (digits[cursor] === '9') {
        digits[cursor] = '0'
        cursor -= 1
      } else {
        digits[cursor] = String.fromCharCode(
          (digits[cursor]?.charCodeAt(0) ?? 48) + 1,
        )
        carry = false
      }
    }
    if (carry) digits.unshift('1')

    if (decimalPlaces === 0) {
      integer = digits.join('')
      fraction = ''
    } else {
      const splitAt = digits.length - decimalPlaces
      integer = digits.slice(0, splitAt).join('') || '0'
      fraction = digits.slice(splitAt).join('')
    }
  }

  fraction = fraction.replace(/0+$/, '')
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ',')

  return `${sign}${grouped}${fraction ? `.${fraction}` : ''}`
}

export function formatMoney(
  amount: string | null,
  currency: string | null,
  maxDecimals = 2,
): string {
  if (amount === null || amount === '') return '—'
  const text = formatDecimal(amount, maxDecimals)
  return currency ? `${text} ${currency}` : text
}

export function isDecimalString(value: string, maxDecimals = 6): boolean {
  return new RegExp(`^[0-9]{0,12}[.]?[0-9]{0,${maxDecimals}}$`).test(value.trim())
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Borrador',
  VALIDATED: 'Validada',
  PENDING_APPROVAL: 'Pendiente de aprobación',
  RETURNED: 'Devuelta',
  APPROVED: 'Aprobada',
  ISSUED: 'Emitida',
  SENT: 'Enviada',
  ACKNOWLEDGED: 'Acusada',
  CANCELLED: 'Cancelada',
  CLOSED: 'Cerrada',
  ARCHIVED: 'Archivada',
}

export function purchaseOrderStatusLabel(status: PurchaseOrderStatus | string): string {
  return STATUS_LABELS[status] ?? status
}

const APPROVAL_LABELS: Record<string, string> = {
  NOT_SUBMITTED: 'No enviada',
  PENDING: 'Pendiente',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  RETURNED: 'Devuelta',
}

export function approvalStatusLabel(
  status: PurchaseOrderApprovalStatus | string,
): string {
  return APPROVAL_LABELS[status] ?? status
}

const ISSUANCE_LABELS: Record<string, string> = {
  NOT_ISSUED: 'No emitida',
  IN_PROGRESS: 'En proceso',
  ISSUED: 'Emitida',
  FAILED: 'Fallida',
  CANCELLED: 'Cancelada',
}

export function issuanceStatusLabel(
  status: PurchaseOrderIssuanceStatus | string,
): string {
  return ISSUANCE_LABELS[status] ?? status
}

const DISPATCH_LABELS: Record<string, string> = {
  NOT_SENT: 'No enviada',
  QUEUED: 'En cola',
  SENDING: 'Enviando',
  SENT: 'Enviada',
  DELIVERED: 'Entregada',
  FAILED: 'Fallida',
  MANUAL_DELIVERY: 'Entrega manual',
}

export function dispatchStatusLabel(
  status: PurchaseOrderDispatchStatus | string,
): string {
  return DISPATCH_LABELS[status] ?? status
}

const ACK_LABELS: Record<string, string> = {
  NONE: 'Sin acuse',
  PENDING: 'Pendiente',
  RECEIVED: 'Recibido',
  VALIDATED: 'Validado',
  REJECTED: 'Rechazado',
}

export function acknowledgementStatusLabel(
  status: PurchaseOrderAcknowledgementStatus | string,
): string {
  return ACK_LABELS[status] ?? status
}

const FULFILMENT_LABELS: Record<PurchaseOrderFulfilmentStatus, string> = {
  NOT_STARTED: 'No iniciada',
  SCHEDULED: 'Programada',
  IN_PROGRESS: 'En progreso',
  PARTIALLY_RECEIVED: 'Recepción parcial',
  RECEIVED: 'Recibida',
  CLOSED: 'Cerrada',
  NOT_IMPLEMENTED: 'No implementada',
}

export function fulfilmentStatusLabel(status: PurchaseOrderFulfilmentStatus): string {
  return FULFILMENT_LABELS[status] ?? status
}

const VARIANCE_LABELS: Record<VarianceType, string> = {
  PRICE: 'Precio',
  QUANTITY: 'Cantidad',
  DISCOUNT: 'Descuento',
  TAX: 'Impuesto',
  FREIGHT: 'Flete',
  CHARGE: 'Cargo',
  DELIVERY_DATE: 'Fecha de entrega',
  DESTINATION: 'Destino',
}

export function varianceTypeLabel(type: VarianceType): string {
  return VARIANCE_LABELS[type] ?? type
}

const VARIANCE_STATUS_LABELS: Record<VarianceStatus, string> = {
  DETECTED: 'Detectada',
  JUSTIFIED: 'Justificada',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
}

export function varianceStatusLabel(status: VarianceStatus): string {
  return VARIANCE_STATUS_LABELS[status] ?? status
}

const CHARGE_LABELS: Record<ChargeType, string> = {
  FREIGHT: 'Flete',
  INSURANCE: 'Seguro',
  PACKAGING: 'Embalaje',
  HANDLING: 'Manipulación',
  INSTALLATION: 'Instalación',
  SERVICE: 'Servicio',
  OTHER: 'Otro',
}

export function chargeTypeLabel(type: ChargeType): string {
  return CHARGE_LABELS[type] ?? type
}

const FILE_CLASSIFICATION_LABELS: Record<PurchaseOrderFileClassification, string> = {
  PROPOSAL: 'Propuesta comercial',
  SPECIFICATION: 'Especificación',
  TERMS: 'Términos',
  BLUEPRINT: 'Plano',
  CERTIFICATE: 'Certificado',
  SCHEDULE: 'Cronograma',
  WARRANTY: 'Garantía',
  SUPPORT: 'Documento de soporte',
}

export function fileClassificationLabel(
  classification: PurchaseOrderFileClassification,
): string {
  return FILE_CLASSIFICATION_LABELS[classification] ?? classification
}

const VISIBILITY_LABELS: Record<PurchaseOrderFileVisibility, string> = {
  INTERNAL_ONLY: 'Solo interno',
  VISIBLE_TO_SUPPLIER: 'Visible para proveedor',
  VISIBLE_TO_RECEPTION: 'Visible para recepción',
  AUDIT_ONLY: 'Solo auditoría',
}

export function fileVisibilityLabel(visibility: PurchaseOrderFileVisibility): string {
  return VISIBILITY_LABELS[visibility] ?? visibility
}

const PAYMENT_TYPE_LABELS: Record<PaymentTermsType, string> = {
  IMMEDIATE: 'Inmediato',
  NET_DAYS: 'Días netos',
  ADVANCE_PLUS_BALANCE: 'Adelanto + saldo',
  MILESTONE: 'Hitos',
  CONSIGNMENT: 'Consignación',
}

export function paymentTermsTypeLabel(type: PaymentTermsType): string {
  return PAYMENT_TYPE_LABELS[type] ?? type
}

const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  BANK_TRANSFER: 'Transferencia bancaria',
  CHECK: 'Cheque',
  CASH: 'Efectivo',
  CREDIT: 'Crédito',
  LETTER_OF_CREDIT: 'Carta de crédito',
  OTHER: 'Otro',
}

export function paymentMethodLabel(method: PaymentMethod): string {
  return PAYMENT_METHOD_LABELS[method] ?? method
}

const DELIVERY_MODALITY_LABELS: Record<DeliveryModality, string> = {
  DELIVERY: 'Entrega',
  PICKUP: 'Recolección',
  FCA: 'FCA',
  FAS: 'FAS',
  FOB: 'FOB',
  CIF: 'CIF',
  DAP: 'DAP',
  DDP: 'DDP',
  OTHER: 'Otro',
}

export function deliveryModalityLabel(modality: DeliveryModality): string {
  return DELIVERY_MODALITY_LABELS[modality] ?? modality
}

const FREIGHT_RESP_LABELS: Record<FreightResponsibility, string> = {
  SUPPLIER: 'Proveedor',
  BUYER: 'Comprador',
  SHARED: 'Compartido',
}

export function freightResponsibilityLabel(r: FreightResponsibility): string {
  return FREIGHT_RESP_LABELS[r] ?? r
}

const DISPATCH_CHANNEL_LABELS: Record<DispatchChannel, string> = {
  EMAIL: 'Correo',
  PORTAL: 'Portal',
  EDI: 'EDI',
  MANUAL: 'Manual',
}

export function dispatchChannelLabel(channel: DispatchChannel): string {
  return DISPATCH_CHANNEL_LABELS[channel] ?? channel
}

const ACK_TYPE_LABELS: Record<AcknowledgementType, string> = {
  EMAIL_REPLY: 'Respuesta de correo',
  PORTAL_CONFIRM: 'Confirmación en portal',
  SIGNED_DOCUMENT: 'Documento firmado',
  MANUAL: 'Manual',
}

export function acknowledgementTypeLabel(type: AcknowledgementType): string {
  return ACK_TYPE_LABELS[type] ?? type
}

const AMENDMENT_TYPE_LABELS: Record<AmendmentType, string> = {
  QUANTITY_REDUCTION: 'Reducción de cantidad',
  RESCHEDULE: 'Reprogramación',
  DESTINATION_CHANGE: 'Cambio de destino',
  TERMS_CHANGE: 'Cambio de términos',
  PRICE_CHANGE_WITH_NEW_DECISION: 'Cambio de precio con nueva decisión',
  CANCELLATION: 'Cancelación',
  OTHER: 'Otro',
}

export function amendmentTypeLabel(type: AmendmentType): string {
  return AMENDMENT_TYPE_LABELS[type] ?? type
}

const AMENDMENT_STATUS_LABELS: Record<AmendmentStatus, string> = {
  DRAFT: 'Borrador',
  VALIDATED: 'Validada',
  SUBMITTED: 'Enviada',
  APPROVED: 'Aprobada',
  ISSUED: 'Emitida',
  CANCELLED: 'Cancelada',
}

export function amendmentStatusLabel(status: AmendmentStatus): string {
  return AMENDMENT_STATUS_LABELS[status] ?? status
}

const APPROVAL_DECISION_LABELS: Record<ApprovalDecision, string> = {
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  RETURNED: 'Devuelta',
}

export function approvalDecisionLabel(decision: ApprovalDecision): string {
  return APPROVAL_DECISION_LABELS[decision] ?? decision
}

const GROUPING_LABELS: Record<GenerationGroupingRule, string> = {
  BY_SUPPLIER: 'Por proveedor',
  BY_SUPPLIER_AND_CURRENCY: 'Por proveedor y moneda',
  BY_SUPPLIER_CURRENCY_DESTINATION: 'Por proveedor, moneda y destino',
}

export function groupingRuleLabel(rule: GenerationGroupingRule): string {
  return GROUPING_LABELS[rule] ?? rule
}

export function generateIdempotencyKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}
