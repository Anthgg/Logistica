import { useTranslations } from '../../../hooks/useTranslations'
import { formatDateTime } from '../../../utils/date'
import type {
  AdminEvaluationDetail,
  RiskHistoryEntry,
} from '../types/continuous-auth'
import { RiskLevelBadge } from './RiskLevelBadge'

function availableTimeline(
  detail: AdminEvaluationDetail,
): RiskHistoryEntry[] {
  if (detail.risk_history && detail.risk_history.length > 0) {
    return detail.risk_history
  }

  return [
    {
      id: detail.id,
      risk_level: detail.risk_level,
      authentication_level: detail.authentication_level,
      recommended_action: detail.recommended_action,
      applied_action: detail.applied_action,
      evaluated_at: detail.evaluated_at,
    },
  ]
}

export function RiskTimeline({
  detail,
}: {
  detail: AdminEvaluationDetail
}) {
  const { translate } = useTranslations()
  const entries = availableTimeline(detail)

  return (
    <section
      className="rounded-2xl border border-slate-200 bg-white p-5"
      aria-labelledby="risk-timeline-title"
    >
      <h2 id="risk-timeline-title" className="font-bold text-slate-950">
        Cambios de nivel disponibles
      </h2>
      {!detail.risk_history && (
        <p className="mt-1 text-xs text-slate-500">
          El backend no devolvió historial adicional; se muestra únicamente
          esta evaluación.
        </p>
      )}
      <ol className="mt-4 space-y-3">
        {entries.map((entry) => (
          <li
            key={entry.id}
            className="relative border-l-2 border-slate-200 pl-5"
          >
            <span
              className="absolute -left-[5px] top-2 h-2 w-2 rounded-full bg-blue-600"
              aria-hidden="true"
            />
            <div className="flex flex-wrap items-center gap-2">
              <RiskLevelBadge level={entry.risk_level} />
              <time className="text-xs text-slate-500">
                {formatDateTime(entry.evaluated_at)}
              </time>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Acción aplicada: {translate('action', entry.applied_action, entry.applied_action)}
            </p>
          </li>
        ))}
      </ol>
    </section>
  )
}
