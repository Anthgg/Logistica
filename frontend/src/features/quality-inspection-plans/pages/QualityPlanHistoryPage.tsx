import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { QualityPlanHistoryTimeline } from '../components/QualityPlanHistoryTimeline'
import type { QualityPlanHistoryEvent } from '../types/quality-inspection-plans'

export function QualityPlanHistoryPage() {
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()

  const { data: events, isLoading } = useQuery<QualityPlanHistoryEvent[]>(
    ['quality-plan-history', planId],
    `/logistics/quality-inspection-plans/${planId}/history`,
    undefined,
    { enabled: !!planId },
  )

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-bold text-slate-800">Historial del plan</h1>
        <button onClick={() => navigate(-1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">
          Volver
        </button>
      </div>
      {isLoading ? (
        <div className="text-xs text-slate-500">Cargando historial...</div>
      ) : (
        <QualityPlanHistoryTimeline events={events ?? []} />
      )}
    </div>
  )
}
