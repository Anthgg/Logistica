import type { PurchaseOrderFulfilment } from '../types/purchase-orders-v2'
import { EmptyState } from './ui'

export function PurchaseOrderFulfilmentPanel({
  fulfilment,
}: {
  fulfilment: PurchaseOrderFulfilment | null
}) {
  if (!fulfilment) return <EmptyState title="Sin información de cumplimiento" />

  const notImplemented = fulfilment.source_status === 'NOT_IMPLEMENTED'

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
        <h2 className="text-sm font-bold text-slate-800">Cumplimiento</h2>
        {notImplemented ? (
          <p className="mt-2 rounded-lg border border-indigo-100 bg-indigo-50/40 p-2 text-indigo-700">
            Recepción aún no implementada. No se muestran cantidades inventadas ni se simula progreso.
          </p>
        ) : (
          <dl className="mt-2 grid grid-cols-2 gap-1">
            <dt className="text-slate-500">Cantidad ordenada:</dt><dd className="font-mono">{fulfilment.ordered_quantity}</dd>
            <dt className="text-slate-500">Cantidad programada:</dt><dd className="font-mono">{fulfilment.scheduled_quantity}</dd>
            <dt className="text-slate-500">Pendiente de programar:</dt><dd className="font-mono">{fulfilment.pending_schedule_quantity}</dd>
            <dt className="text-slate-500">Cantidad recibida:</dt><dd className="font-mono">{fulfilment.received_quantity ?? '—'}</dd>
          </dl>
        )}
        {fulfilment.note && <p className="mt-2 text-[11px] text-slate-500">{fulfilment.note}</p>}
      </div>
    </div>
  )
}