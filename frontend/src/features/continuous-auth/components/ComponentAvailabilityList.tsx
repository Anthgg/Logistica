import { useTranslations } from '../../../hooks/useTranslations'
import type { ContinuousAuthComponentSummary } from '../types/continuous-auth'
import { normalizeComponentName } from '../utils/risk-labels'

function componentExplanation(
  component: ContinuousAuthComponentSummary,
  statusLabel: string,
): string {
  if (component.reason) {
    return component.reason
  }
  return statusLabel
}

const dotStyles = {
  available: 'bg-emerald-500',
  pending: 'bg-amber-500',
  unavailable: 'bg-slate-400',
  failed: 'bg-rose-500',
  degraded: 'bg-orange-500',
}

export function ComponentAvailabilityList({
  components,
}: {
  components: ContinuousAuthComponentSummary[]
}) {
  const { translate } = useTranslations()
  if (components.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-600">
        El backend todavía no informó componentes disponibles.
      </p>
    )
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-3" aria-label="Componentes de verificación">
      {components.map((component) => (
        <li
          key={component.name}
          className="rounded-xl border border-slate-200 bg-white p-4"
        >
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${dotStyles[component.status]}`}
              aria-hidden="true"
            />
            <h3 className="font-bold text-slate-900">
              {normalizeComponentName(component.name)}
            </h3>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            {componentExplanation(
              component,
              translate(
                'continuous_auth_status',
                component.status,
                component.status,
              ),
            )}
          </p>
        </li>
      ))}
    </ul>
  )
}
