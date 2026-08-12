import { useCallback, useEffect, useState } from 'react'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type { EvaluationCapabilities, EvaluationRanking } from '../types/evaluation'
import { ErrorState, StatusPill, TableSkeleton } from './ui/SharedState'

export function EvaluationRankingPanel({
  evaluationId,
  capabilities,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
}) {
  const [ranking, setRanking] = useState<EvaluationRanking | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setRanking(await quotationEvaluationsApi.getRanking(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudo cargar el ranking.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />
  if (!ranking) return <p className="text-xs text-slate-500">Sin ranking calculado.</p>

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">
        El ranking es autoritativo del backend. No se marca automáticamente al
        primer puesto como seleccionado. No hay medallas: es una decisión de compra.
      </p>
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2.5 text-right">Pos.</th>
              <th className="px-3 py-2.5 text-left">Proveedor</th>
              <th className="px-3 py-2.5 text-right">Puntaje</th>
              <th className="px-3 py-2.5 text-right">Cobertura</th>
              <th className="px-3 py-2.5 text-right">Precio comparable</th>
              <th className="px-3 py-2.5 text-right">Plazo (días)</th>
              <th className="px-3 py-2.5 text-left">Riesgo</th>
              <th className="px-3 py-2.5 text-left">Estado</th>
              <th className="px-3 py-2.5 text-left">Empate</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {ranking.entries.map((e) => {
              const showPrice = capabilities.can_view_prices
              return (
                <tr key={e.candidate_id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 text-right font-mono font-semibold">{e.position}</td>
                  <td className="px-3 py-2">{e.supplier_name}</td>
                  <td className="px-3 py-2 text-right font-mono">{e.total_score}</td>
                  <td className="px-3 py-2 text-right font-mono">{e.coverage}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {showPrice ? (e.comparable_price ?? '—') : <span className="text-slate-400">Restringido</span>}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">{e.delivery_days ?? '—'}</td>
                  <td className="px-3 py-2">{e.risk_level}</td>
                  <td className="px-3 py-2">
                    {e.status === 'DISQUALIFIED' ? <StatusPill tone="danger">Descalificado</StatusPill>
                      : e.is_tied ? <StatusPill tone="warning">Empate</StatusPill>
                      : <StatusPill tone="success">Elegible</StatusPill>}
                  </td>
                  <td className="px-3 py-2">
                    {e.is_tied ? <span className="font-mono text-amber-600">{e.tie_group_id ?? '—'}</span> : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}