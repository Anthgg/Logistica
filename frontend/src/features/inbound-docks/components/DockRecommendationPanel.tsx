import { StatusPill, SectionPanel } from './ui/Primitives'
import type { DockRecommendation } from '../types/inbound-docks'
import { formatSecondsApprox } from '../utils/format'

export function DockRecommendationPanel({
  recommendation,
}: {
  recommendation: DockRecommendation | null | undefined
}) {
  return (
    <SectionPanel
      title="Recomendación operativa"
      description="La asignación no se ejecutará hasta confirmarla."
    >
      {!recommendation ? (
        <p className="text-xs text-slate-500">Sin recomendación disponible.</p>
      ) : (
        <div className="space-y-2 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            {recommendation.recommended_dock_id ? (
              <span className="text-sm font-bold text-slate-800">
                Muelle recomendado: {recommendation.recommended_dock_code}{' '}
                <span className="text-slate-500">— {recommendation.recommended_dock_name}</span>
              </span>
            ) : (
              <span className="text-sm font-semibold text-rose-700">
                No hay recomendación.
              </span>
            )}
            <StatusPill tone={recommendation.is_available ? 'success' : 'warning'}>
              {recommendation.is_available ? 'Disponible' : 'No disponible'}
            </StatusPill>
          </div>
          {recommendation.estimated_wait_seconds != null && (
            <p className="text-[11px] text-slate-600">
              Espera estimada: {formatSecondsApprox(recommendation.estimated_wait_seconds)}
            </p>
          )}
          {recommendation.policy_used && (
            <p className="text-[11px] text-slate-500">
              Política: {recommendation.policy_used}
            </p>
          )}
          {recommendation.matched_capabilities.length > 0 && (
            <p className="text-[11px] text-slate-600">
              <span className="font-semibold">Coincidencias:</span>{' '}
              {recommendation.matched_capabilities.join(', ')}
            </p>
          )}
          {recommendation.reasons.length > 0 && (
            <ul className="list-disc pl-4 text-[11px] text-slate-700">
              {recommendation.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          {recommendation.warnings.length > 0 && (
            <ul className="list-disc pl-4 text-[11px] text-amber-700">
              {recommendation.warnings.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          <p className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-2 text-[11px] text-indigo-700">
            Recomendación operativa. La asignación no se ejecutará hasta confirmarla.
          </p>
        </div>
      )}
    </SectionPanel>
  )
}
