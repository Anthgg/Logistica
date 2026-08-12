import { Link } from 'react-router-dom'
import type { DockAssignmentPreparation } from '../types/gate-control'
import { EmptyState } from './ui'

export function DockAssignmentPreparationPanel({
  preparation,
  queueEntryId,
}: {
  preparation: DockAssignmentPreparation | null
  queueEntryId?: string | null
}) {
  if (!preparation) return <EmptyState title="Sin preparación disponible" />
  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
        <h2 className="text-sm font-bold text-slate-800">Preparación para asignación de muelle</h2>
        <dl className="mt-2 grid grid-cols-2 gap-1 md:grid-cols-3">
          <dt className="text-slate-500">CPV:</dt><dd className="font-mono">{preparation.cpv_code ?? '—'}</dd>
          <dt className="text-slate-500">CIT:</dt><dd className="font-mono">{preparation.cit_code ?? '—'}</dd>
          <dt className="text-slate-500">Almacén:</dt><dd>{preparation.warehouse_name}</dd>
          <dt className="text-slate-500">Gate:</dt><dd>{preparation.gate_name ?? '—'}</dd>
          <dt className="text-slate-500">Proveedor:</dt><dd>{preparation.supplier_name ?? '—'}</dd>
          <dt className="text-slate-500">Placa:</dt><dd className="font-mono">{preparation.vehicle_plate ?? '—'}</dd>
          <dt className="text-slate-500">Conductor:</dt><dd>{preparation.driver_name_redacted ?? '—'}</dd>
          <dt className="text-slate-500">Llegada:</dt><dd>{preparation.arrived_at ?? '—'}</dd>
          <dt className="text-slate-500">Decisión:</dt><dd>{preparation.decision_type ?? '—'}</dd>
          <dt className="text-slate-500">Precinto:</dt><dd className="font-mono">{preparation.seal_number ?? '—'}</dd>
          <dt className="text-slate-500">Pallets:</dt><dd>{preparation.pallets ?? '—'}</dd>
          <dt className="text-slate-500">Bultos:</dt><dd>{preparation.packages ?? '—'}</dd>
        </dl>
        {preparation.conditions && <div className="mt-2"><span className="text-slate-500">Condiciones:</span> {preparation.conditions}</div>}
        {preparation.warnings.length > 0 && (
          <ul className="mt-2 list-disc pl-4 text-amber-700">{preparation.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-indigo-100 bg-indigo-50/40 p-3 text-xs text-indigo-700">
        <p>Vehículo liberado por garita. La asignación de muelle y descarga se realizarán en la Fase 038.</p>
        {queueEntryId ? (
          <Link
            to={`/logistics/inbound/docks/queue/${queueEntryId}`}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-[#173a55]"
          >
            Preparar asignación de muelle
          </Link>
        ) : (
          <Link
            to="/logistics/inbound/docks"
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-[#173a55]"
          >
            Ir a muelles de entrada
          </Link>
        )}
      </div>
    </div>
  )
}