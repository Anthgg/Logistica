import { PriorityBadge, StatusBadge } from '../common/StatusBadge'
import type { Shipment } from '../../types/operations'
import { formatDateTime } from '../../utils/date'

interface Props {
  shipment: Shipment
  language: string
}

export function ShipmentSummary({ shipment, language }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 mb-5">
      {/* Estado */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs">
        <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
          Estado
        </span>
        <div>
          <StatusBadge value={shipment.status}>{shipment.status_label}</StatusBadge>
        </div>
      </div>

      {/* Prioridad */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs">
        <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
          Prioridad
        </span>
        <div>
          <PriorityBadge value={shipment.priority}>{shipment.priority_label}</PriorityBadge>
        </div>
      </div>

      {/* Bultos */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs">
        <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
          Bultos
        </span>
        <span className="text-sm font-bold text-slate-900">
          {shipment.package_count} ud.
        </span>
      </div>

      {/* Peso */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs">
        <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
          Peso
        </span>
        <span className="text-sm font-bold text-slate-900">
          {Number(shipment.total_weight).toLocaleString(language)} kg
        </span>
      </div>

      {/* Valor Declarado */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs">
        <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
          Valor declarado
        </span>
        <span className="text-sm font-bold text-slate-900">
          {shipment.declared_value !== null
            ? `S/ ${Number(shipment.declared_value).toLocaleString(language, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`
            : 'No declarado'}
        </span>
      </div>

      {/* Entrega Estimada */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs">
        <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
          Entrega estimada
        </span>
        <span className="text-xs font-semibold text-slate-800 truncate block">
          {formatDateTime(shipment.expected_delivery_at)}
        </span>
      </div>
    </div>
  )
}
