import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type {
  EvaluationDecisionType,
  QuotationEvaluation,
  QuotationEvaluationStatus,
  SupplierEvaluationTemplate,
} from '../types/evaluation'
import {
  decisionTypeLabel,
  evaluationStatusLabel,
} from '../format'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui/SharedState'

type TabKey = 'drafts' | 'in_progress' | 'calculated' | 'decided'

const TABS: Array<{ key: TabKey; label: string; statuses: QuotationEvaluationStatus[] }> = [
  { key: 'drafts', label: 'Borradores', statuses: ['DRAFT', 'READY'] },
  { key: 'in_progress', label: 'En progreso', statuses: ['IN_PROGRESS', 'UNDER_REVIEW'] },
  { key: 'calculated', label: 'Calculadas', statuses: ['CALCULATED'] },
  { key: 'decided', label: 'Decididas', statuses: ['DECISION_RECORDED'] },
]

const DECISION_OPTIONS: EvaluationDecisionType[] = [
  'SINGLE_SUPPLIER',
  'SPLIT_BY_LINE',
  'SPLIT_BY_QUANTITY',
  'NO_AWARD',
  'REQUOTE',
  'CLARIFICATION',
  'MANUAL_EXCEPTION',
]

const STATUS_OPTIONS: QuotationEvaluationStatus[] = [
  'DRAFT',
  'READY',
  'IN_PROGRESS',
  'CALCULATED',
  'UNDER_REVIEW',
  'DECISION_RECORDED',
  'SUPERSEDED',
  'CANCELLED',
  'ARCHIVED',
]

export function QuotationEvaluationsPage() {
  const navigate = useNavigate()
  const perms = useLogisticsPermissions()

  const [tab, setTab] = useState<TabKey>('drafts')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 350)
  const [status, setStatus] = useState<QuotationEvaluationStatus | 'ALL'>('ALL')
  const [templateFilter, setTemplateFilter] = useState<string | 'ALL'>('ALL')
  const [decisionFilter, setDecisionFilter] = useState<EvaluationDecisionType | 'ALL'>('ALL')
  const [withTies, setWithTies] = useState(false)
  const [withDisqualified, setWithDisqualified] = useState(false)
  const [withManualScores, setWithManualScores] = useState(false)
  const [withOverrides, setWithOverrides] = useState(false)
  const [currency, setCurrency] = useState<string>('ALL')

  const [page, setPage] = useState(1)
  const [items, setItems] = useState<QuotationEvaluation[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const [templates, setTemplates] = useState<SupplierEvaluationTemplate[]>([])

  const canCreate = perms.hasPermission(
    LOGISTICS_PERMISSIONS.supplierEvaluations.create,
  )

  useEffect(() => {
    supplierEvaluationTemplatesApi
      .list({ page: 1, page_size: 100 })
      .then((res) => setTemplates(res.items ?? []))
      .catch(() => setTemplates([]))
  }, [])

  const load = useMemo(() => {
    return async () => {
      setIsLoading(true)
      setIsError(false)
      try {
        const res = await quotationEvaluationsApi.list({
          search: debouncedSearch || undefined,
          status: status === 'ALL' ? null : status,
          template_id: templateFilter === 'ALL' ? null : templateFilter,
          decision_type: decisionFilter === 'ALL' ? null : decisionFilter,
          with_ties: withTies,
          with_disqualified: withDisqualified,
          with_manual_scores: withManualScores,
          with_overrides: withOverrides,
          currency: currency === 'ALL' ? null : currency,
          tab,
          page,
          page_size: 20,
        })
        setItems(res.items ?? [])
        setTotalPages(res.total_pages ?? 1)
        setTotal(res.total ?? 0)
      } catch (err: unknown) {
        setIsError(true)
        setErrorMessage(
          err instanceof Error ? err.message : 'No se pudieron cargar las evaluaciones.',
        )
      } finally {
        setIsLoading(false)
      }
    }
  }, [
    debouncedSearch,
    status,
    templateFilter,
    decisionFilter,
    withTies,
    withDisqualified,
    withManualScores,
    withOverrides,
    currency,
    tab,
    page,
  ])

  useEffect(() => {
    setPage(1)
  }, [
    debouncedSearch,
    status,
    templateFilter,
    decisionFilter,
    withTies,
    withDisqualified,
    withManualScores,
    withOverrides,
    currency,
    tab,
  ])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">
            Evaluación de proveedores
          </h1>
          <p className="text-xs text-slate-500">
            Compara propuestas, puntúa criterios y registra la decisión. Sin
            emisión de orden de compra ni aprobación de gasto.
          </p>
        </div>
        {canCreate && (
          <button
            type="button"
            onClick={() => navigate('/logistics/purchasing/evaluations/new')}
            className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white shadow-xs hover:bg-[#173a55]"
          >
            Nueva evaluación
          </button>
        )}
      </div>

      {/* Tabs */}
      <div
        role="tablist"
        aria-label="Estado de la evaluación"
        className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1"
      >
        {TABS.map((t) => {
          const active = tab === t.key
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={active}
              type="button"
              onClick={() => setTab(t.key)}
              className={
                active
                  ? 'rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-[#1F4E6D] shadow-xs'
                  : 'rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700'
              }
            >
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Buscador + filtros */}
      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        <div className="flex flex-wrap gap-2">
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por REQ, ronda, evaluación, proveedor, plantilla o CCO"
            aria-label="Buscar evaluaciones"
            className="min-w-[240px] flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />
          <Select
            value={status}
            onValueChange={(v) => setStatus(v as QuotationEvaluationStatus | 'ALL')}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos los estados</SelectItem>
              {STATUS_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>
                  {evaluationStatusLabel(s)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={templateFilter}
            onValueChange={setTemplateFilter}
          >
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Plantilla" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todas las plantillas</SelectItem>
              {templates.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.code} — {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={decisionFilter}
            onValueChange={(v) =>
              setDecisionFilter(v as EvaluationDecisionType | 'ALL')
            }
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Tipo de decisión" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todas las decisiones</SelectItem>
              {DECISION_OPTIONS.map((d) => (
                <SelectItem key={d} value={d}>
                  {decisionTypeLabel(d)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={currency} onValueChange={setCurrency}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Moneda" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todas</SelectItem>
              <SelectItem value="PEN">PEN</SelectItem>
              <SelectItem value="USD">USD</SelectItem>
              <SelectItem value="EUR">EUR</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {[
            { label: 'Con empate', value: withTies, set: setWithTies },
            { label: 'Con descalificados', value: withDisqualified, set: setWithDisqualified },
            { label: 'Con puntajes manuales', value: withManualScores, set: setWithManualScores },
            { label: 'Con overrides', value: withOverrides, set: setWithOverrides },
          ].map((chip) => (
            <label
              key={chip.label}
              className="inline-flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600"
            >
              <input
                type="checkbox"
                checked={chip.value}
                onChange={(e) => chip.set(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D] focus:ring-[#1F4E6D]"
              />
              {chip.label}
            </label>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        {isError ? (
          <div className="p-4">
            <ErrorState message={errorMessage} onRetry={() => void load()} />
          </div>
        ) : isLoading ? (
          <div className="p-4">
            <TableSkeleton />
          </div>
        ) : items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="No hay evaluaciones para los filtros actuales"
              description="Ajusta los filtros o crea una nueva evaluación desde una ronda cerrada."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50/60 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-3 py-2.5 text-left">REQ</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Ronda</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Evaluación</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Plantilla</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Estado</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Candidatos</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Elegibles</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Desc.</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Empates</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Moneda</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Decisión</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Fecha</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50/60">
                    <td className="px-3 py-2 font-mono text-xs">{ev.requisition_code}</td>
                    <td className="px-3 py-2 text-xs">#{ev.round_number}</td>
                    <td className="px-3 py-2 text-xs">
                      <button
                        type="button"
                        onClick={() => navigate(`/logistics/purchasing/evaluations/${ev.id}`)}
                        className="font-semibold text-[#1F4E6D] hover:underline"
                      >
                        {ev.code}
                      </button>
                    </td>
                    <td className="px-3 py-2 text-xs">{ev.template_code}</td>
                    <td className="px-3 py-2">
                      <StatusPill tone={statusTone(ev.status)}>
                        {evaluationStatusLabel(ev.status)}
                      </StatusPill>
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs">{ev.candidates_count}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-emerald-600">{ev.eligible_count}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-rose-600">{ev.disqualified_count}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs">
                      {ev.ties_count > 0 ? (
                        <StatusPill tone="warning">{ev.ties_count}</StatusPill>
                      ) : (
                        '0'
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs">{ev.comparison_currency ?? '—'}</td>
                    <td className="px-3 py-2 text-xs">
                      {ev.decision_type ? (
                        <span className="text-slate-600">
                          {decisionTypeLabel(ev.decision_type)}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-500">
                      {new Date(ev.created_at).toLocaleDateString('es-PE')}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => navigate(`/logistics/purchasing/evaluations/${ev.id}`)}
                        className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>
            {total} resultado(s) · página {page} de {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded-lg border border-slate-200 px-2.5 py-1 font-semibold disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="rounded-lg border border-slate-200 px-2.5 py-1 font-semibold disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function statusTone(
  status: QuotationEvaluationStatus,
): 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'muted' {
  switch (status) {
    case 'DRAFT':
      return 'muted'
    case 'READY':
      return 'info'
    case 'IN_PROGRESS':
      return 'info'
    case 'CALCULATED':
      return 'success'
    case 'UNDER_REVIEW':
      return 'warning'
    case 'DECISION_RECORDED':
      return 'success'
    case 'SUPERSEDED':
      return 'muted'
    case 'CANCELLED':
      return 'danger'
    case 'ARCHIVED':
      return 'muted'
    default:
      return 'neutral'
  }
}