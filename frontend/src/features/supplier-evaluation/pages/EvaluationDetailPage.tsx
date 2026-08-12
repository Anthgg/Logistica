import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type {
  EvaluationCapabilities,
  QuotationEvaluation,
  QuotationEvaluationCandidate,
} from '../types/evaluation'
import { evaluationStatusLabel } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from '../components/ui/SharedState'
import { EvaluationCandidatesPanel } from '../components/EvaluationCandidatesPanel'
import { EvaluationCurrencySection } from '../components/EvaluationCurrencySection'
import { TechnicalEvaluationMatrix } from '../components/TechnicalEvaluationMatrix'
import { ManualScoresPanel } from '../components/ManualScoresPanel'
import { CalculateEvaluationDialog } from '../components/CalculateEvaluationDialog'
import { EvaluationRunStatus } from '../components/EvaluationRunStatus'
import { SupplierComparisonMatrixPanel } from '../components/SupplierComparisonMatrixPanel'
import { EvaluationRankingPanel } from '../components/EvaluationRankingPanel'
import { EvaluationTiePanel } from '../components/EvaluationTiePanel'
import { CandidateDisqualificationPanel } from '../components/CandidateDisqualificationPanel'
import { EvaluationOverridesPanel } from '../components/EvaluationOverridesPanel'
import { EvaluationHistoryTimeline } from '../components/EvaluationHistoryTimeline'
import { ComparativeDocumentPanel } from '../components/ComparativeDocumentPanel'
import { EvaluationExportsPanel } from '../components/EvaluationExportsPanel'
import { EvaluationDecisionPage } from '../pages/EvaluationDecisionPage'

type Tab =
  | 'overview'
  | 'candidates'
  | 'currency'
  | 'technical'
  | 'manual'
  | 'calculate'
  | 'comparison'
  | 'ranking'
  | 'ties'
  | 'disqualifications'
  | 'overrides'
  | 'decision'
  | 'document'
  | 'exports'
  | 'history'

const TABS: Array<{ key: Tab; label: string }> = [
  { key: 'overview', label: 'Resumen' },
  { key: 'candidates', label: 'Candidatos' },
  { key: 'currency', label: 'Moneda' },
  { key: 'technical', label: 'Técnica' },
  { key: 'manual', label: 'Puntajes manuales' },
  { key: 'calculate', label: 'Cálculo' },
  { key: 'comparison', label: 'Comparación' },
  { key: 'ranking', label: 'Ranking' },
  { key: 'ties', label: 'Empates' },
  { key: 'disqualifications', label: 'Descalificaciones' },
  { key: 'overrides', label: 'Overrides' },
  { key: 'decision', label: 'Decisión' },
  { key: 'document', label: 'CCO' },
  { key: 'exports', label: 'Exportaciones' },
  { key: 'history', label: 'Historial' },
]

export function EvaluationDetailPage({
  initialTab = 'overview',
}: {
  initialTab?: Tab
} = {}) {
  const { evaluationId } = useParams<{ evaluationId: string }>()
  const [tab, setTab] = useState<Tab>(initialTab)
  const [evaluation, setEvaluation] = useState<QuotationEvaluation | null>(null)
  const [capabilities, setCapabilities] = useState<EvaluationCapabilities | null>(null)
  const [candidates, setCandidates] = useState<QuotationEvaluationCandidate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const load = async () => {
    if (!evaluationId) return
    setIsLoading(true)
    setIsError(false)
    try {
      const [ev, caps, cands] = await Promise.all([
        quotationEvaluationsApi.get(evaluationId),
        quotationEvaluationsApi.getCapabilities(evaluationId),
        quotationEvaluationsApi.getCandidates(evaluationId),
      ])
      setEvaluation(ev)
      setCapabilities(caps)
      setCandidates(cands)
    } catch (err: unknown) {
      setIsError(true)
      setErrorMessage(err instanceof Error ? err.message : 'No se pudo cargar la evaluación.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evaluationId])

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={errorMessage} onRetry={() => void load()} />
  if (!evaluation || !capabilities)
    return <EmptyState title="Evaluación no encontrada" />

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">{evaluation.code}</h1>
          <p className="text-xs text-slate-500">
            REQ {evaluation.requisition_code} · Ronda #{evaluation.round_number} · {evaluation.template_code} v{evaluation.template_version}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill tone="info">{evaluationStatusLabel(evaluation.status)}</StatusPill>
          {evaluation.has_ties && <StatusPill tone="warning">Con empate</StatusPill>}
          {evaluation.has_disqualifications && <StatusPill tone="danger">Con descalificados</StatusPill>}
        </div>
      </div>

      {/* Resumen compacto */}
      {tab === 'overview' && (
        <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
          {[
            { label: 'Candidatos', value: evaluation.candidates_count },
            { label: 'Elegibles', value: evaluation.eligible_count },
            { label: 'Descalificados', value: evaluation.disqualified_count },
            { label: 'Empates', value: evaluation.ties_count },
            { label: 'Moneda comparación', value: evaluation.comparison_currency ?? '—' },
            { label: 'Puntajes manuales', value: evaluation.has_manual_scores ? 'Sí' : 'No' },
            { label: 'Overrides', value: evaluation.has_overrides ? 'Sí' : 'No' },
            { label: 'CCO', value: evaluation.cco_code ?? '—' },
          ].map((s) => (
            <div key={s.label} className="rounded-lg border border-slate-200 bg-white p-2.5">
              <div className="text-slate-500">{s.label}</div>
              <div className="mt-0.5 font-mono text-sm font-semibold text-slate-800">{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={
              tab === t.key
                ? 'rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-[#1F4E6D] shadow-xs'
                : 'rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700'
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600">
          <p>
            Esta evaluación no emite orden de compra ni aprueba gasto. El ranking
            y los puntajes son autoritativos del backend. Las cifras se muestran
            con permiso y no se almacenan localmente.
          </p>
        </div>
      )}
      {tab === 'candidates' && (
        <EvaluationCandidatesPanel evaluationId={evaluation.id} candidates={candidates} capabilities={capabilities} />
      )}
      {tab === 'currency' && <EvaluationCurrencySection evaluationId={evaluation.id} />}
      {tab === 'technical' && <TechnicalEvaluationMatrix evaluationId={evaluation.id} candidates={candidates} capabilities={capabilities} />}
      {tab === 'manual' && <ManualScoresPanel evaluationId={evaluation.id} candidates={candidates} capabilities={capabilities} />}
      {tab === 'calculate' && (
        <>
          <CalculateEvaluationDialog evaluationId={evaluation.id} capabilities={capabilities} onChanged={load} />
          <EvaluationRunStatus evaluationId={evaluation.id} />
        </>
      )}
      {tab === 'comparison' && <SupplierComparisonMatrixPanel evaluationId={evaluation.id} capabilities={capabilities} />}
      {tab === 'ranking' && <EvaluationRankingPanel evaluationId={evaluation.id} capabilities={capabilities} />}
      {tab === 'ties' && <EvaluationTiePanel evaluationId={evaluation.id} capabilities={capabilities} onChanged={load} />}
      {tab === 'disqualifications' && (
        <CandidateDisqualificationPanel evaluationId={evaluation.id} candidates={candidates} capabilities={capabilities} onChanged={load} />
      )}
      {tab === 'overrides' && <EvaluationOverridesPanel evaluationId={evaluation.id} capabilities={capabilities} onChanged={load} />}
      {tab === 'decision' && <EvaluationDecisionPage evaluationId={evaluation.id} evaluation={evaluation} capabilities={capabilities} onChanged={load} />}
      {tab === 'document' && <ComparativeDocumentPanel evaluationId={evaluation.id} capabilities={capabilities} />}
      {tab === 'exports' && <EvaluationExportsPanel evaluationId={evaluation.id} capabilities={capabilities} />}
      {tab === 'history' && <EvaluationHistoryTimeline evaluationId={evaluation.id} />}
    </div>
  )
}
