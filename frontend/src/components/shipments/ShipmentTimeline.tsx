import { LogisticsIcon } from '../common/LogisticsIcon'
import { ShipmentTimelineItem } from './ShipmentTimelineItem'
import type { ShipmentEvent } from '../../types/operations'

interface Props {
  events: ShipmentEvent[]
}

export function ShipmentTimeline({ events }: Props) {
  // Ordenar cronológicamente si es necesario (el más reciente primero)
  const sortedEvents = events.toSorted(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs flex flex-col gap-4">
      {/* Header de la tarjeta */}
      <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
          <LogisticsIcon name="activity" size={18} />
        </span>
        <div>
          <h2 className="text-sm font-semibold text-slate-900 leading-tight">
            Línea de tiempo
          </h2>
          <p className="text-[11px] text-slate-500 leading-none mt-0.5">
            Trazabilidad histórica de cambios de estado
          </p>
        </div>
      </div>

      {/* Lista de eventos */}
      {sortedEvents.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center text-slate-400">
          <LogisticsIcon name="activity" size={24} />
          <p className="text-xs">Sin eventos de trazabilidad registrados.</p>
        </div>
      ) : (
        <ol className="mt-1">
          {sortedEvents.map((event, index) => (
            <ShipmentTimelineItem
              key={event.id}
              event={event}
              isLatest={index === 0}
              isLast={index === sortedEvents.length - 1}
            />
          ))}
        </ol>
      )}
    </div>
  )
}
