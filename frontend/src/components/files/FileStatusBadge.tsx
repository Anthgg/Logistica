import type {
  FileClassification,
  FileIntegrityStatus,
  FileLifecycleStatus,
  FileUploadStatus,
  MalwareScanStatus,
  EvidenceStatus,
  FileDeletionRequestStatus,
} from '../../types/files'

const LIFECYCLE_LABELS: Record<FileLifecycleStatus, string> = {
  UPLOADING: 'Cargando',
  PROCESSING: 'Procesando',
  QUARANTINED: 'En cuarentena',
  AVAILABLE: 'Disponible',
  REJECTED: 'Rechazado',
  ARCHIVED: 'Archivado',
  DELETED: 'Eliminado',
  CORRUPTED: 'Corrupto',
  FAILED: 'Fallido',
}

const LIFECYCLE_STYLES: Record<FileLifecycleStatus, string> = {
  UPLOADING: 'bg-blue-50 text-blue-700 border-blue-300',
  PROCESSING: 'bg-amber-50 text-amber-700 border-amber-300',
  QUARANTINED: 'bg-rose-50 text-rose-700 border-rose-300',
  AVAILABLE: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  REJECTED: 'bg-rose-50 text-rose-700 border-rose-300',
  ARCHIVED: 'bg-slate-100 text-slate-600 border-slate-300',
  DELETED: 'bg-slate-100 text-slate-400 border-slate-200',
  CORRUPTED: 'bg-rose-50 text-rose-700 border-rose-300',
  FAILED: 'bg-rose-50 text-rose-700 border-rose-300',
}

export function FileLifecycleBadge({ status }: { status: FileLifecycleStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${LIFECYCLE_STYLES[status]}`}>
      {LIFECYCLE_LABELS[status]}
    </span>
  )
}

const SCAN_LABELS: Record<MalwareScanStatus, string> = {
  PENDING: 'Pendiente',
  SCANNING: 'Escaneando',
  CLEAN: 'Limpio',
  INFECTED: 'Infectado',
  SCAN_FAILED: 'Escaneo fallido',
  NOT_APPLICABLE: 'N/A',
}

const SCAN_STYLES: Record<MalwareScanStatus, string> = {
  PENDING: 'bg-slate-100 text-slate-500 border-slate-300',
  SCANNING: 'bg-amber-50 text-amber-700 border-amber-300',
  CLEAN: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  INFECTED: 'bg-rose-50 text-rose-700 border-rose-300',
  SCAN_FAILED: 'bg-rose-50 text-rose-700 border-rose-300',
  NOT_APPLICABLE: 'bg-slate-100 text-slate-400 border-slate-200',
}

export function FileScanBadge({ status }: { status: MalwareScanStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${SCAN_STYLES[status]}`}>
      {SCAN_LABELS[status]}
    </span>
  )
}

const INTEGRITY_LABELS: Record<FileIntegrityStatus, string> = {
  VERIFIED: 'Verificada',
  UNVERIFIED: 'Sin verificar',
  MISMATCH: 'No coincide',
  OBJECT_MISSING: 'Objeto faltante',
  CORRUPTED: 'Corrupto',
}

const INTEGRITY_STYLES: Record<FileIntegrityStatus, string> = {
  VERIFIED: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  UNVERIFIED: 'bg-slate-100 text-slate-500 border-slate-300',
  MISMATCH: 'bg-rose-50 text-rose-700 border-rose-300',
  OBJECT_MISSING: 'bg-rose-50 text-rose-700 border-rose-300',
  CORRUPTED: 'bg-rose-50 text-rose-700 border-rose-300',
}

export function FileIntegrityBadge({ status }: { status: FileIntegrityStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${INTEGRITY_STYLES[status]}`}>
      {INTEGRITY_LABELS[status]}
    </span>
  )
}

const CLASSIFICATION_LABELS: Record<FileClassification, string> = {
  INTERNAL: 'Interno',
  CONFIDENTIAL: 'Confidencial',
  RESTRICTED: 'Restringido',
  HIGHLY_RESTRICTED: 'Altamente restringido',
  PUBLIC_APPROVED: 'Público aprobado',
}

const CLASSIFICATION_STYLES: Record<FileClassification, string> = {
  INTERNAL: 'bg-slate-50 text-slate-700 border-slate-300',
  CONFIDENTIAL: 'bg-amber-50 text-amber-700 border-amber-300',
  RESTRICTED: 'bg-orange-50 text-orange-700 border-orange-300',
  HIGHLY_RESTRICTED: 'bg-rose-50 text-rose-700 border-rose-300',
  PUBLIC_APPROVED: 'bg-emerald-50 text-emerald-700 border-emerald-300',
}

export function FileClassificationBadge({ classification }: { classification: FileClassification }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${CLASSIFICATION_STYLES[classification]}`}>
      {CLASSIFICATION_LABELS[classification]}
    </span>
  )
}

const UPLOAD_LABELS: Record<FileUploadStatus, string> = {
  PREPARING: 'Preparando',
  AUTHORIZING: 'Autorizando',
  UPLOADING: 'Cargando',
  PAUSED: 'Pausado',
  RESUMING: 'Reanudando',
  FINALIZING: 'Finalizando',
  ANALYZING: 'Analizando',
  VALIDATING: 'Validando',
  QUARANTINED: 'En cuarentena',
  AVAILABLE: 'Disponible',
  REJECTED: 'Rechazado',
  FAILED: 'Fallido',
  CANCELLED: 'Cancelado',
}

export function FileUploadStatusBadge({ status }: { status: FileUploadStatus }) {
  const style = status === 'AVAILABLE'
    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
    : status === 'QUARANTINED' || status === 'REJECTED' || status === 'FAILED'
      ? 'bg-rose-50 text-rose-700 border-rose-300'
      : status === 'CANCELLED'
        ? 'bg-slate-100 text-slate-400 border-slate-200'
        : 'bg-amber-50 text-amber-700 border-amber-300'
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${style}`}>
      {UPLOAD_LABELS[status]}
    </span>
  )
}

const EVIDENCE_LABELS: Record<EvidenceStatus, string> = {
  DRAFT: 'Borrador',
  PENDING: 'Pendiente',
  ACCEPTED: 'Aceptada',
  REJECTED: 'Rechazada',
  REVOKED: 'Revocada',
  SUPERSEDED: 'Sustituida',
}

const EVIDENCE_STYLES: Record<EvidenceStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 border-slate-300',
  PENDING: 'bg-amber-50 text-amber-700 border-amber-300',
  ACCEPTED: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  REJECTED: 'bg-rose-50 text-rose-700 border-rose-300',
  REVOKED: 'bg-slate-100 text-slate-500 border-slate-300',
  SUPERSEDED: 'bg-slate-100 text-slate-500 border-slate-300',
}

export function EvidenceStatusBadge({ status }: { status: EvidenceStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${EVIDENCE_STYLES[status]}`}>
      {EVIDENCE_LABELS[status]}
    </span>
  )
}

const DELETION_LABELS: Record<FileDeletionRequestStatus, string> = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  PURGED: 'Purgada',
}

export function FileDeletionStatusBadge({ status }: { status: FileDeletionRequestStatus }) {
  const style = status === 'PURGED'
    ? 'bg-slate-100 text-slate-400 border-slate-200'
    : status === 'APPROVED'
      ? 'bg-amber-50 text-amber-700 border-amber-300'
      : status === 'REJECTED'
        ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
        : 'bg-amber-50 text-amber-700 border-amber-300'
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${style}`}>
      {DELETION_LABELS[status]}
    </span>
  )
}

