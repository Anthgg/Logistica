import { Link } from 'react-router-dom'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { StatusBadge } from '../common/StatusBadge'
import type { ShipmentStatus } from '../../types/operations'

interface Props {
  trackingCode: string
  status: ShipmentStatus
  statusLabel?: string
  canChangeStatus: boolean
  hasAvailableTransitions: boolean
  onChangeStatus: () => void
}

export function ShipmentHeader({
  trackingCode,
  status,
  statusLabel,
  canChangeStatus,
  hasAvailableTransitions,
  onChangeStatus,
}: Props) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200/80 pb-5 mb-5">
      <div className="flex flex-col gap-1">
        <Link
          to="/shipments"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-[#1F4E6D] transition-colors mb-1 w-fit"
        >
          <LogisticsIcon name="chevron" size={13} className="rotate-180 text-slate-400" />
          Volver a envíos
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none">
            DETALLE DEL ENVÍO
          </p>
          <StatusBadge value={status}>{statusLabel}</StatusBadge>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[#172033] font-mono leading-tight">
          {trackingCode}
        </h1>
        <p className="text-xs text-slate-500 leading-snug">
          Información operativa y trazabilidad consolidada del despacho.
        </p>
      </div>

      {canChangeStatus && hasAvailableTransitions && (
        <button
          type="button"
          onClick={onChangeStatus}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-[10px] bg-[#1F4E6D] px-4 text-sm font-medium text-white shadow-xs transition-colors hover:bg-[#173E58] focus-visible:outline-2 focus-visible:outline-[#1F4E6D] focus-visible:outline-offset-2 shrink-0 cursor-pointer border-none"
        >
          <LogisticsIcon name="activity" size={16} />
          Cambiar estado
        </button>
      )}
    </header>
  )
}
