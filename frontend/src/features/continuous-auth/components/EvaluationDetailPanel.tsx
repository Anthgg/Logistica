import { useTranslations } from '../../../hooks/useTranslations'
import { formatDateTime } from '../../../utils/date'
import type { AdminEvaluationDetail } from '../types/continuous-auth'
import { AuthenticationLevelBadge } from './AuthenticationLevelBadge'
import { RiskLevelBadge } from './RiskLevelBadge'

function recordEntries(
  record: Record<string, number | null>,
): Array<[string, number | null]> {
  return Object.entries(record)
}

function latencyText(
  latency: AdminEvaluationDetail['latency'],
): string {
  if (typeof latency === 'number') {
    return `${latency} ms`
  }

  return Object.entries(latency)
    .map(([name, value]) => `${name}: ${value} ms`)
    .join(' · ')
}

function componentAvailability(
  detail: AdminEvaluationDetail,
): Array<[string, string]> {
  const keys = [
    ...Object.keys(detail.component_scores),
    ...Object.keys(detail.component_risks),
  ].map((key) => key.toLowerCase())

  return [
    ['Facial', keys.some((key) => key.includes('facial') || key.includes('face')) ? 'Reportado' : 'No informado'],
    ['PAD', keys.some((key) => key.includes('pad') || key.includes('presence')) ? 'Reportado' : 'No informado'],
    ['Conductual', keys.some((key) => key.includes('behavior') || key.includes('conduct')) ? 'Reportado' : 'No informado'],
  ]
}

export function EvaluationDetailPanel({
  detail,
}: {
  detail: AdminEvaluationDetail
}) {
  const { translate } = useTranslations()
  const metadata = [
    ['Fecha', formatDateTime(detail.evaluated_at)],
    ['Usuario', detail.user.label ?? detail.user.id],
    ['Sesión', detail.session.label ?? detail.session.id],
    [
      'Participante',
      detail.participant?.label ??
        detail.participant?.id ??
        'No vinculado',
    ],
    ['Acción recomendada', translate('action', detail.recommended_action, detail.recommended_action)],
    ['Acción aplicada', translate('action', detail.applied_action, detail.applied_action)],
    ['Latencia', latencyText(detail.latency)],
  ]

  return (
    <div className="grid gap-5 xl:grid-cols-[1.3fr_1fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-blue-700">
              Evaluación
            </p>
            <h2 className="mt-1 font-mono text-sm font-bold text-slate-950">
              {detail.id}
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <RiskLevelBadge level={detail.risk_level} />
            <AuthenticationLevelBadge
              level={detail.authentication_level}
            />
          </div>
        </div>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
          {metadata.map(([label, value]) => (
            <div
              key={label}
              className="rounded-xl border border-slate-100 bg-slate-50 p-3"
            >
              <dt className="text-xs font-semibold text-slate-500">
                {label}
              </dt>
              <dd className="mt-1 break-words text-sm font-medium text-slate-900">
                {value}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="font-bold text-slate-950">
          Resumen técnico autorizado
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Solo valores normalizados entregados por el backend.
        </p>

        <div className="mt-4 space-y-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600">
              Disponibilidad de componentes
            </h3>
            <dl className="mt-2 grid grid-cols-3 gap-2">
              {componentAvailability(detail).map(([name, value]) => (
                <div key={name} className="rounded-lg bg-slate-50 p-2">
                  <dt className="text-xs font-semibold text-slate-700">
                    {name}
                  </dt>
                  <dd className="mt-1 text-xs text-slate-500">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600">
              Riesgo combinado
            </h3>
            <p className="mt-1 text-sm font-semibold text-slate-900">
              {detail.combined_risk ?? 'No disponible'}
            </p>
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600">
              Puntajes autorizados por componente
            </h3>
            {recordEntries(detail.component_scores).length === 0 ? (
              <p className="mt-1 text-sm text-slate-500">No disponibles</p>
            ) : (
              <dl className="mt-2 grid gap-2">
                {recordEntries(detail.component_scores).map(
                  ([name, value]) => (
                    <div
                      key={name}
                      className="flex justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-sm"
                    >
                      <dt className="font-medium text-slate-700">{name}</dt>
                      <dd className="font-mono text-slate-900">
                        {value ?? 'No disponible'}
                      </dd>
                    </div>
                  ),
                )}
              </dl>
            )}
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600">
              Riesgos por componente
            </h3>
            {recordEntries(detail.component_risks).length === 0 ? (
              <p className="mt-1 text-sm text-slate-500">No disponibles</p>
            ) : (
              <dl className="mt-2 grid gap-2">
                {recordEntries(detail.component_risks).map(
                  ([name, value]) => (
                    <div
                      key={name}
                      className="flex justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-sm"
                    >
                      <dt className="font-medium text-slate-700">{name}</dt>
                      <dd className="font-mono text-slate-900">
                        {value ?? 'No disponible'}
                      </dd>
                    </div>
                  ),
                )}
              </dl>
            )}
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-600">
              Versiones
            </h3>
            <dl className="mt-2 space-y-1 text-sm">
              {Object.entries(detail.model_versions).map(
                ([name, version]) => (
                  <div key={name} className="flex justify-between gap-3">
                    <dt className="text-slate-600">{name}</dt>
                    <dd className="font-mono text-slate-900">{version}</dd>
                  </div>
                ),
              )}
            </dl>
          </div>
        </div>
      </section>
    </div>
  )
}
