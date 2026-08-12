import { Link } from 'react-router-dom'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { StatusBadge, PriorityBadge } from '../common/StatusBadge'
import type { Shipment } from '../../types/operations'
import { formatDateTime } from '../../utils/date'

interface Props {
  shipments: Shipment[]
}

export function RecentShipmentsTable({ shipments }: Props) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      {/* Section header */}
      <div className="flex h-12 items-center justify-between border-b border-slate-200 px-4">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-orange-50 text-orange-600" aria-hidden="true">
            <LogisticsIcon name="truck" size={14} />
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none">
              Flujo reciente
            </p>
            <h2 className="text-sm font-semibold text-slate-800 leading-tight">Últimos envíos</h2>
          </div>
        </div>
        <Link
          to="/shipments"
          className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 transition-colors"
        >
          Ver todos <LogisticsIcon name="chevron" size={13} />
        </Link>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        {shipments.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-center text-slate-400">
            <LogisticsIcon name="package" size={28} />
            <p className="text-xs font-medium">No hay envíos recientes</p>
            <p className="text-[10px] text-slate-400">Las operaciones aparecerán aquí</p>
          </div>
        ) : (
          <table className="w-full min-w-[740px] text-left text-xs">
            <thead>
              <tr className="bg-slate-50">
                {['Código', 'Trayecto', 'Prioridad', 'Estado', 'Registro'].map((h) => (
                  <th
                    key={h}
                    scope="col"
                    className="px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500 whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
                <th scope="col" className="w-8 px-2" aria-label="Acciones" />
              </tr>
            </thead>
            <tbody>
              {shipments.map((s) => (
                <tr
                  key={s.id}
                  className="border-t border-slate-100 transition-colors hover:bg-slate-50/80"
                >
                  {/* Código */}
                  <td className="px-4 py-2.5 align-middle">
                    <Link
                      to={`/shipments/${s.id}`}
                      className="block font-bold text-blue-600 hover:text-blue-700 font-mono text-[11px] tracking-wide leading-tight"
                    >
                      {s.tracking_code}
                    </Link>
                    <span className="block text-[10px] text-slate-400 leading-tight max-w-[160px] truncate">
                      {s.package_description}
                    </span>
                  </td>
                  {/* Trayecto */}
                  <td className="px-4 py-2.5 align-middle">
                    <span className="flex items-center gap-1 text-xs text-slate-600 whitespace-nowrap">
                      <span className="text-slate-400">{s.origin_district}</span>
                      <LogisticsIcon name="chevron" size={11} className="text-slate-300 shrink-0" />
                      <span className="font-semibold text-slate-800">{s.destination_district}</span>
                    </span>
                  </td>
                  {/* Prioridad */}
                  <td className="px-4 py-2.5 align-middle">
                    <PriorityBadge value={s.priority}>{s.priority_label}</PriorityBadge>
                  </td>
                  {/* Estado */}
                  <td className="px-4 py-2.5 align-middle">
                    <StatusBadge value={s.status}>{s.status_label}</StatusBadge>
                  </td>
                  {/* Registro */}
                  <td className="px-4 py-2.5 align-middle whitespace-nowrap">
                    <span className="text-[10px] text-slate-400">{formatDateTime(s.created_at)}</span>
                  </td>
                  {/* Acción */}
                  <td className="px-2 py-2.5 align-middle text-slate-300 hover:text-slate-500">
                    <LogisticsIcon name="more" size={14} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
