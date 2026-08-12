import { useCallback, useEffect, useState } from 'react'
import { evaluationScoresApi } from '../api/evaluationScoresApi'
import type { EvaluationCapabilities, EvaluationScoreOverride, EvaluationOverrideRequest } from '../types/evaluation'
import { overrideStatusLabel } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from './ui/SharedState'
import { Modal } from './ui/Overlay'
import { DecimalInput } from './ui/DecimalInput'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function EvaluationOverridesPanel({
  evaluationId,
  capabilities,
  onChanged,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
  onChanged: () => void
}) {
  const [items, setItems] = useState<EvaluationScoreOverride[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<EvaluationOverrideRequest>({
    candidate_id: '',
    criterion_id: '',
    proposed_score: '',
    reason: '',
    evidence_id: null,
  })
  const [submitting, setSubmitting] = useState(false)

  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.supplierEvaluations.requestOverride,
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setItems(await evaluationScoresApi.listOverrides(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar los overrides.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleRequest = async () => {
    if (!form.candidate_id || !form.criterion_id || !form.proposed_score.trim() || !form.reason.trim()) {
      alert('Todos los campos son obligatorios.')
      return
    }
    setSubmitting(true)
    try {
      const executed = await guard.run(async () => {
        await evaluationScoresApi.requestOverride(evaluationId, form)
      })
      if (executed) {
        setOpen(false)
        setForm({ candidate_id: '', criterion_id: '', proposed_score: '', reason: '', evidence_id: null })
        await load()
        await onChanged()
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleApprove = async (id: string) => {
    try {
      await evaluationScoresApi.approveOverride(evaluationId, id)
      await load()
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo aprobar.')
    }
  }

  const handleReject = async (id: string) => {
    const r = prompt('Motivo de rechazo:') ?? ''
    if (!r.trim()) return
    try {
      await evaluationScoresApi.rejectOverride(evaluationId, id, r)
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo rechazar.')
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          El solicitante no aprueba su propio override si el backend lo prohíbe. El
          ranking no se actualiza hasta que el backend complete una nueva corrida.
        </p>
        {capabilities.can_request_override && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            Solicitar override
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState title="Sin overrides" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Proveedor</th>
                <th className="px-3 py-2.5 text-left">Criterio</th>
                <th className="px-3 py-2.5 text-right">Original</th>
                <th className="px-3 py-2.5 text-right">Propuesto</th>
                <th className="px-3 py-2.5 text-left">Motivo</th>
                <th className="px-3 py-2.5 text-left">Solicitante</th>
                <th className="px-3 py-2.5 text-left">Aprobador</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{o.supplier_name}</td>
                  <td className="px-3 py-2 font-mono">{o.criterion_code}</td>
                  <td className="px-3 py-2 text-right font-mono">{o.original_score}</td>
                  <td className="px-3 py-2 text-right font-mono">{o.proposed_score}</td>
                  <td className="px-3 py-2">{o.reason}</td>
                  <td className="px-3 py-2">{o.requested_by}</td>
                  <td className="px-3 py-2">{o.approved_by ?? '—'}</td>
                  <td className="px-3 py-2"><StatusPill tone={o.status === 'APPROVED' ? 'success' : o.status === 'REJECTED' ? 'danger' : 'warning'}>{overrideStatusLabel(o.status)}</StatusPill></td>
                  <td className="px-3 py-2 text-right">
                    {capabilities.can_approve_override && o.status === 'PENDING' && (
                      <div className="flex justify-end gap-1">
                        <button type="button" onClick={() => void handleApprove(o.id)} className="rounded border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50">Aprobar</button>
                        <button type="button" onClick={() => void handleReject(o.id)} className="rounded border border-rose-200 px-2 py-0.5 text-[11px] font-semibold text-rose-700 hover:bg-rose-50">Rechazar</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Solicitar override"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleRequest} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Guardando…' : 'Solicitar'}</button>
          </>
        }
      >
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">ID candidato</label>
              <input value={form.candidate_id} onChange={(e) => setForm({ ...form, candidate_id: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">ID criterio</label>
              <input value={form.criterion_id} onChange={(e) => setForm({ ...form, criterion_id: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
          </div>
          <DecimalInput label="Puntaje propuesto (string)" value={form.proposed_score} onChange={(v) => setForm({ ...form, proposed_score: v })} maxDecimals={6} />
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Motivo</label>
            <textarea value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} rows={3} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
      </Modal>
    </div>
  )
}