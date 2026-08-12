import { LogisticsIcon } from '../common/LogisticsIcon'
import { PriorityBadge, StatusBadge } from '../common/StatusBadge'
import { ShipmentRoute } from './ShipmentRoute'
import type { Shipment } from '../../types/operations'
import { formatDateTime } from '../../utils/date'

interface Props {
  shipment: Shipment
  language: string
}

export function ShipmentInformationCard({ shipment, language }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs flex flex-col gap-4">
      {/* Header de la tarjeta */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#1F4E6D]">
            <LogisticsIcon name="truck" size={18} />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 leading-tight">
              Información del envío
            </h2>
            <p className="text-[11px] text-slate-500 leading-none mt-0.5">
              Datos principales del despacho
            </p>
          </div>
        </div>
        <StatusBadge value={shipment.status}>{shipment.status_label}</StatusBadge>
      </div>

      {/* Visual de ruta */}
      <ShipmentRoute
        originAddress={shipment.origin_address}
        originDistrict={shipment.origin_district}
        destinationAddress={shipment.destination_address}
        destinationDistrict={shipment.destination_district}
      />

      {/* Grilla de datos secundarios sin líneas tradicionales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-50 p-2.5">
          <span className="block text-[11px] font-semibold text-slate-500">
            Contenido
          </span>
          <p className="text-xs font-semibold text-slate-900 mt-0.5">
            {shipment.package_description}
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-2.5">
          <span className="block text-[11px] font-semibold text-slate-500">
            Bultos / Peso total
          </span>
          <p className="text-xs font-semibold text-slate-900 mt-0.5">
            {shipment.package_count} ud. / {Number(shipment.total_weight).toLocaleString(language)} kg
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-2.5">
          <span className="block text-[11px] font-semibold text-slate-500">
            Prioridad asignada
          </span>
          <div className="mt-1">
            <PriorityBadge value={shipment.priority}>
              {shipment.priority_label}
            </PriorityBadge>
          </div>
        </div>

        <div className="rounded-lg bg-slate-50 p-2.5">
          <span className="block text-[11px] font-semibold text-slate-500">
            Valor declarado
          </span>
          <p className="text-xs font-semibold text-slate-900 mt-0.5">
            {shipment.declared_value !== null
              ? `S/ ${Number(shipment.declared_value).toLocaleString(language, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`
              : 'No especificado'}
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-2.5 sm:col-span-2">
          <span className="block text-[11px] font-semibold text-slate-500">
            Entrega esperada
          </span>
          <p className="text-xs font-semibold text-slate-900 mt-0.5">
            {formatDateTime(shipment.expected_delivery_at)}
          </p>
        </div>
      </div>
    </div>
  )
}
