import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { evaluationDecisionsApi } from '../api/evaluationDecisionsApi'
import type {
  EvaluationCapabilities,
  EvaluationDecisionCreate,
  EvaluationDecisionType,
  EvaluationDecisionValidation,
  NoAwardDecisionInput,
  QuotationEvaluation,
  QuotationEvaluationDecision,
  SplitAwardLineInput,
  SplitAwardQuantityInput,
} from '../types/evaluation'
import { decisionTypeLabel, decisionStatusLabel, generateIdempotencyKey } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from '../components/ui/SharedState'
import { Modal } from '../components/ui/Overlay'
import { DecimalInput } from '../components/ui/DecimalInput'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'

const DECISION_TYPES: EvaluationDecisionType[] = [
  'SINGLE_SUPPLIER',
  'SPLIT_BY_LINE',
  'SPLIT_BY_QUANTITY',
  'NO_AWARD',
  'REQUOTE',
  'CLARIFICATION',
  'MANUAL_EXCEPTION',
]

export function EvaluationDecisionPage({
  evaluationId,
  evaluation,
  capabilities,
  onChanged,
}: {
  evaluationId: string
  evaluation: QuotationEvaluation
  capabilities: EvaluationCapabilities
  onChanged: () => void
}) {
  const navigate = useNavigate()
  const permissions = useLogisticsPermissions()
  const [decision, setDecision] = useState<QuotationEvaluationDecision | null>(null)
  const [validation, setValidation] = useState<EvaluationDecisionValidation | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [recordOpen, setRecordOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.supplierEvaluations.recordDecision,
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setDecision(await evaluationDecisionsApi.getActiveDecision(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudo cargar la decisión.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleCreate = async (type: EvaluationDecisionType) => {
    try {
      const payload: EvaluationDecisionCreate = { type }
      const d = await evaluationDecisionsApi.createDecision(evaluationId, payload)
      setDecision(d)
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo crear la decisión.')
    }
  }

  const handleValidate = async () => {
    if (!decision) return
    try {
      setValidation(await evaluationDecisionsApi.validateDecision(evaluationId, decision.id))
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo validar.')
    }
  }

  const handleRecord = async () => {
    if (!decision) return
    setSubmitting(true)
    try {
      const executed = await guard.run(async () => {
        await evaluationDecisionsApi.recordDecision(evaluationId, decision.id, generateIdempotencyKey())
      })
      if (executed) {
        setRecordOpen(false)
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-500">
          Registrar decisión no emite orden de compra ni aprueba gasto. La
          aprobación de gasto posterior es independiente. El registro requiere
          step-up CRITICAL. Evaluación: {evaluation.code}.
        </p>
        {capabilities.can_create_decision && !decision && (
          <Select value="" onValueChange={(v) => void handleCreate(v as EvaluationDecisionType)}>
            <SelectTrigger className="w-[220px]"><SelectValue placeholder="Crear decisión…" /></SelectTrigger>
            <SelectContent>
              {DECISION_TYPES.map((t) => <SelectItem key={t} value={t}>{decisionTypeLabel(t)}</SelectItem>)}
            </SelectContent>
          </Select>
        )}
      </div>

      {!decision ? (
        <EmptyState
          title="Sin decisión creada"
          description="Crea una decisión para registrar la adjudicación o no adjudicación."
        />
      ) : (
        <>
          <div className="rounded-xl border border-slate-200 p-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold">{decisionTypeLabel(decision.type)}</span>
              <StatusPill tone={decision.status === 'RECORDED' ? 'success' : 'info'}>{decisionStatusLabel(decision.status)}</StatusPill>
            </div>
            <dl className="mt-2 grid grid-cols-2 gap-1 md:grid-cols-3">
              <dt className="text-slate-500">Tipo:</dt><dd>{decisionTypeLabel(decision.type)}</dd>
              <dt className="text-slate-500">Líneas:</dt><dd>{decision.lines.length}</dd>
              <dt className="text-slate-500">Total:</dt><dd className="font-mono">{decision.total_amount ?? '—'} {decision.total_currency ?? ''}</dd>
              <dt className="text-slate-500">Aprobación pendiente:</dt><dd>{decision.procurement_approval_pending ? 'Sí' : 'No'}</dd>
              <dt className="text-slate-500">Justificación:</dt><dd>{decision.justification ?? '—'}</dd>
            </dl>
          </div>

          {/* Formas según tipo */}
          {decision.type === 'SINGLE_SUPPLIER' && (
            <SingleSupplierDecisionForm evaluationId={evaluationId} decision={decision} capabilities={capabilities} onChanged={load} />
          )}
          {decision.type === 'SPLIT_BY_LINE' && (
            <SplitAwardByLineEditor evaluationId={evaluationId} decision={decision} onChanged={load} />
          )}
          {decision.type === 'SPLIT_BY_QUANTITY' && (
            <SplitAwardByQuantityEditor evaluationId={evaluationId} decision={decision} onChanged={load} />
          )}
          {decision.type === 'NO_AWARD' && (
            <NoAwardDecisionForm evaluationId={evaluationId} decision={decision} onChanged={load} />
          )}
          {decision.type === 'REQUOTE' && (
            <RequoteDecisionForm evaluationId={evaluationId} decision={decision} onChanged={load} />
          )}

          {/* Validación */}
          <div className="flex items-center gap-2">
            {capabilities.can_record_decision && (
              <button type="button" onClick={handleValidate} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                Validar decisión
              </button>
            )}
            {capabilities.can_record_decision && (
              <button type="button" onClick={() => setRecordOpen(true)} disabled={guard.isBlocked} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
                Registrar decisión
              </button>
            )}
            {decision.status === 'RECORDED' &&
              permissions.hasPermission(
                LOGISTICS_PERMISSIONS.purchaseOrdersV2.generate,
              ) && (
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/logistics/purchasing/purchase-orders/generate?decisionId=${encodeURIComponent(decision.id)}`,
                    )
                  }
                  className="min-h-10 rounded-lg border border-[#1F4E6D]/30 bg-[#1F4E6D]/5 px-3 text-xs font-semibold text-[#1F4E6D] hover:bg-[#1F4E6D]/10"
                >
                  Previsualizar órdenes de compra
                </button>
              )}
          </div>

          {validation && (
            <div className={`rounded-lg border p-3 text-xs ${validation.is_valid ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-rose-200 bg-rose-50 text-rose-700'}`}>
              <div className="font-semibold">{validation.is_valid ? 'Validación OK' : 'Validación con errores'}</div>
              {validation.errors.length > 0 && (
                <ul className="mt-1 list-disc pl-4">{validation.errors.map((e) => <li key={e.code ?? e.message}>{e.message}</li>)}</ul>
              )}
              {validation.warnings.length > 0 && (
                <ul className="mt-1 list-disc pl-4 text-amber-700">{validation.warnings.map((w) => <li key={w.code ?? w.message}>{w.message}</li>)}</ul>
              )}
            </div>
          )}
        </>
      )}

      <Modal
        open={recordOpen}
        onOpenChange={setRecordOpen}
        title="Registrar decisión"
        footer={
          <>
            <button type="button" onClick={() => setRecordOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleRecord} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Registrando…' : 'Registrar'}</button>
          </>
        }
      >
        <div className="space-y-2 text-xs">
          <p className="font-semibold text-slate-700">Resumen</p>
          {decision && (
            <ul className="space-y-1">
              <li>Tipo: {decisionTypeLabel(decision.type)}</li>
              <li>Líneas: {decision.lines.length}</li>
              <li>Total: {decision.total_amount ?? '—'} {decision.total_currency ?? ''}</li>
            </ul>
          )}
          <p className="rounded-lg border border-amber-200 bg-amber-50/50 p-2 text-amber-800">
            Esta acción registra y congela la decisión de evaluación. No emite una
            orden de compra ni aprueba el gasto.
          </p>
        </div>
      </Modal>
    </div>
  )
}

function SingleSupplierDecisionForm({
  evaluationId,
  decision,
  capabilities,
  onChanged,
}: {
  evaluationId: string
  decision: QuotationEvaluationDecision
  capabilities: EvaluationCapabilities
  onChanged: () => void
}) {
  const [justification, setJustification] = useState(decision.justification ?? '')
  const [reasonNotFirst, setReasonNotFirst] = useState(decision.reason_not_first_rank ?? '')
  const [submitting, setSubmitting] = useState(false)

  const handleSave = async () => {
    setSubmitting(true)
    try {
      await evaluationDecisionsApi.updateDecision(evaluationId, decision.id, { justification, reason_not_first_rank: reasonNotFirst || null })
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 p-3 text-xs">
      <p className="font-semibold text-slate-700">Proveedor único</p>
      <p className="mt-1 text-slate-500">No se selecciona automáticamente el primer puesto.</p>
      <div className="mt-2 space-y-2">
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Justificación</label>
          <textarea value={justification} onChange={(e) => setJustification(e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Motivo si no es primer puesto</label>
          <textarea value={reasonNotFirst} onChange={(e) => setReasonNotFirst(e.target.value)} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        {capabilities.can_record_decision && (
          <button type="button" disabled={submitting} onClick={handleSave} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
            {submitting ? 'Guardando…' : 'Guardar'}
          </button>
        )}
      </div>
    </div>
  )
}

function SplitAwardByLineEditor({
  evaluationId,
  decision,
  onChanged,
}: {
  evaluationId: string
  decision: QuotationEvaluationDecision
  onChanged: () => void
}) {
  const [lines, setLines] = useState<SplitAwardLineInput[]>(decision.lines.map((l) => ({
    line_id: l.line_id,
    awarded_candidate_id: l.awarded_candidate_id ?? '',
    awarded_quantity: l.awarded_quantity ?? '',
    reason: l.reason ?? null,
  })))
  const [submitting, setSubmitting] = useState(false)

  const handleSave = async () => {
    setSubmitting(true)
    try {
      await evaluationDecisionsApi.setSplitByLine(evaluationId, decision.id, lines)
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 p-3 text-xs">
      <p className="font-semibold text-slate-700">Dividir por línea</p>
      <p className="mt-1 text-slate-500">El proveedor debe cotizar la línea. No se permite proveedor descalificado. No se crea OC.</p>
      <div className="mt-2 overflow-x-auto rounded-lg border border-slate-100">
        <table className="min-w-full divide-y divide-slate-100">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-2 py-1.5 text-left">Línea</th>
              <th className="px-2 py-1.5 text-left">Producto</th>
              <th className="px-2 py-1.5 text-left">ID candidato</th>
              <th className="px-2 py-1.5 text-right">Cantidad</th>
              <th className="px-2 py-1.5 text-left">Motivo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {decision.lines.map((l, i) => (
              <tr key={l.line_id}>
                <td className="px-2 py-1.5 font-mono">{l.line_id}</td>
                <td className="px-2 py-1.5">{l.product_name}</td>
                <td className="px-2 py-1.5"><input value={lines[i]?.awarded_candidate_id ?? ''} onChange={(e) => setLines((ls) => ls.map((x, idx) => idx === i ? { ...x, awarded_candidate_id: e.target.value } : x))} className="w-full rounded border border-slate-300 px-2 py-1 font-mono text-[11px]" /></td>
                <td className="px-2 py-1.5"><input value={lines[i]?.awarded_quantity ?? ''} onChange={(e) => setLines((ls) => ls.map((x, idx) => idx === i ? { ...x, awarded_quantity: e.target.value } : x))} className="w-24 rounded border border-slate-300 px-2 py-1 text-right font-mono text-[11px]" inputMode="decimal" /></td>
                <td className="px-2 py-1.5"><input value={lines[i]?.reason ?? ''} onChange={(e) => setLines((ls) => ls.map((x, idx) => idx === i ? { ...x, reason: e.target.value || null } : x))} className="w-full rounded border border-slate-300 px-2 py-1 text-[11px]" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button type="button" disabled={submitting} onClick={handleSave} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
        {submitting ? 'Guardando…' : 'Guardar split por línea'}
      </button>
    </div>
  )
}

function SplitAwardByQuantityEditor({
  evaluationId,
  decision,
  onChanged,
}: {
  evaluationId: string
  decision: QuotationEvaluationDecision
  onChanged: () => void
}) {
  const [distributions, setDistributions] = useState<SplitAwardQuantityInput[]>(
    decision.split_distributions.reduce<SplitAwardQuantityInput[]>((acc, d) => {
      const existing = acc.find((a) => a.line_id === d.line_id)
      if (existing) existing.distributions.push({ candidate_id: d.candidate_id, quantity: d.quantity })
      else acc.push({ line_id: d.line_id, distributions: [{ candidate_id: d.candidate_id, quantity: d.quantity }] })
      return acc
    }, []),
  )
  const [submitting, setSubmitting] = useState(false)

  const handleSave = async () => {
    setSubmitting(true)
    try {
      await evaluationDecisionsApi.setSplitByQuantity(evaluationId, decision.id, distributions)
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 p-3 text-xs">
      <p className="font-semibold text-slate-700">Dividir por cantidad</p>
      <p className="mt-1 text-slate-500">Cantidades como strings. El backend valida acumulados y no se supera la cantidad solicitada. No se calculan acumulados como autoridad.</p>
      <div className="mt-2 space-y-2">
        {distributions.map((d, i) => (
          <div key={d.line_id} className="rounded-lg border border-slate-100 p-2">
            <div className="font-mono text-[11px]">Línea {d.line_id}</div>
            {d.distributions.map((dist, j) => (
              <div key={j} className="mt-1 grid grid-cols-2 gap-2">
                <input value={dist.candidate_id} onChange={(e) => setDistributions((ds) => ds.map((x, idx) => idx === i ? { ...x, distributions: x.distributions.map((dd, dj) => dj === j ? { ...dd, candidate_id: e.target.value } : dd) } : x))} className="rounded border border-slate-300 px-2 py-1 font-mono text-[11px]" />
                <DecimalInput value={dist.quantity} onChange={(v) => setDistributions((ds) => ds.map((x, idx) => idx === i ? { ...x, distributions: x.distributions.map((dd, dj) => dj === j ? { ...dd, quantity: v } : dd) } : x))} maxDecimals={4} className="w-32" />
              </div>
            ))}
          </div>
        ))}
      </div>
      <button type="button" disabled={submitting} onClick={handleSave} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
        {submitting ? 'Guardando…' : 'Guardar split por cantidad'}
      </button>
    </div>
  )
}

function NoAwardDecisionForm({
  evaluationId,
  decision,
  onChanged,
}: {
  evaluationId: string
  decision: QuotationEvaluationDecision
  onChanged: () => void
}) {
  const [form, setForm] = useState<NoAwardDecisionInput>({
    reason: '',
    unsatisfied_criteria: [],
    comments: null,
    next_action: null,
    evidence_id: null,
  })
  const [submitting, setSubmitting] = useState(false)

  const REASONS = ['NONE_SUITABLE', 'PRICE_OUT_OF_RANGE', 'TECHNICAL_NON_COMPLIANCE', 'RISK', 'INVALID_ROUND', 'REQUIREMENT_CHANGED', 'OTHER']

  const handleSave = async () => {
    if (!form.reason) { alert('Motivo obligatorio.'); return }
    setSubmitting(true)
    try {
      await evaluationDecisionsApi.setNoAward(evaluationId, decision.id, form)
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 p-3 text-xs">
      <p className="font-semibold text-slate-700">No adjudicar</p>
      <p className="mt-1 text-slate-500">No se crea automáticamente una nueva ronda.</p>
      <div className="mt-2 space-y-2">
        <Select value={form.reason} onValueChange={(v) => setForm({ ...form, reason: v })}>
          <SelectTrigger><SelectValue placeholder="Motivo" /></SelectTrigger>
          <SelectContent>
            {REASONS.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
          </SelectContent>
        </Select>
        <textarea value={form.comments ?? ''} onChange={(e) => setForm({ ...form, comments: e.target.value || null })} rows={2} placeholder="Comentarios" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <input value={form.next_action ?? ''} onChange={(e) => setForm({ ...form, next_action: e.target.value || null })} placeholder="Próxima acción" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      </div>
      <button type="button" disabled={submitting} onClick={handleSave} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
        {submitting ? 'Guardando…' : 'Guardar no adjudicación'}
      </button>
    </div>
  )
}

function RequoteDecisionForm({
  evaluationId,
  decision,
  onChanged,
}: {
  evaluationId: string
  decision: QuotationEvaluationDecision
  onChanged: () => void
}) {
  const [reason, setReason] = useState('')
  const [comments, setComments] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSave = async () => {
    if (!reason.trim()) { alert('Motivo obligatorio.'); return }
    setSubmitting(true)
    try {
      await evaluationDecisionsApi.setRequote(evaluationId, decision.id, { reason: reason.trim(), comments: comments.trim() || null })
      await onChanged()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 p-3 text-xs">
      <p className="font-semibold text-slate-700">Solicitar nueva cotización</p>
      <div className="mt-2 space-y-2">
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} placeholder="Motivo" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <textarea value={comments} onChange={(e) => setComments(e.target.value)} rows={2} placeholder="Comentarios" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      </div>
      <button type="button" disabled={submitting} onClick={handleSave} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
        {submitting ? 'Guardando…' : 'Guardar requote'}
      </button>
    </div>
  )
}
