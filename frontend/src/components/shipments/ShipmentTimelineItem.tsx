import { useState } from 'react'
import { StatusBadge } from '../common/StatusBadge'
import type { ShipmentEvent, ShipmentStatus } from '../../types/operations'
import { formatDateTime } from '../../utils/date'
import { useTranslations } from '../../hooks/useTranslations'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { getShipmentStatusLabel } from '../../features/shipments/shipmentStatusLabels'

const statusDotColors: Record<ShipmentStatus | string, string> = {
  registered: 'bg-slate-400 text-slate-700',
  pending_pickup: 'bg-amber-400 text-amber-700',
  picked_up: 'bg-blue-500 text-blue-700',
  warehouse_received: 'bg-indigo-500 text-indigo-700',
  in_transit: 'bg-purple-500 text-purple-700',
  out_for_delivery: 'bg-sky-500 text-sky-700',
  delivered: 'bg-emerald-500 text-emerald-700',
  delayed: 'bg-rose-500 text-rose-700',
  cancelled: 'bg-slate-500 text-slate-800',
  returned: 'bg-rose-400 text-rose-800',
}

interface Props {
  event: ShipmentEvent
  isLatest: boolean
  isLast: boolean
}

export function ShipmentTimelineItem({ event, isLatest, isLast }: Props) {
  const { language } = useTranslations()
  const [isExpanded, setIsExpanded] = useState(false)
  const descriptionText = event.description ?? 'Cambio de estado operativo.'
  const isLongText = descriptionText.length > 110

  const dotColor = statusDotColors[event.new_status] ?? 'bg-slate-400'
  const newStatusLabel = getShipmentStatusLabel(event.new_status, language, event.new_status_label)
  const prevStatusLabel = event.previous_status
    ? getShipmentStatusLabel(event.previous_status, language, event.previous_status_label)
    : null

  return (
    <li className="relative pl-6 pb-5 last:pb-0">
      {/* Línea conectora vertical */}
      {!isLast && (
        <span
          className="absolute left-[7px] top-3 bottom-0 w-0.5 bg-slate-200"
          aria-hidden="true"
        />
      )}

      {/* Punto de estado */}
      <span
        className={`absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full ring-4 ${
          isLatest ? 'ring-blue-100 animate-pulse' : 'ring-white'
        } ${dotColor}`}
        aria-hidden="true"
      />

      <div className={`flex flex-col gap-1 p-2.5 rounded-xl transition-colors ${isLatest ? 'bg-blue-50/50 border border-blue-100' : ''}`}>
        {/* Fila del encabezado: Badge de Nuevo Estado + Estado Anterior + Fecha */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge value={event.new_status}>
              {newStatusLabel}
            </StatusBadge>
            {prevStatusLabel && (
              <span className="text-[10px] text-slate-400">
                (anterior: <span className="font-medium text-slate-600">{prevStatusLabel}</span>)
              </span>
            )}
            {isLatest && (
              <span className="text-[9px] font-bold uppercase tracking-wider text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded-md">
                Estado Actual
              </span>
            )}
          </div>
          <time className="text-[11px] text-slate-400 font-medium whitespace-nowrap">
            {formatDateTime(event.created_at)}
          </time>
        </div>

        {/* Ubicación */}
        {event.location && (
          <span className="text-[11px] font-semibold text-slate-600 block mt-0.5">
            <LogisticsIcon name="location" size={12} className="inline-block align-middle mr-0.5" aria-hidden /> {event.location}
          </span>
        )}

        {/* Descripción con ver más / ver menos si supera 110 caracteres */}
        <p className={`text-xs text-slate-600 leading-snug mt-0.5 ${!isExpanded && isLongText ? 'line-clamp-3' : ''}`}>
          {descriptionText}
        </p>

        {isLongText && (
          <button
            type="button"
            onClick={() => setIsExpanded((v) => !v)}
            className="text-[11px] font-semibold text-[#1F4E6D] hover:underline w-fit mt-0.5 cursor-pointer bg-transparent border-none p-0"
          >
            {isExpanded ? 'Ver menos' : 'Ver más'}
          </button>
        )}
      </div>
    </li>
  )
}
