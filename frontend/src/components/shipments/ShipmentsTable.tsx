import { Link } from 'react-router-dom'
import type { Client, Shipment } from '../../types/operations'
import { formatDateTime } from '../../utils/date'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { ShipmentPriorityBadge, ShipmentStatusBadge } from './ShipmentBadges'

interface ShipmentsTableProps {
  shipments: Shipment[]
  clients: Client[]
  isLoading: boolean
}

export function ShipmentsTable({
  shipments,
  clients,
  isLoading,
}: ShipmentsTableProps) {
  const clientMap = new Map<string, Client>()
  for (const c of clients) {
    clientMap.set(c.id, c)
  }

  if (isLoading) {
    return (
      <div className="w-full overflow-hidden rounded-xl border border-slate-200/80 bg-white">
        <div className="divide-y divide-slate-100">
          {[...Array(6)].map((_, idx) => (
            <div key={idx} className="flex items-center gap-4 px-4 py-3.5 animate-pulse">
              <div className="h-4 w-24 rounded bg-slate-200" />
              <div className="h-4 w-32 rounded bg-slate-200" />
              <div className="h-4 w-40 rounded bg-slate-200" />
              <div className="h-4 w-16 rounded bg-slate-200" />
              <div className="h-4 w-20 rounded bg-slate-200" />
              <div className="ml-auto h-7 w-20 rounded bg-slate-200" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (shipments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-200 bg-white p-10 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400 mb-3">
          <LogisticsIcon name="package" size={24} />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">No se encontraron envíos</h3>
        <p className="mt-1 text-xs text-slate-500 max-w-sm">
          Intenta ajustar los criterios de búsqueda o limpia los filtros activos para ver los resultados disponibles.
        </p>
      </div>
    )
  }

  return (
    <div className="w-full overflow-hidden rounded-xl border border-slate-200/90 bg-white shadow-2xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200/80 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th scope="col" className="px-4 py-3">Envío</th>
              <th scope="col" className="px-4 py-3">Cliente</th>
              <th scope="col" className="px-4 py-3">Trayecto</th>
              <th scope="col" className="px-4 py-3">Prioridad</th>
              <th scope="col" className="px-4 py-3">Estado</th>
              <th scope="col" className="px-4 py-3">Registro</th>
              <th scope="col" className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {shipments.map((item) => {
              const client = clientMap.get(item.client_id)
              return (
                <tr key={item.id} className="group transition-colors hover:bg-slate-50/70">
                  {/* Envío */}
                  <td className="px-4 py-3.5 align-middle">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-[#1F4E6D]">
                        <LogisticsIcon name="package" size={16} />
                      </div>
                      <div>
                        <Link
                          to={`/shipments/${item.id}`}
                          className="font-bold text-[#173F5F] hover:underline hover:text-blue-700"
                        >
                          {item.tracking_code}
                        </Link>
                        <p className="text-[11px] text-slate-500 font-medium">
                          {item.package_count} {item.package_count === 1 ? 'bulto' : 'bultos'}
                        </p>
                      </div>
                    </div>
                  </td>

                  {/* Cliente */}
                  <td className="px-4 py-3.5 align-middle">
                    <p className="font-semibold text-slate-800">
                      {client?.business_name ?? 'Cliente Desconocido'}
                    </p>
                    {client?.document_number && (
                      <p className="text-[11px] text-slate-500 font-medium">
                        {client.document_type || 'RUC'}: {client.document_number}
                      </p>
                    )}
                  </td>

                  {/* Trayecto */}
                  <td className="px-4 py-3.5 align-middle">
                    <div className="flex items-center gap-1.5 font-medium text-slate-800">
                      <span>{item.origin_district}</span>
                      <LogisticsIcon name="chevron" size={12} className="text-slate-400 shrink-0" />
                      <span>{item.destination_district}</span>
                    </div>
                    {item.package_description && (
                      <p className="text-[11px] text-slate-500 truncate max-w-[200px]">
                        {item.package_description}
                      </p>
                    )}
                  </td>

                  {/* Prioridad */}
                  <td className="px-4 py-3.5 align-middle">
                    <ShipmentPriorityBadge value={item.priority}>
                      {item.priority_label}
                    </ShipmentPriorityBadge>
                  </td>

                  {/* Estado */}
                  <td className="px-4 py-3.5 align-middle">
                    <ShipmentStatusBadge value={item.status}>
                      {item.status_label}
                    </ShipmentStatusBadge>
                  </td>

                  {/* Registro */}
                  <td className="px-4 py-3.5 align-middle text-slate-500 font-medium text-[11px] whitespace-nowrap">
                    {formatDateTime(item.created_at)}
                  </td>

                  {/* Acciones */}
                  <td className="px-4 py-3.5 align-middle text-right">
                    <Link
                      to={`/shipments/${item.id}`}
                      className="inline-flex items-center gap-1 h-8 px-2.5 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-[#1F4E6D] shadow-2xs transition-colors hover:bg-slate-50 hover:border-slate-300"
                    >
                      <span>Ver detalle</span>
                    </Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
