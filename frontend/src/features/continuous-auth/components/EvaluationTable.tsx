import { Link } from 'react-router-dom'
import { Pagination } from '../../../components/common/Pagination'
import { useTranslations } from '../../../hooks/useTranslations'
import { formatDateTime } from '../../../utils/date'
import type { AdminEvaluationPage } from '../types/continuous-auth'
import { AuthenticationLevelBadge } from './AuthenticationLevelBadge'
import { RiskLevelBadge } from './RiskLevelBadge'

export function EvaluationTable({
  data,
  onPageChange,
}: {
  data: AdminEvaluationPage
  onPageChange: (page: number) => void
}) {
  const { translate } = useTranslations()
  if (data.items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
        <h2 className="font-bold text-slate-900">
          No hay evaluaciones para estos filtros
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Ajusta los filtros o actualiza la consulta.
        </p>
      </div>
    )
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              {[
                'Fecha',
                'Usuario',
                'Sesión',
                'Participante',
                'Riesgo',
                'Autenticación',
                'Acción',
                'Latencia',
                'Detalle',
              ].map((heading) => (
                <th
                  key={heading}
                  scope="col"
                  className="border-b border-slate-200 px-3 py-3 font-bold"
                >
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.items.map((evaluation) => (
              <tr key={evaluation.id}>
                <td className="whitespace-nowrap px-3 py-3">
                  {formatDateTime(evaluation.evaluated_at)}
                </td>
                <td className="max-w-36 truncate px-3 py-3 font-mono">
                  {evaluation.user_id}
                </td>
                <td className="max-w-36 truncate px-3 py-3 font-mono">
                  {evaluation.session_id}
                </td>
                <td className="max-w-36 truncate px-3 py-3 font-mono">
                  {evaluation.participant_id ?? 'No vinculado'}
                </td>
                <td className="px-3 py-3">
                  <RiskLevelBadge level={evaluation.risk_level} />
                </td>
                <td className="px-3 py-3">
                  <AuthenticationLevelBadge
                    level={evaluation.authentication_level}
                  />
                </td>
                <td className="px-3 py-3">
                  {translate('action', evaluation.applied_action, evaluation.applied_action)}
                </td>
                <td className="whitespace-nowrap px-3 py-3">
                  {evaluation.latency_ms} ms
                </td>
                <td className="px-3 py-3">
                  <Link
                    to={`/admin/continuous-auth/evaluations/${evaluation.id}`}
                    className="font-bold text-blue-700 underline-offset-2 hover:underline"
                  >
                    Ver detalle
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 p-3 md:hidden">
        {data.items.map((evaluation) => (
          <article
            key={evaluation.id}
            className="rounded-xl border border-slate-200 p-4"
          >
            <div className="flex flex-wrap gap-2">
              <RiskLevelBadge level={evaluation.risk_level} />
              <AuthenticationLevelBadge
                level={evaluation.authentication_level}
              />
            </div>
            <dl className="mt-3 grid gap-2 text-xs">
              <div>
                <dt className="font-semibold text-slate-500">Fecha</dt>
                <dd>{formatDateTime(evaluation.evaluated_at)}</dd>
              </div>
              <div>
                <dt className="font-semibold text-slate-500">Usuario</dt>
                <dd className="truncate font-mono">
                  {evaluation.user_id}
                </dd>
              </div>
              <div>
                <dt className="font-semibold text-slate-500">Acción</dt>
                <dd>{translate('action', evaluation.applied_action, evaluation.applied_action)}</dd>
              </div>
            </dl>
            <Link
              to={`/admin/continuous-auth/evaluations/${evaluation.id}`}
              className="mt-3 inline-flex min-h-11 items-center font-bold text-blue-700"
            >
              Ver detalle
            </Link>
          </article>
        ))}
      </div>

      <div className="border-t border-slate-200 p-3">
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={onPageChange}
        />
      </div>
    </section>
  )
}
