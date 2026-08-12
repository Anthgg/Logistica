import { useCallback, useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { evaluationScoresApi } from '../api/evaluationScoresApi'
import type {
  EvaluationCapabilities,
  ManualEvaluationScore,
  ManualEvaluationScoreInput,
  QuotationEvaluationCandidate,
} from '../types/evaluation'
import { scoreStatusLabel } from '../format'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from './ui/SharedState'
import { Modal } from './ui/Overlay'
import { DecimalInput } from './ui/DecimalInput'

export function ManualScoresPanel({
  evaluationId,
  candidates,
  capabilities,
}: {
  evaluationId: string
  candidates: QuotationEvaluationCandidate[]
  capabilities: EvaluationCapabilities
}) {
  const [scores, setScores] = useState<ManualEvaluationScore[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<ManualEvaluationScoreInput>({
    candidate_id: '',
    criterion_id: '',
    raw_value: '',
    rubric_level_code: null,
    evidence_id: null,
    evidence_required: false,
    reason: null,
    conflict_of_interest_declared: false,
  })
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      const all = await evaluationScoresApi.listScores(evaluationId)
      setScores(all.filter((s) => s.source === 'MANUAL') as ManualEvaluationScore[])
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar los puntajes.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleCreate = async () => {
    if (!form.candidate_id || !form.criterion_id || !form.raw_value.trim()) {
      alert('Proveedor, criterio y valor son obligatorios.')
      return
    }
    if (form.evidence_required && !form.evidence_id) {
      alert('Evidencia obligatoria.')
      return
    }
    setSubmitting(true)
    try {
      await evaluationScoresApi.createManualScore(evaluationId, form)
      setOpen(false)
      setForm({ candidate_id: '', criterion_id: '', raw_value: '', rubric_level_code: null, evidence_id: null, evidence_required: false, reason: null, conflict_of_interest_declared: false })
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo registrar el puntaje.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReview = async (scoreId: string, action: 'accept' | 'reject') => {
    const comment = action === 'reject' ? prompt('Comentario de rechazo:') ?? '' : undefined
    try {
      if (action === 'accept') await evaluationScoresApi.acceptManualScore(evaluationId, scoreId)
      else await evaluationScoresApi.rejectManualScore(evaluationId, scoreId, comment ?? '')
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo revisar.')
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          El puntaje se envía como string. El backend normaliza. No se envía
          weighted_score ni ranking. No se modifica un puntaje ACCEPTED (corrección
          vía nueva versión).
        </p>
        {capabilities.can_create_manual_score && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            Registrar puntaje manual
          </button>
        )}
      </div>

      {scores.length === 0 ? (
        <EmptyState title="Sin puntajes manuales" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Proveedor</th>
                <th className="px-3 py-2.5 text-left">Criterio</th>
                <th className="px-3 py-2.5 text-left">Rúbrica</th>
                <th className="px-3 py-2.5 text-right">Valor</th>
                <th className="px-3 py-2.5 text-right">Puntaje</th>
                <th className="px-3 py-2.5 text-left">Evidencia</th>
                <th className="px-3 py-2.5 text-left">Motivo</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scores.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2">{s.supplier_name}</td>
                  <td className="px-3 py-2"><span className="font-mono">{s.criterion_code}</span> · {s.criterion_name}</td>
                  <td className="px-3 py-2">{s.formula_label ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{s.original_value ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{s.score ?? '—'}</td>
                  <td className="px-3 py-2">{s.evidence_name ?? '—'}</td>
                  <td className="px-3 py-2">{s.reason ?? '—'}</td>
                  <td className="px-3 py-2"><StatusPill tone={s.status === 'ACCEPTED' ? 'success' : s.status === 'REJECTED' ? 'danger' : 'warning'}>{scoreStatusLabel(s.status)}</StatusPill></td>
                  <td className="px-3 py-2 text-right">
                    {capabilities.can_review_manual_score && s.status === 'SUBMITTED' && (
                      <div className="flex justify-end gap-1">
                        <button type="button" onClick={() => void handleReview(s.id, 'accept')} className="rounded border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50">Aprobar</button>
                        <button type="button" onClick={() => void handleReview(s.id, 'reject')} className="rounded border border-rose-200 px-2 py-0.5 text-[11px] font-semibold text-rose-700 hover:bg-rose-50">Rechazar</button>
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
        title="Puntaje manual"
        size="lg"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Guardando…' : 'Registrar'}</button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Proveedor</label>
            <Select value={form.candidate_id} onValueChange={(v) => setForm({ ...form, candidate_id: v })}>
              <SelectTrigger><SelectValue placeholder="Proveedor" /></SelectTrigger>
              <SelectContent>
                {candidates.map((c) => <SelectItem key={c.id} value={c.id}>{c.supplier_name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Criterio (ID)</label>
              <input value={form.criterion_id} onChange={(e) => setForm({ ...form, criterion_id: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
            <DecimalInput label="Valor (string)" value={form.raw_value} onChange={(v) => setForm({ ...form, raw_value: v })} maxDecimals={6} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Nivel de rúbrica (opcional)</label>
            <input value={form.rubric_level_code ?? ''} onChange={(e) => setForm({ ...form, rubric_level_code: e.target.value || null })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Motivo</label>
            <textarea value={form.reason ?? ''} onChange={(e) => setForm({ ...form, reason: e.target.value || null })} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input type="checkbox" checked={form.evidence_required} onChange={(e) => setForm({ ...form, evidence_required: e.target.checked })} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
            Evidencia requerida
          </label>
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input type="checkbox" checked={form.conflict_of_interest_declared} onChange={(e) => setForm({ ...form, conflict_of_interest_declared: e.target.checked })} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
            Declaro conflicto de interés
          </label>
        </div>
      </Modal>
    </div>
  )
}