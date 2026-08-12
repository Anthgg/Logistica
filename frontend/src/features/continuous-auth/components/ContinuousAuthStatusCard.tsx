import { useTranslations } from '../../../hooks/useTranslations'
import { formatDateTime } from '../../../utils/date'
import type { ContinuousAuthStatus } from '../types/continuous-auth'
import { AuthenticationLevelBadge } from './AuthenticationLevelBadge'
import { RiskLevelBadge } from './RiskLevelBadge'

export function ContinuousAuthStatusCard({
  status,
}: {
  status: ContinuousAuthStatus
}) {
  const { translate } = useTranslations()
  const fields = [
    {
      label: 'Última evaluación',
      value: formatDateTime(status.last_evaluation_at),
    },
    {
      label: 'Próxima evaluación disponible',
      value: formatDateTime(status.next_evaluation_after),
    },
    {
      label: 'Acción recomendada',
      value: translate('action', status.recommended_action, status.recommended_action),
    },
    {
      label: 'Acción aplicada',
      value: translate('action', status.applied_action, status.applied_action),
    },
  ]

  return (
    <section
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      aria-labelledby="continuous-auth-summary-title"
    >
      <div className="flex flex-col gap-4 border-b border-slate-100 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-blue-700">
            Protección de sesión
          </p>
          <h2
            id="continuous-auth-summary-title"
            className="mt-1 text-lg font-bold text-slate-950"
          >
            {translate(
              'continuous_auth_status',
              status.continuous_auth_status,
              status.continuous_auth_status,
            )}
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            {status.degraded && status.degraded_reason
              ? status.degraded_reason
              : status.enabled
                ? 'Protección continua habilitada.'
                : 'Protección continua deshabilitada.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <RiskLevelBadge level={status.risk_level} />
          <AuthenticationLevelBadge
            level={status.authentication_level}
          />
        </div>
      </div>

      <dl className="mt-4 grid gap-3 sm:grid-cols-2">
        {fields.map((field) => (
          <div
            key={field.label}
            className="rounded-xl border border-slate-100 bg-slate-50 p-3"
          >
            <dt className="text-xs font-semibold text-slate-500">
              {field.label}
            </dt>
            <dd className="mt-1 text-sm font-medium text-slate-900">
              {field.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
