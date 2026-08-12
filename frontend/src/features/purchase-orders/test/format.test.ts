import { describe, expect, it } from 'vitest'
import {
  formatDecimal,
  formatMoney,
  isDecimalString,
  purchaseOrderStatusLabel,
  approvalStatusLabel,
  dispatchStatusLabel,
  varianceTypeLabel,
  amendmentTypeLabel,
  groupingRuleLabel,
  generateIdempotencyKey,
} from '../format'
import type {
  PurchaseOrderStatus,
  PurchaseOrderApprovalStatus,
  PurchaseOrderDispatchStatus,
  VarianceType,
  AmendmentType,
  GenerationGroupingRule,
} from '../types/purchase-orders-v2'

describe('formatDecimal / formatMoney', () => {
  it('muestra guion para null o vacío', () => {
    expect(formatDecimal(null)).toBe('—')
    expect(formatDecimal('')).toBe('—')
  })
  it('formatea valor decimal', () => {
    const out = formatDecimal('12.3456', 2)
    expect(['12,35', '12.35']).toContain(out)
  })
  it('formatMoney incluye moneda', () => {
    expect(formatMoney('100', 'USD')).toContain('USD')
    expect(formatMoney(null, 'PEN')).toBe('—')
  })
})

describe('isDecimalString', () => {
  it('acepta enteros y decimales', () => {
    expect(isDecimalString('100')).toBe(true)
    expect(isDecimalString('25.50')).toBe(true)
  })
  it('rechaza negativos y texto', () => {
    expect(isDecimalString('-10')).toBe(false)
    expect(isDecimalString('abc')).toBe(false)
  })
})

describe('generateIdempotencyKey', () => {
  it('genera un string único no vacío', () => {
    const k = generateIdempotencyKey()
    expect(typeof k).toBe('string')
    expect(k.length).toBeGreaterThan(0)
  })
})

describe('etiquetas de dominio OC', () => {
  it('traduce estado general', () => {
    expect(purchaseOrderStatusLabel('DRAFT' as PurchaseOrderStatus)).toBe('Borrador')
    expect(purchaseOrderStatusLabel('ISSUED' as PurchaseOrderStatus)).toBe('Emitida')
  })
  it('traduce estado de aprobación', () => {
    expect(approvalStatusLabel('PENDING' as PurchaseOrderApprovalStatus)).toBe('Pendiente')
    expect(approvalStatusLabel('APPROVED' as PurchaseOrderApprovalStatus)).toBe('Aprobada')
  })
  it('traduce estado de envío', () => {
    expect(dispatchStatusLabel('SENT' as PurchaseOrderDispatchStatus)).toBe('Enviada')
    expect(dispatchStatusLabel('FAILED' as PurchaseOrderDispatchStatus)).toBe('Fallida')
  })
  it('traduce tipo de variación', () => {
    expect(varianceTypeLabel('PRICE' as VarianceType)).toBe('Precio')
  })
  it('traduce tipo de enmienda', () => {
    expect(amendmentTypeLabel('RESCHEDULE' as AmendmentType)).toBe('Reprogramación')
  })
  it('traduce regla de agrupación', () => {
    expect(groupingRuleLabel('BY_SUPPLIER' as GenerationGroupingRule)).toBe('Por proveedor')
    expect(groupingRuleLabel('BY_SUPPLIER_AND_CURRENCY' as GenerationGroupingRule)).toBe('Por proveedor y moneda')
  })
})