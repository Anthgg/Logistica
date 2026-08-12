import { clsx } from 'clsx'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { StatusPill, EmptyPanel, SectionPanel } from './ui/Primitives'
import {
  formatServerTime,
  formatSecondsApprox,
  priorityLabel,
  priorityTone,
  queueStatusLabel,
  queueStatusTone,
} from '../utils/format'
import type { InboundDockQueueEntry } from '../types/inbound-docks'

export function InboundDockQueueTable({
  entries,
  onSelect,
  selectedId,
  capabilities,
  onChangePriority,
}: {
  entries: InboundDockQueueEntry[]
  onSelect?: (entry: InboundDockQueueEntry) => void
  selectedId?: string
  capabilities?: {
    can_change_priority?: boolean
  } | null
  onChangePriority?: (entry: InboundDockQueueEntry) => void
}) {
  if (!entries.length) {
    return (
      <SectionPanel
        title="Cola de vehículos"
        description="Vehículos autorizados esperando asignación de muelle."
      >
        <EmptyPanel
          title="Sin vehículos en cola"
          description="No hay entradas pendientes. Cuando se autorice un vehículo, aparecerá aquí."
        />
      </SectionPanel>
    )
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="w-full min-w-[960px] border-collapse text-left text-xs">
        <thead>
          <tr className="bg-slate-50 text-slate-500">
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Pos.</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Prioridad</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">CPV</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">CIT</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Proveedor</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Transportista</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Placa</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Vehículo</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Gate clearance</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Esperando</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Ventana CIT</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Compatibles</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase">Estado</th>
            <th className="px-3 py-2 text-[10px] font-semibold uppercase text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr
              key={e.id}
              className={clsx(
                'border-t border-slate-100 hover:bg-slate-50/60',
                selectedId === e.id && 'bg-slate-50',
              )}
            >
              <td className="px-3 py-2 font-mono font-bold text-slate-800">{e.position}</td>
              <td className="px-3 py-2">
                <StatusPill tone={priorityTone(e.priority)}>{priorityLabel(e.priority)}</StatusPill>
              </td>
              <td className="px-3 py-2 font-mono text-slate-800">{e.cpv_code ?? '—'}</td>
              <td className="px-3 py-2 font-mono text-slate-800">{e.cit_code ?? '—'}</td>
              <td className="px-3 py-2">{e.supplier_name ?? '—'}</td>
              <td className="px-3 py-2">{e.carrier_name ?? '—'}</td>
              <td className="px-3 py-2 font-mono text-slate-800">{e.vehicle_plate ?? '—'}</td>
              <td className="px-3 py-2">{e.vehicle_type ?? '—'}</td>
              <td className="px-3 py-2 font-mono text-slate-700">
                {e.gate_clearance_at ? formatServerTime(e.gate_clearance_at) : '—'}
              </td>
              <td className="px-3 py-2 font-mono text-slate-700">
                {e.waiting_seconds != null ? formatSecondsApprox(e.waiting_seconds) : '—'}
              </td>
              <td className="px-3 py-2 font-mono text-slate-700">
                {e.cit_window_start && e.cit_window_end
                  ? `${formatServerTime(e.cit_window_start)} – ${formatServerTime(e.cit_window_end)}`
                  : '—'}
              </td>
              <td className="px-3 py-2">
                {e.compatible_dock_ids?.length ? (
                  <span className="text-[11px] text-slate-600">
                    {e.compatible_dock_ids.length} muelle(s)
                  </span>
                ) : (
                  <span className="text-[11px] text-slate-400">—</span>
                )}
              </td>
              <td className="px-3 py-2">
                <StatusPill tone={queueStatusTone(e.status)}>{queueStatusLabel(e.status)}</StatusPill>
                {e.alerts?.length > 0 && (
                  <p className="mt-1 inline-flex items-center gap-1 text-[10px] text-amber-700">
                    <LogisticsIcon name="alert" size={11} className="text-amber-600" /> {e.alerts.length} alerta(s)
                  </p>
                )}
              </td>
              <td className="px-3 py-2 text-right">
                <div className="flex justify-end gap-1">
                  {onChangePriority && capabilities?.can_change_priority && (
                    <button
                      type="button"
                      onClick={() => onChangePriority(e)}
                      className="rounded-md border border-slate-200 px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
                    >
                      Prioridad
                    </button>
                  )}
                  {onSelect && (
                    <button
                      type="button"
                      onClick={() => onSelect(e)}
                      className="rounded-md bg-[#1F4E6D] px-2 py-1 text-[11px] font-semibold text-white hover:bg-[#173a55]"
                    >
                      Detalle
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
