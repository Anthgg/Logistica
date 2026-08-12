import { useCallback, useEffect, useState } from 'react'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type { EvaluationHistoryEvent } from '../types/evaluation'
import { ErrorState, TableSkeleton, EmptyState } from './ui/SharedState'

export function EvaluationHistoryTimeline({ evaluationId }: { evaluationId: string }) {
  const [events, setEvents] = useState<EvaluationHistoryEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setEvents(await quotationEvaluationsApi.getHistory(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudo cargar el historial.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />
  if (events.length === 0) return <EmptyState title="Sin eventos de historial" />

  return (
    <ol className="space-y-2 border-l border-slate-200 pl-4 text-xs">
      {events.map((e) => (
        <li key={e.id} className="relative">
          <span className="absolute -left-[21px] top-1 h-3 w-3 rounded-full border-2 border-[#1F4E6D] bg-white" />
          <div className="rounded-lg border border-slate-100 bg-white p-2.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800">{e.action}</span>
              <span className="text-[11px] text-slate-400">{new Date(e.occurred_at).toLocaleString('es-PE')}</span>
            </div>
            <dl className="mt-1 grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] text-slate-500 md:grid-cols-4">
              <dt>Actor:</dt><dd>{e.actor_display_name ?? '—'}</dd>
              <dt>Recurso:</dt><dd>{e.resource_type ?? '—'} {e.resource_id ? `· ${e.resource_id.slice(0, 8)}` : ''}</dd>
              <dt>Resultado:</dt><dd>{e.result}</dd>
              <dt>Motivo:</dt><dd>{e.reason ?? '—'}</dd>
              <dt>Corrida:</dt><dd>{e.run_id ?? '—'}</dd>
              <dt>Versión:</dt><dd>{e.version ?? '—'}</dd>
            </dl>
          </div>
        </li>
      ))}
    </ol>
  )
}