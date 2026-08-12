import { useCallback, useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type { EvaluationCapabilities, EvaluationTie, TiePolicy } from '../types/evaluation'
import { tiePolicyLabel } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from './ui/SharedState'
import { Modal } from './ui/Overlay'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

const RESOLUTIONS: TiePolicy[] = ['HIGHEST_TECHNICAL', 'LOWEST_PRICE', 'LOWEST_RISK', 'SHORTEST_DELIVERY', 'REQUOTE']

export function EvaluationTiePanel({
  evaluationId,
  capabilities,
  onChanged,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
  onChanged: () => void
}) {
  const [ties, setTies] = useState<EvaluationTie[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState<EvaluationTie | null>(null)
  const [resolution, setResolution] = useState<TiePolicy | 'MANUAL'>('MANUAL')
  const [reason, setReason] = useState('')
  const [winnerId, setWinnerId] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.supplierEvaluations.calculate,
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setTies(await quotationEvaluationsApi.listTies(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar los empates.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleResolve = async () => {
    if (!active) return
    if (resolution === 'MANUAL' && !reason.trim()) {
      alert('El motivo es obligatorio para una resolución manual.')
      return
    }
    setSubmitting(true)
    try {
      const executed = await guard.run(async () => {
        await quotationEvaluationsApi.resolveTie(evaluationId, {
          tie_id: active.id,
          resolution,
          reason: reason.trim() || null,
          winner_candidate_id: resolution === 'MANUAL' ? winnerId || null : null,
        })
      })
      if (executed) {
        setOpen(false)
        setReason('')
        setWinnerId('')
        await load()
        await onChanged()
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">
        No se ocultan empates. La resolución del backend puede requerir step-up.
      </p>
      {ties.length === 0 ? (
        <EmptyState title="Sin empates" />
      ) : (
        <div className="space-y-2">
          {ties.map((t) => (
            <div key={t.id} className="rounded-xl border border-slate-200 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold">Grupo de empate <span className="font-mono">{t.group_id}</span></span>
                {t.resolved
                  ? <StatusPill tone="success">Resuelto</StatusPill>
                  : t.action_required ? <StatusPill tone="warning">Acción requerida</StatusPill> : <StatusPill tone="muted">Pendiente</StatusPill>}
              </div>
              <div className="mt-1 text-slate-500">Política: {tiePolicyLabel(t.tie_policy)}</div>
              <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-100">
                {t.candidates.map((c) => (
                  <li key={c.candidate_id} className="flex justify-between px-2 py-1">
                    <span>{c.supplier_name}</span>
                    <span className="font-mono">{c.total_score}</span>
                  </li>
                ))}
              </ul>
              {t.resolution && <div className="mt-1 text-emerald-600">Resolución: {t.resolution}</div>}
              {!t.resolved && capabilities.can_record_decision && (
                <button
                  type="button"
                  onClick={() => { setActive(t); setOpen(true); setResolution('MANUAL'); setWinnerId(''); setReason('') }}
                  className="mt-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Resolver empate
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Resolver empate"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleResolve} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Resolviendo…' : 'Resolver'}</button>
          </>
        }
      >
        <div className="space-y-3">
          <Select value={resolution} onValueChange={(v) => setResolution(v as TiePolicy | 'MANUAL')}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {RESOLUTIONS.map((r) => <SelectItem key={r} value={r}>{tiePolicyLabel(r)}</SelectItem>)}
              <SelectItem value="MANUAL">Decisión manual (motivo obligatorio)</SelectItem>
            </SelectContent>
          </Select>
          {resolution === 'MANUAL' && active && (
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Proveedor ganador del desempate</label>
              <Select value={winnerId} onValueChange={setWinnerId}>
                <SelectTrigger><SelectValue placeholder="Selecciona proveedor" /></SelectTrigger>
                <SelectContent>
                  {active.candidates.map((c) => <SelectItem key={c.candidate_id} value={c.candidate_id}>{c.supplier_name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Motivo {resolution === 'MANUAL' && <span className="text-rose-500">*</span>}</label>
            <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
      </Modal>
    </div>
  )
}