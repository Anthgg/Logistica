import { clsx } from 'clsx'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { StatusPill, SectionPanel } from './ui/Primitives'
import {
  dockOperationalStatusLabel,
  dockOperationalStatusTone,
  dockTypeLabel,
  formatServerDateTime,
  formatServerTime,
  formatSecondsApprox,
} from '../utils/format'
import type { WarehouseDockSummary } from '../types/inbound-docks'

export function WarehouseDocksBoard({
  docks,
  onSelect,
  selectedId,
  emptyMessage = 'No hay muelles para mostrar.',
}: {
  docks: WarehouseDockSummary[]
  onSelect?: (dock: WarehouseDockSummary) => void
  selectedId?: string
  emptyMessage?: string
}) {
  if (!docks.length) {
    return (
      <SectionPanel title="Vista de muelles" description="Estado operativo por muelle">
        <p className="text-xs text-slate-500">{emptyMessage}</p>
      </SectionPanel>
    )
  }
  return (
    <ul
      className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
      role="list"
      aria-label="Muelles"
    >
      {docks.map((dock) => {
        const occupied = dock.active_assignment_id && dock.occupied_since
        const waitingApprox = dock.occupied_since
          ? Math.max(
              0,
              Math.floor((Date.now() - new Date(dock.occupied_since).getTime()) / 1000),
            )
          : null
        return (
          <li key={dock.id}>
            <button
              type="button"
              onClick={() => onSelect?.(dock)}
              className={clsx(
                'flex w-full flex-col gap-1.5 rounded-xl border bg-white p-3 text-left text-xs shadow-xs transition-shadow hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]',
                selectedId === dock.id ? 'border-[#1F4E6D]' : 'border-slate-200',
              )}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold text-slate-800">{dock.code}</span>
                <span className="text-slate-500">{dock.name}</span>
                <StatusPill tone={dockOperationalStatusTone(dock.operational_status)}>
                  {dockOperationalStatusLabel(dock.operational_status)}
                </StatusPill>
              </div>
              <div className="flex flex-wrap gap-3 text-[11px] text-slate-500">
                <span className="inline-flex items-center gap-1">
                  <LogisticsIcon name="building" size={12} className="text-slate-400" />
                  {dock.warehouse_name}
                </span>
                <span className="inline-flex items-center gap-1">
                  <LogisticsIcon name="sliders" size={12} className="text-slate-400" />
                  {dockTypeLabel(dock.type)}
                </span>
              </div>
              {occupied && (
                <div className="rounded-lg border border-amber-100 bg-amber-50/40 p-2 text-[11px]">
                  <p className="font-semibold text-amber-700">
                    Ocupado — {dock.active_assignment_vehicle_plate ?? 'vehículo sin placa'}
                  </p>
                  <p className="text-amber-700">
                    Desde {formatServerTime(dock.occupied_since)} ({formatSecondsApprox(waitingApprox)})
                  </p>
                </div>
              )}
              <div className="text-[10px] text-slate-400">
                Actualizado {formatServerDateTime(dock.occupied_since ?? new Date().toISOString())}
              </div>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
