import { describe, expect, it } from 'vitest'
import {
  formatDecimal,
  formatMoney,
  visualSum,
  visualDiff,
  isDecimalString,
  evaluationStatusLabel,
  decisionTypeLabel,
  tiePolicyLabel,
  generateIdempotencyKey,
} from '../format'

describe('formatDecimal', () => {
  it('muestra guion para null o vacío', () => {
    expect(formatDecimal(null)).toBe('—')
    expect(formatDecimal('')).toBe('—')
  })
  it('formatea valor decimal como string de presentación', () => {
    const out = formatDecimal('12.3456', 2)
    // No depende del locale exacto: solo valida que redondea a 2 decimales
    expect(['12,35', '12.35']).toContain(out)
  })
  it('devuelve el string original si no es número', () => {
    expect(formatDecimal('abc')).toBe('abc')
  })
})

describe('formatMoney', () => {
  it('incluye moneda cuando se proporciona', () => {
    expect(formatMoney('100.50', 'USD')).toContain('USD')
  })
  it('muestra guion si no hay monto', () => {
    expect(formatMoney(null, 'PEN')).toBe('—')
  })
})

describe('visualSum / visualDiff', () => {
  it('suma pesos visualmente (no autoritativo)', () => {
    expect(visualSum(['25.0000', '25.0000', '50.0000'])).toBe('100.000000')
  })
  it('diferencia hasta 100', () => {
    expect(visualDiff('90', '100')).toBe('10.000000')
  })
  it('maneja valores no finitos', () => {
    expect(visualDiff('abc', '100')).toBe('—')
  })
})

describe('isDecimalString', () => {
  it('acepta enteros y decimales', () => {
    expect(isDecimalString('100')).toBe(true)
    expect(isDecimalString('25.50')).toBe(true)
  })
  it('rechaza negativos u otros signos', () => {
    expect(isDecimalString('-10')).toBe(false)
    expect(isDecimalString('abc')).toBe(false)
  })
})

describe('generateIdempotencyKey', () => {
  it('genera un UUID-like o string único', () => {
    const k = generateIdempotencyKey()
    expect(typeof k).toBe('string')
    expect(k.length).toBeGreaterThan(0)
  })
})

describe('etiquetas de dominio', () => {
  it('traduce estado de evaluación', () => {
    expect(evaluationStatusLabel('DRAFT')).toBe('Borrador')
    expect(evaluationStatusLabel('DECISION_RECORDED')).toBe('Decisión registrada')
  })
  it('traduce tipo de decisión', () => {
    expect(decisionTypeLabel('SINGLE_SUPPLIER')).toBe('Proveedor único')
    expect(decisionTypeLabel('NO_AWARD')).toBe('No adjudicar')
  })
  it('traduce política de empate', () => {
    expect(tiePolicyLabel('LOWEST_PRICE')).toBe('Menor precio')
    expect(tiePolicyLabel('MANUAL')).toBe('Decisión manual')
  })
})