import type {
  DriverComplianceStatus,
  DriverEligibilityStatus,
  DriverLifecycleStatus,
  DriverLicenseStatus,
  DriverLicenseVerificationStatus,
  DriverPhotoStatus,
} from '../../types/drivers'

const LIFECYCLE_LABELS: Record<DriverLifecycleStatus, string> = {
  DRAFT: 'Borrador',
  ACTIVE: 'Activo',
  INACTIVE: 'Inactivo',
  SUSPENDED: 'Suspendido',
  BLOCKED: 'Bloqueado',
  RETIRED: 'Retirado',
  ARCHIVED: 'Archivado',
}

const LIFECYCLE_STYLES: Record<DriverLifecycleStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 border-slate-300',
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  INACTIVE: 'bg-slate-50 text-slate-500 border-slate-200',
  SUSPENDED: 'bg-amber-50 text-amber-700 border-amber-300',
  BLOCKED: 'bg-rose-50 text-rose-700 border-rose-300',
  RETIRED: 'bg-slate-100 text-slate-600 border-slate-300',
  ARCHIVED: 'bg-slate-100 text-slate-400 border-slate-200',
}

export function DriverLifecycleBadge({ status }: { status: DriverLifecycleStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${LIFECYCLE_STYLES[status]}`}>
      {LIFECYCLE_LABELS[status]}
    </span>
  )
}

const COMPLIANCE_LABELS: Record<DriverComplianceStatus, string> = {
  UNEVALUATED: 'Sin evaluar',
  COMPLIANT: 'Cumple',
  PARTIAL: 'Cumple parcial',
  NON_COMPLIANT: 'No cumple',
  DOCUMENTS_EXPIRED: 'Docs. vencidos',
  LICENSE_EXPIRED: 'Licencia vencida',
  LICENSE_SUSPENDED: 'Licencia suspendida',
  UNDER_REVIEW: 'En revisión',
  CONFLICT: 'Con conflicto',
}

const COMPLIANCE_STYLES: Record<DriverComplianceStatus, string> = {
  UNEVALUATED: 'bg-slate-100 text-slate-500 border-slate-300',
  COMPLIANT: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  PARTIAL: 'bg-amber-50 text-amber-700 border-amber-300',
  NON_COMPLIANT: 'bg-rose-50 text-rose-700 border-rose-300',
  DOCUMENTS_EXPIRED: 'bg-rose-50 text-rose-700 border-rose-300',
  LICENSE_EXPIRED: 'bg-rose-50 text-rose-700 border-rose-300',
  LICENSE_SUSPENDED: 'bg-amber-50 text-amber-700 border-amber-300',
  UNDER_REVIEW: 'bg-blue-50 text-blue-700 border-blue-300',
  CONFLICT: 'bg-rose-50 text-rose-700 border-rose-300',
}

export function DriverComplianceBadge({ status }: { status: DriverComplianceStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${COMPLIANCE_STYLES[status]}`}>
      {COMPLIANCE_LABELS[status]}
    </span>
  )
}

const ELIGIBILITY_LABELS: Record<DriverEligibilityStatus, string> = {
  UNEVALUATED: 'Sin evaluar',
  ELIGIBLE: 'Elegible',
  INELIGIBLE: 'No elegible',
  RESTRICTED: 'Restringido',
  LICENSE_EXPIRED: 'Licencia vencida',
  DOCUMENTS_INCOMPLETE: 'Docs. incompletos',
  CARRIER_INACTIVE: 'Transportista inactivo',
  BLOCKED: 'Bloqueado',
  UNDER_REVIEW: 'En revisión',
}

const ELIGIBILITY_STYLES: Record<DriverEligibilityStatus, string> = {
  UNEVALUATED: 'bg-slate-100 text-slate-500 border-slate-300',
  ELIGIBLE: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  INELIGIBLE: 'bg-rose-50 text-rose-700 border-rose-300',
  RESTRICTED: 'bg-amber-50 text-amber-700 border-amber-300',
  LICENSE_EXPIRED: 'bg-rose-50 text-rose-700 border-rose-300',
  DOCUMENTS_INCOMPLETE: 'bg-amber-50 text-amber-700 border-amber-300',
  CARRIER_INACTIVE: 'bg-amber-50 text-amber-700 border-amber-300',
  BLOCKED: 'bg-rose-50 text-rose-700 border-rose-300',
  UNDER_REVIEW: 'bg-blue-50 text-blue-700 border-blue-300',
}

export function DriverEligibilityBadge({ status }: { status: DriverEligibilityStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${ELIGIBILITY_STYLES[status]}`}>
      {ELIGIBILITY_LABELS[status]}
    </span>
  )
}

const LICENSE_STATUS_LABELS: Record<DriverLicenseStatus, string> = {
  DRAFT: 'Borrador',
  ACTIVE: 'Vigente',
  SUSPENDED: 'Suspendida',
  REVOKED: 'Revocada',
  EXPIRED: 'Vencida',
  ARCHIVED: 'Archivada',
  SUPERSEDED: 'Sustituida',
}

const LICENSE_STATUS_STYLES: Record<DriverLicenseStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 border-slate-300',
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  SUSPENDED: 'bg-amber-50 text-amber-700 border-amber-300',
  REVOKED: 'bg-rose-50 text-rose-700 border-rose-300',
  EXPIRED: 'bg-rose-50 text-rose-700 border-rose-300',
  ARCHIVED: 'bg-slate-100 text-slate-400 border-slate-200',
  SUPERSEDED: 'bg-slate-100 text-slate-500 border-slate-300',
}

export function DriverLicenseBadge({ status }: { status: DriverLicenseStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${LICENSE_STATUS_STYLES[status]}`}>
      {LICENSE_STATUS_LABELS[status]}
    </span>
  )
}

const VERIFICATION_LABELS: Record<DriverLicenseVerificationStatus, string> = {
  PENDING: 'Pendiente',
  VERIFIED: 'Verificada',
  VERIFIED_EXTERNAL: 'Verificada (externa)',
  REJECTED: 'Rechazada',
  EXPIRED: 'Vencida',
}

export function DriverLicenseVerificationBadge({ status }: { status: DriverLicenseVerificationStatus }) {
  const style = status === 'VERIFIED' || status === 'VERIFIED_EXTERNAL'
    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
    : status === 'PENDING'
      ? 'bg-amber-50 text-amber-700 border-amber-300'
      : 'bg-rose-50 text-rose-700 border-rose-300'
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${style}`}>
      {VERIFICATION_LABELS[status]}
    </span>
  )
}

const PHOTO_STATUS_LABELS: Record<DriverPhotoStatus, string> = {
  PENDING: 'Pendiente',
  ACTIVE: 'Activa',
  REVOKED: 'Revocada',
  ARCHIVED: 'Archivada',
  PENDIENTE_FASE_030: 'Pendiente (Fase 030)',
}

export function DriverPhotoBadge({ status }: { status: DriverPhotoStatus }) {
  const style = status === 'ACTIVE'
    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
    : status === 'PENDIENTE_FASE_030'
      ? 'bg-blue-50 text-blue-700 border-blue-300'
      : 'bg-slate-100 text-slate-500 border-slate-300'
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${style}`}>
      {PHOTO_STATUS_LABELS[status]}
    </span>
  )
}

export function ExpirationChip({ days, isExpired }: { days: number | null; isExpired: boolean }) {
  if (isExpired) {
    return <span className="inline-flex items-center rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 border border-rose-300">Vencido</span>
  }
  if (days === null) {
    return <span className="text-xs text-slate-400">—</span>
  }
  if (days <= 30) {
    return <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-300">{days}d</span>
  }
  return <span className="text-xs text-slate-500">{days}d</span>
}