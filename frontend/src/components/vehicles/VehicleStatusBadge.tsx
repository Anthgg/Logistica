import type {
  VehicleComplianceStatus,
  VehicleLifecycleStatus,
  VehicleOperationalStatus,
} from '../../types/vehicles'

interface LifecycleProps {
  status: VehicleLifecycleStatus
  size?: 'sm' | 'md'
}

interface OperationalProps {
  status: VehicleOperationalStatus
  size?: 'sm' | 'md'
}

interface ComplianceProps {
  status: VehicleComplianceStatus
  size?: 'sm' | 'md'
}

const LIFECYCLE_CONFIG: Record<VehicleLifecycleStatus, { label: string; className: string }> = {
  DRAFT: { label: 'Borrador', className: 'bg-slate-100 text-slate-600 border-slate-300' },
  ACTIVE: { label: 'Activo', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  INACTIVE: { label: 'Inactivo', className: 'bg-gray-100 text-gray-700 border-gray-300' },
  SUSPENDED: { label: 'Suspendido', className: 'bg-amber-100 text-amber-800 border-amber-300' },
  RETIRED: { label: 'Retirado', className: 'bg-red-100 text-red-800 border-red-300' },
  ARCHIVED: { label: 'Archivado', className: 'bg-slate-200 text-slate-600 border-slate-300' },
}

const OPERATIONAL_CONFIG: Record<VehicleOperationalStatus, { label: string; className: string }> = {
  UNEVALUATED: { label: 'Sin evaluar', className: 'bg-slate-100 text-slate-600 border-slate-300' },
  AVAILABLE: { label: 'Disponible', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  UNAVAILABLE: { label: 'No disponible', className: 'bg-slate-200 text-slate-700 border-slate-300' },
  UNDER_REVIEW: { label: 'En revisión', className: 'bg-blue-100 text-blue-800 border-blue-300' },
  MAINTENANCE: { label: 'Mantenimiento', className: 'bg-indigo-100 text-indigo-800 border-indigo-300' },
  DOCUMENTS_EXPIRED: { label: 'Docs Vencidos', className: 'bg-rose-100 text-rose-800 border-rose-300' },
  DOCUMENTS_INCOMPLETE: { label: 'Docs Incompletos', className: 'bg-amber-100 text-amber-800 border-amber-300' },
  BLOCKED: { label: 'Bloqueado', className: 'bg-red-100 text-red-800 border-red-300' },
  OUT_OF_SERVICE: { label: 'Fuera de Servicio', className: 'bg-gray-200 text-gray-800 border-gray-400' },
  RETIRED: { label: 'Retirado', className: 'bg-red-200 text-red-900 border-red-400' },
}

const COMPLIANCE_CONFIG: Record<VehicleComplianceStatus, { label: string; className: string }> = {
  COMPLIANT: { label: 'Cumple', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  PARTIAL: { label: 'Cumplimiento Parcial', className: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  NON_COMPLIANT: { label: 'No Cumple', className: 'bg-red-100 text-red-800 border-red-300' },
  DOCUMENTS_EXPIRED: { label: 'Docs Vencidos', className: 'bg-rose-100 text-rose-800 border-rose-300' },
  UNDER_REVIEW: { label: 'En Evaluación', className: 'bg-blue-100 text-blue-800 border-blue-300' },
}

export function VehicleLifecycleBadge({ status, size = 'md' }: LifecycleProps) {
  const cfg = LIFECYCLE_CONFIG[status] ?? { label: status, className: 'bg-slate-100 text-slate-600 border-slate-300' }
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'

  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${sizeClass} ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}

export function VehicleOperationalBadge({ status, size = 'md' }: OperationalProps) {
  const cfg = OPERATIONAL_CONFIG[status] ?? { label: status, className: 'bg-slate-100 text-slate-600 border-slate-300' }
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium border ${sizeClass} ${cfg.className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {cfg.label}
    </span>
  )
}

export function VehicleComplianceBadge({ status, size = 'md' }: ComplianceProps) {
  const cfg = COMPLIANCE_CONFIG[status] ?? { label: status, className: 'bg-slate-100 text-slate-600 border-slate-300' }
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'

  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${sizeClass} ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}
