import type {
  PurchaseRequisitionPriority,
  PurchaseRequisitionStatus,
} from '../../types/purchase-requisitions'

interface StatusProps {
  status: PurchaseRequisitionStatus
  size?: 'sm' | 'md'
}

interface PriorityProps {
  priority: PurchaseRequisitionPriority
  size?: 'sm' | 'md'
}

const STATUS_CONFIG: Record<PurchaseRequisitionStatus, { label: string; className: string }> = {
  DRAFT: { label: 'Borrador', className: 'bg-slate-100 text-slate-700 border-slate-300' },
  SUBMITTED: { label: 'Enviado', className: 'bg-blue-100 text-blue-800 border-blue-300' },
  UNDER_REVIEW: { label: 'En Revisión', className: 'bg-indigo-100 text-indigo-800 border-indigo-300' },
  RETURNED: { label: 'Devuelto para Cambios', className: 'bg-amber-100 text-amber-800 border-amber-300' },
  APPROVED: { label: 'Aprobado', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  REJECTED: { label: 'Rechazado', className: 'bg-rose-100 text-rose-800 border-rose-300' },
  WITHDRAWN: { label: 'Retirado', className: 'bg-gray-100 text-gray-700 border-gray-300' },
  CANCELLED: { label: 'Cancelado', className: 'bg-red-100 text-red-800 border-red-300' },
  ARCHIVED: { label: 'Archivado', className: 'bg-slate-200 text-slate-600 border-slate-300' },
}

const PRIORITY_CONFIG: Record<PurchaseRequisitionPriority, { label: string; className: string }> = {
  LOW: { label: 'Baja', className: 'bg-slate-100 text-slate-600 border-slate-300' },
  NORMAL: { label: 'Normal', className: 'bg-blue-100 text-blue-800 border-blue-300' },
  HIGH: { label: 'Alta', className: 'bg-indigo-100 text-indigo-800 border-indigo-300' },
  URGENT: { label: 'Urgente', className: 'bg-amber-100 text-amber-800 border-amber-300 font-bold' },
  CRITICAL: { label: 'Crítica', className: 'bg-rose-100 text-rose-800 border-rose-300 font-bold' },
}

export function RequisitionStatusBadge({ status, size = 'md' }: StatusProps) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, className: 'bg-slate-100 text-slate-600 border-slate-300' }
  const sizeClass = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'

  return (
    <span className={`inline-flex items-center rounded-full font-semibold border ${sizeClass} ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}

export function RequisitionPriorityBadge({ priority, size = 'md' }: PriorityProps) {
  const cfg = PRIORITY_CONFIG[priority] ?? { label: priority, className: 'bg-slate-100 text-slate-600 border-slate-300' }
  const sizeClass = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'

  return (
    <span className={`inline-flex items-center rounded-full font-semibold border ${sizeClass} ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}
