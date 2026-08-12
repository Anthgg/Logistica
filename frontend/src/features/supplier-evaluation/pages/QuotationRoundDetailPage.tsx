import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import type { QuotationEvaluation, QuotationRoundSummary } from '../types/evaluation'
import { roundStatusLabel } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from '../components/ui/SharedState'

/**
 * Vista de detalle de ronda de cotización integrada con evaluación.
 * Permite ver la ronda y crear/ver evaluaciones asociadas.
 * No muestra datos sellados ni crea órdenes de compra.
 */
export function QuotationRoundDetailPage() {
  const { roundId } = useParams<{ roundId: string }>()
  const navigate = useNavigate()
  const perms = useLogisticsPermissions()
  const canCreate = perms.hasPermission(LOGISTICS_PERMISSIONS.supplierEvaluations.create)

  const [round, setRound] = useState<QuotationRoundSummary | null>(null)
  const [evaluations, setEvaluations] = useState<QuotationEvaluation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    if (!roundId) return
    setIsLoading(true)
    setIsError(false)
    try {
      const r = await quotationEvaluationsApi.getRound(roundId)
      setRound(r)
      const evals = await quotationEvaluationsApi.list({ search: r.requisition_code, page: 1, page_size: 50 })
      setEvaluations((evals.items ?? []).filter((e) => e.round_id === roundId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudo cargar la ronda.')
    } finally {
      setIsLoading(false)
    }
  }, [roundId])

  useEffect(() => { void load() }, [load])

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />
  if (!round) return <EmptyState title="Ronda no encontrada" />

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Ronda #{round.round_number}</h1>
          <p className="text-xs text-slate-500">REQ {round.requisition_code}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill tone="info">{roundStatusLabel(round.status)}</StatusPill>
          {canCreate && (
            <button
              type="button"
              onClick={() => navigate(`/logistics/purchasing/evaluations/new`)}
              className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white hover:bg-[#173a55]"
            >
              Crear evaluación
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
        {[
          { label: 'Proveedores', value: round.suppliers_count },
          { label: 'Respuestas válidas', value: round.valid_responses_count },
          { label: 'Monedas', value: round.currencies.join(', ') || '—' },
          { label: 'Apertura', value: round.opening_at ? new Date(round.opening_at).toLocaleDateString('es-PE') : '—' },
        ].map((s) => (
          <div key={s.label} className="rounded-lg border border-slate-200 bg-white p-2.5">
            <div className="text-slate-500">{s.label}</div>
            <div className="mt-0.5 font-mono text-sm font-semibold text-slate-800">{s.value}</div>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-sm font-bold text-slate-800">Evaluaciones</h2>
        {evaluations.length === 0 ? (
          <p className="mt-1 text-xs text-slate-500">No hay evaluaciones creadas para esta ronda.</p>
        ) : (
          <ul className="mt-1 divide-y divide-slate-100 rounded-lg border border-slate-200 text-xs">
            {evaluations.map((e) => (
              <li key={e.id} className="flex items-center justify-between px-2 py-1.5">
                <Link to={`/logistics/purchasing/evaluations/${e.id}`} className="font-semibold text-[#1F4E6D] hover:underline">{e.code}</Link>
                <span>{e.status}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}