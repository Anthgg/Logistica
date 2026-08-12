import { describe, expect, it } from 'vitest'
import {
  checkInStatusLabel,
  arrivalClassificationLabel,
  decisionTypeLabel,
  plateMatchStatusLabel,
  licenseStatusLabel,
  verificationStateLabel,
  sealPhysicalStatusLabel,
  checkResultLabel,
  exceptionStatusLabel,
  evidenceTypeLabel,
  gateStatusLabel,
  gateTypeLabel,
  isPlateFormat,
  normalizePlate,
  generateIdempotencyKey,
  formatServerTime,
} from '../format'
import type {
  GateCheckInStatus,
  GateArrivalClassification,
  GateEntryDecisionType,
  GatePlateMatchStatus,
  GateLicenseStatus,
  GateVerificationState,
  GateSealPhysicalStatus,
  GateCheckResultValue,
  GateExceptionStatus,
  GatePhotoEvidenceType,
  WarehouseGateStatus,
  GateType,
} from '../types/gate-control'

describe('format / labels', () => {
  it('traduce estado de check-in', () => {
    expect(checkInStatusLabel('ARRIVED' as GateCheckInStatus)).toBe('Llegada registrada')
    expect(checkInStatusLabel('AUTHORIZED' as GateCheckInStatus)).toBe('Autorizado')
  })
  it('traduce clasificación de llegada', () => {
    expect(arrivalClassificationLabel('EARLY' as GateArrivalClassification)).toBe('Temprana')
    expect(arrivalClassificationLabel('WALK_IN' as GateArrivalClassification)).toBe('Sin cita')
  })
  it('traduce tipo de decisión', () => {
    expect(decisionTypeLabel('AUTHORIZE' as GateEntryDecisionType)).toBe('Autorizar ingreso')
    expect(decisionTypeLabel('DENY' as GateEntryDecisionType)).toBe('Denegar ingreso')
  })
  it('traduce match de placa', () => {
    expect(plateMatchStatusLabel('MATCH' as GatePlateMatchStatus)).toBe('Coincide')
    expect(plateMatchStatusLabel('MISMATCH' as GatePlateMatchStatus)).toBe('No coincide')
  })
  it('traduce estado de licencia', () => {
    expect(licenseStatusLabel('VALID' as GateLicenseStatus)).toBe('Vigente')
    expect(licenseStatusLabel('EXPIRED' as GateLicenseStatus)).toBe('Vencida')
  })
  it('traduce estado de verificación', () => {
    expect(verificationStateLabel('VERIFIED_BY_SOURCE' as GateVerificationState)).toBe('Verificado por fuente autorizada')
    expect(verificationStateLabel('NOT_MATCHING' as GateVerificationState)).toBe('No coincide')
  })
  it('traduce estado físico del precinto', () => {
    expect(sealPhysicalStatusLabel('BROKEN' as GateSealPhysicalStatus)).toBe('Roto')
    expect(sealPhysicalStatusLabel('INTACT' as GateSealPhysicalStatus)).toBe('Intacto')
  })
  it('traduce resultado de check', () => {
    expect(checkResultLabel('COMPLIANT' as GateCheckResultValue)).toBe('Cumple')
    expect(checkResultLabel('NON_COMPLIANT' as GateCheckResultValue)).toBe('No cumple')
  })
  it('traduce estado de excepción', () => {
    expect(exceptionStatusLabel('APPROVED' as GateExceptionStatus)).toBe('Aprobada')
    expect(exceptionStatusLabel('PENDING' as GateExceptionStatus)).toBe('Pendiente')
  })
  it('traduce tipo de evidencia', () => {
    expect(evidenceTypeLabel('PLATE' as GatePhotoEvidenceType)).toBe('Placa')
    expect(evidenceTypeLabel('DRIVER_RESTRICTED' as GatePhotoEvidenceType)).toBe('Conductor (restringido)')
  })
  it('traduce estado y tipo de gate', () => {
    expect(gateStatusLabel('ACTIVE' as WarehouseGateStatus)).toBe('Activo')
    expect(gateTypeLabel('INBOUND' as GateType)).toBe('Entrada')
  })
})

describe('plate helpers', () => {
  it('normaliza placa a mayúsculas', () => {
    expect(normalizePlate('abc-123')).toBe('ABC-123')
  })
  it('valida formato de placa superficialmente', () => {
    expect(isPlateFormat('ABC123')).toBe(true)
    expect(isPlateFormat('AB')).toBe(false)
    expect(isPlateFormat('abc 123 con espacios')).toBe(false)
  })
})

describe('generateIdempotencyKey', () => {
  it('genera un string único no vacío', () => {
    const k = generateIdempotencyKey()
    expect(typeof k).toBe('string')
    expect(k.length).toBeGreaterThan(0)
  })
})

describe('formatServerTime', () => {
  it('muestra guion si no hay hora', () => {
    expect(formatServerTime(null, 'America/Lima')).toBe('—')
  })
  it('formatea hora ISO', () => {
    const out = formatServerTime('2026-07-31T15:00:00Z', 'America/Lima')
    expect(out).not.toBe('—')
  })
})