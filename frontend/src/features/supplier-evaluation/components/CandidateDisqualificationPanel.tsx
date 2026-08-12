import { useCallback, useEffect, useState } from 'react'
import { evaluationScoresApi } from '../api/evaluationScoresApi'
import type {
  CandidateDisqualification,
  EvaluationCapabilities,
  QuotationEvaluationCandidate,
} from '../types/evaluation'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from './ui/SharedState'
import { Modal } from './ui/Overlay'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function CandidateDisqualificationPanel({
  evaluationId,
  candidates,
  capabilities,
  onChanged,
}: {
  evaluationId: string
  candidates: QuotationEvaluationCandidate[]
  capabilities: EvaluationCapabilities
  onChanged: () => void
}) {
  const [items, setItems] = useState<CandidateDisqualification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [candidateId, setCandidateId] = useState('')
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.supplierEvaluations.disqualify,
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setItems(await evaluationScoresApi.listDisqualifications(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las descalificaciones.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleDisqualify = async () => {
    if (!candidateId || !reason.trim()) {
      alert('Proveedor y motivo son obligatorios.')
      return
    }
    setSubmitting(true)
    try {
      const executed = await guard.run(async () => {
        await evaluationScoresApi.disqualify(evaluationId, { candidate_id: candidateId, reason: reason.trim() })
      })
      if (executed) {
        setOpen(false)
        setCandidateId('')
        setReason('')
        await load()
        await onChanged()
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleReverse = async (id: string) => {
    const r = prompt('Motivo de reversión:') ?? ''
    if (!r.trim()) return
    try {
      await evaluationScoresApi.reverseDisqualification(evaluationId, id, r)
      await load()
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo revertir.')
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          No se borra al proveedor del cuadro comparativo. La descalificación puede
          requerir step-up.
        </p>
        {capabilities.can_disqualify && (
          <button type="button" onClick={() => setOpen(true)} disabled={guard.isBlocked} className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50">
            Descalificar proveedor
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState title="Sin descalificaciones" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Proveedor</th>
                <th className="px-3 py-2.5 text-left">Criterio</th>
                <th className="px-3 py-2.5 text-left">Motivo</th>
                <th className="px-3 py-2.5 text-left">Evidencia</th>
                <th className="px-3 py-2.5 text-left">Usuario</th>
                <th className="px-3 py-2.5 text-left">Fecha</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{d.supplier_name}</td>
                  <td className="px-3 py-2 font-mono">{d.criterion_code ?? '—'}</td>
                  <td className="px-3 py-2">{d.reason}</td>
                  <td className="px-3 py-2">{d.evidence_name ?? '—'}</td>
                  <td className="px-3 py-2">{d.disqualified_by}</td>
                  <td className="px-3 py-2">{new Date(d.disqualified_at).toLocaleDateString('es-PE')}</td>
                  <td className="px-3 py-2">
                    {d.status === 'ACTIVE' ? <StatusPill tone="danger">Activa</StatusPill>
                      : d.status === 'REVERTED' ? <StatusPill tone="muted">Revertida</StatusPill>
                      : <StatusPill tone="warning">En revisión</StatusPill>}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {capabilities.can_reverse_disqualification && d.status === 'ACTIVE' && (
                      <button type="button" onClick={() => void handleReverse(d.id)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Revertir</button>
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
        title="Descalificar proveedor"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleDisqualify} className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50">{submitting ? 'Procesando…' : 'Descalificar'}</button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Proveedor</label>
            <select value={candidateId} onChange={(e) => setCandidateId(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="">Selecciona…</option>
              {candidates.map((c) => <option key={c.id} value={c.id}>{c.supplier_name}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Motivo</label>
            <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
      </Modal>
    </div>
  )
}