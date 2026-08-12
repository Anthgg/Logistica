import { purchaseOrderLinesApi } from '../api/purchaseOrderLinesApi'
import type {
  PurchaseOrderCapabilities,
  PurchaseOrderSourceVariance,
} from '../types/purchase-orders-v2'
import { varianceStatusLabel, varianceTypeLabel } from '../format'
import { EmptyState, StatusPill } from './ui'

export function PurchaseOrderVariancesPanel({
  purchaseOrderId,
  variances,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  variances: PurchaseOrderSourceVariance[]
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const handleApprove = async (id: string) => {
    try { await purchaseOrderLinesApi.approveVariance(purchaseOrderId, id); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo aprobar.') }
  }
  const handleReject = async (id: string) => {
    const r = prompt('Motivo de rechazo:') ?? ''; if (!r.trim()) return
    try { await purchaseOrderLinesApi.rejectVariance(purchaseOrderId, id, r); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo rechazar.') }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">No se ocultan variaciones por pequeñas que sean. El sistema decide tolerancias; el usuario no las desaparece.</p>
      {variances.length === 0 ? (
        <EmptyState title="Sin variaciones" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Tipo</th>
                <th className="px-3 py-2.5 text-left">Línea</th>
                <th className="px-3 py-2.5 text-right">Original</th>
                <th className="px-3 py-2.5 text-right">Propuesto</th>
                <th className="px-3 py-2.5 text-right">Impacto</th>
                <th className="px-3 py-2.5 text-left">Motivo</th>
                <th className="px-3 py-2.5 text-left">Evidencia</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {variances.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{varianceTypeLabel(v.type)}</td>
                  <td className="px-3 py-2 font-mono">{v.line_id ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{v.original_value}</td>
                  <td className="px-3 py-2 text-right font-mono">{v.proposed_value}</td>
                  <td className="px-3 py-2 text-right font-mono">{v.impact}</td>
                  <td className="px-3 py-2">{v.reason ?? '—'}</td>
                  <td className="px-3 py-2">{v.evidence_name ?? '—'}</td>
                  <td className="px-3 py-2"><StatusPill tone={v.status === 'APPROVED' ? 'success' : v.status === 'REJECTED' ? 'danger' : v.status === 'JUSTIFIED' ? 'info' : 'warning'}>{varianceStatusLabel(v.status)}</StatusPill></td>
                  <td className="px-3 py-2 text-right">
                    {capabilities.can_approve_transitional && v.status !== 'APPROVED' && v.status !== 'REJECTED' && (
                      <div className="flex justify-end gap-1">
                        <button type="button" onClick={() => void handleApprove(v.id)} className="rounded border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50">Aprobar</button>
                        <button type="button" onClick={() => void handleReject(v.id)} className="rounded border border-rose-200 px-2 py-0.5 text-[11px] font-semibold text-rose-700 hover:bg-rose-50">Rechazar</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}