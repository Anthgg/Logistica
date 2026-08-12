import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  EmptyState,
  ErrorState,
  StatusPill,
  TableSkeleton,
} from '../../supplier-evaluation/components/ui/SharedState'
import { procurementApprovalsApi } from '../api/procurementApprovalsApi'
import type { ProcurementApprovalPolicy } from '../types/phase035-contract'

export function ApprovalPolicyDetailPage({
  section = 'detail',
}: {
  section?: 'detail' | 'versions'
}) {
  const { policyId } = useParams<{ policyId: string }>()
  const navigate = useNavigate()
  const [policy, setPolicy] = useState<ProcurementApprovalPolicy | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!policyId) return
    setIsLoading(true)
    setErrorMessage(null)
    try {
      setPolicy(await procurementApprovalsApi.getPolicy(policyId))
    } catch (error: unknown) {
      setPolicy(null)
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo cargar la política.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [policyId])

  useEffect(() => {
    void load()
  }, [load])

  if (isLoading) return <TableSkeleton />
  if (errorMessage) {
    return <ErrorState message={errorMessage} onRetry={() => void load()} />
  }
  if (!policy) return <EmptyState title="Política no encontrada" />

  const base = `/logistics/purchasing/approval-policies/${policy.id}`

  return (
    <section className="space-y-4" aria-labelledby="policy-detail-title">
      <header className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <button
          type="button"
          onClick={() =>
            navigate('/logistics/purchasing/approval-policies')
          }
          className="min-h-10 text-xs font-semibold text-[#1F4E6D] hover:underline"
        >
          ← Volver a políticas
        </button>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-mono text-xs font-bold text-[#1F4E6D]">
              {policy.code}
            </p>
            <h1
              id="policy-detail-title"
              className="mt-1 text-xl font-bold text-slate-950"
            >
              {policy.name}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {policy.description ?? 'Sin descripción'}
            </p>
          </div>
          <div className="flex gap-2">
            <StatusPill>{policy.status}</StatusPill>
            {policy.is_fallback && (
              <StatusPill tone="warning">Fallback</StatusPill>
            )}
          </div>
        </div>
      </header>

      <nav
        aria-label="Secciones de la política"
        className="flex gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1"
      >
        <button
          type="button"
          aria-current={section === 'detail' ? 'page' : undefined}
          onClick={() => navigate(base)}
          className={
            section === 'detail'
              ? 'min-h-10 rounded-lg bg-white px-3 text-xs font-semibold text-[#1F4E6D] shadow-sm'
              : 'min-h-10 rounded-lg px-3 text-xs text-slate-600'
          }
        >
          Resumen
        </button>
        <button
          type="button"
          aria-current={section === 'versions' ? 'page' : undefined}
          onClick={() => navigate(`${base}/versions`)}
          className={
            section === 'versions'
              ? 'min-h-10 rounded-lg bg-white px-3 text-xs font-semibold text-[#1F4E6D] shadow-sm'
              : 'min-h-10 rounded-lg px-3 text-xs text-slate-600'
          }
        >
          Versiones
        </button>
      </nav>

      {section === 'detail' && (
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ['Tipo de recurso', policy.subject_type],
            ['Prioridad', String(policy.priority)],
            ['Alcance', policy.effective_scope],
            ['Versión activa', policy.active_version_id ?? '—'],
            ['Organización', policy.organization_id],
            ['Código normalizado', policy.normalized_code],
            ['Creada', policy.created_at],
            ['Actualizada', policy.updated_at],
          ].map(([label, value]) => (
            <div
              key={label}
              className="min-w-0 rounded-xl border border-slate-200 bg-white p-3"
            >
              <dt className="text-xs text-slate-500">{label}</dt>
              <dd className="mt-1 truncate text-sm font-semibold text-slate-800">
                {value}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {section === 'versions' && (
        <div className="space-y-3">
          {policy.active_version_id ? (
            <article className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Versión activa conocida
                </h2>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {policy.active_version_id}
                </p>
              </div>
              <button
                type="button"
                onClick={() =>
                  navigate(
                    `/logistics/purchasing/approval-policy-versions/${policy.active_version_id}`,
                  )
                }
                className="min-h-10 rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-700"
              >
                Abrir versión
              </button>
            </article>
          ) : (
            <EmptyState title="La política no informa una versión activa" />
          )}
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            El backend no publica listado ni creación de versiones. Solo puede
            abrirse la versión activa que la política ya referencia.
          </div>
        </div>
      )}
    </section>
  )
}
