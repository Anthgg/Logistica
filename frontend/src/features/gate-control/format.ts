import type {
  GateArrivalClassification,
  GateCheckInStatus,
  GateEntryDecisionType,
  GateExceptionStatus,
  GateLicenseStatus,
  GatePlateMatchStatus,
  GateSealPhysicalStatus,
  GateVerificationState,
  GateCheckResultValue,
  GateCorrectionStatus,
  GatePhotoEvidenceType,
  WarehouseGateStatus,
  GateType,
} from './types/gate-control'

const STATUS_LABELS: Record<GateCheckInStatus, string> = {
  CREATED: 'Creado',
  ARRIVED: 'Llegada registrada',
  IN_VERIFICATION: 'En verificación',
  HELD: 'Retenido',
  WAITING_SUPERVISOR: 'Esperando supervisor',
  AUTHORIZED: 'Autorizado',
  AUTHORIZED_WITH_OBSERVATIONS: 'Autorizado con observaciones',
  DENIED: 'Denegado',
  COMPLETED: 'Completado',
  CANCELLED: 'Cancelado',
}

export function checkInStatusLabel(s: GateCheckInStatus): string {
  return STATUS_LABELS[s] ?? s
}

const CLASSIFICATION_LABELS: Record<GateArrivalClassification, string> = {
  EARLY: 'Temprana',
  ON_TIME: 'A tiempo',
  LATE: 'Tardía',
  WALK_IN: 'Sin cita',
  UNKNOWN: 'Sin determinar',
}

export function arrivalClassificationLabel(c: GateArrivalClassification): string {
  return CLASSIFICATION_LABELS[c] ?? c
}

const DECISION_LABELS: Record<GateEntryDecisionType, string> = {
  AUTHORIZE: 'Autorizar ingreso',
  AUTHORIZE_WITH_OBSERVATIONS: 'Autorizar con observaciones',
  DENY: 'Denegar ingreso',
  HOLD: 'Retener en puerta',
  REQUEST_SUPERVISOR: 'Solicitar supervisor',
}

export function decisionTypeLabel(d: GateEntryDecisionType): string {
  return DECISION_LABELS[d] ?? d
}

const PLATE_LABELS: Record<GatePlateMatchStatus, string> = {
  MATCH: 'Coincide',
  MISMATCH: 'No coincide',
  FORMAT_VALID: 'Formato válido',
  NOT_VERIFIED: 'No verificado',
  REQUIRES_REVIEW: 'Requiere revisión',
}

export function plateMatchStatusLabel(s: GatePlateMatchStatus): string {
  return PLATE_LABELS[s] ?? s
}

const LICENSE_LABELS: Record<GateLicenseStatus, string> = {
  VALID: 'Vigente',
  EXPIRED: 'Vencida',
  NOT_MATCHING: 'No coincide',
  CATEGORY_MISMATCH: 'Categoría no coincide',
  NOT_VERIFIED: 'No verificada',
  REQUIRES_REVIEW: 'Requiere revisión',
}

export function licenseStatusLabel(s: GateLicenseStatus): string {
  return LICENSE_LABELS[s] ?? s
}

const VERIFICATION_LABELS: Record<GateVerificationState, string> = {
  NOT_VERIFIED: 'No verificado',
  FORMAT_VALID: 'Formato válido',
  VERIFIED_BY_SOURCE: 'Verificado por fuente autorizada',
  NOT_MATCHING: 'No coincide',
  REQUIRES_REVIEW: 'Requiere revisión',
}

export function verificationStateLabel(s: GateVerificationState): string {
  return VERIFICATION_LABELS[s] ?? s
}

const SEAL_LABELS: Record<GateSealPhysicalStatus, string> = {
  INTACT: 'Intacto',
  BROKEN: 'Roto',
  TAMPERED: 'Manipulado',
  DAMAGED: 'Dañado',
  ABSENT: 'Ausente',
  ILLEGIBLE: 'Ilegible',
  NOT_APPLICABLE: 'No aplica',
}

export function sealPhysicalStatusLabel(s: GateSealPhysicalStatus): string {
  return SEAL_LABELS[s] ?? s
}

const CHECK_RESULT_LABELS: Record<GateCheckResultValue, string> = {
  COMPLIANT: 'Cumple',
  COMPLIANT_WITH_OBSERVATION: 'Cumple con observación',
  NON_COMPLIANT: 'No cumple',
  NOT_APPLICABLE: 'No aplica',
  NOT_VERIFIED: 'No verificado',
  REQUIRES_REVIEW: 'Requiere revisión',
}

export function checkResultLabel(r: GateCheckResultValue): string {
  return CHECK_RESULT_LABELS[r] ?? r
}

const EXCEPTION_LABELS: Record<GateExceptionStatus, string> = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  SUPERSEDED: 'Reemplazada',
}

export function exceptionStatusLabel(s: GateExceptionStatus): string {
  return EXCEPTION_LABELS[s] ?? s
}

const CORRECTION_LABELS: Record<GateCorrectionStatus, string> = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  APPLIED: 'Aplicada',
}

export function correctionStatusLabel(s: GateCorrectionStatus): string {
  return CORRECTION_LABELS[s] ?? s
}

const EVIDENCE_LABELS: Record<GatePhotoEvidenceType, string> = {
  VEHICLE: 'Vehículo',
  PLATE: 'Placa',
  DRIVER_RESTRICTED: 'Conductor (restringido)',
  DOCUMENT: 'Documento',
  GUIDE: 'Guía',
  SEAL: 'Precinto',
  EXTERIOR_CONDITION: 'Condición exterior',
  SECURITY: 'Seguridad',
}

export function evidenceTypeLabel(e: GatePhotoEvidenceType): string {
  return EVIDENCE_LABELS[e] ?? e
}

const GATE_STATUS_LABELS: Record<WarehouseGateStatus, string> = {
  ACTIVE: 'Activo',
  INACTIVE: 'Inactivo',
  ARCHIVED: 'Archivado',
}

export function gateStatusLabel(s: WarehouseGateStatus): string {
  return GATE_STATUS_LABELS[s] ?? s
}

const GATE_TYPE_LABELS: Record<GateType, string> = {
  INBOUND: 'Entrada',
  OUTBOUND: 'Salida',
  BIDIRECTIONAL: 'Bidireccional',
}

export function gateTypeLabel(t: GateType): string {
  return GATE_TYPE_LABELS[t] ?? t
}

export function isPlateFormat(value: string): boolean {
  // Validación superficial: letras, dígitos, guiones. No autoritativa.
  return /^[A-Za-z0-9-]{3,12}$/.test(value.trim())
}

export function normalizePlate(value: string): string {
  return value.trim().toUpperCase()
}

export function generateIdempotencyKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export function formatServerTime(serverTime: string | null, timezone: string | null): string {
  if (!serverTime) return '—'
  try {
    return new Date(serverTime).toLocaleString('es-PE', {
      timeZone: timezone ?? undefined,
      dateStyle: 'medium',
      timeStyle: 'medium',
    })
  } catch {
    return serverTime
  }
}