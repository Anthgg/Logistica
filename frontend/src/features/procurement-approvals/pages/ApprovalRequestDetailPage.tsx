import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { formatMoney } from '../../purchase-orders/format'
import {
  EmptyState,
  ErrorState,
  StatusPill,
  TableSkeleton,
} from '../../supplier-evaluation/components/ui/SharedState'
import { procurementApprovalsApi } from '../api/procurementApprovalsApi'
import type {
  ApprovalAuditSealSummary,
  ProcurementApprovalRequest,
} from '../types/phase035-contract'

type RequestSection = 'detail' | 'history' | 'integrity'

function formatDate(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-PE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function ApprovalRequestDetailPage({
  section = 'detail',
}: {
  section?: RequestSection
}) {
  const { requestId } = useParams<{ requestId: string }>()
  const navigate = useNavigate()
  const [request, setRequest] =
    useState<ProcurementApprovalRequest | null>(null)
  const [seal, setSeal] = useState<ApprovalAuditSealSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!requestId) return
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const detail = await procurementApprovalsApi.getRequest(requestId)
      setRequest(detail)
      if (section === 'integrity') {
        setSeal(await procurementApprovalsApi.getAuditSeal(requestId))
      } else {
        setSeal(null)
      }
    } catch (error: unknown) {
      setRequest(null)
      setSeal(null)
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo cargar la solicitud de aprobación.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [requestId, section])

  useEffect(() => {
    void load()
  }, [load])

  if (isLoading) return <TableSkeleton rows={7} />
  if (errorMessage) {
    return <ErrorState message={errorMessage} onRetry={() => void load()} />
  }
  if (!request || !requestId) {
    return <EmptyState title="Solicitud de aprobación no encontrada" />
  }

  const base = `/logistics/purchasing/approvals/${requestId}`
  const subjectIsPurchaseOrder = [
    'PURCHASE_ORDER',
    'purchase_order',
  ].includes(request.subject_type)

  return (
    <section className="space-y-4" aria-labelledby="approval-request-title">
      <header className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <button
          type="button"
          onClick={() =>
            navigate('/logistics/purchasing/approvals/inbox')
          }
          className="min-h-10 text-xs font-semibold text-[#1F4E6D] hover:underline"
        >
          ← Volver a la bandeja
        </button>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
              Solicitud de aprobación
            </p>
            <h1
              id="approval-request-title"
              className="mt-1 text-xl font-bold text-slate-950"
            >
              {request.request_code}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {request.subject_type} ·{' '}
              {request.subject_code ?? request.subject_id}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusPill tone="info">{request.status}</StatusPill>
            {request.final_decision && (
              <StatusPill>{request.final_decision}</StatusPill>
            )}
          </div>
        </div>
      </header>

      <nav
        aria-label="Secciones de la solicitud"
        className="flex gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1"
      >
        {[
          ['detail', 'Resumen', ''],
          ['history', 'Historial', '/history'],
          ['integrity', 'Integridad', '/integrity'],
        ].map(([key, label, suffix]) => (
          <button
            key={key}
            type="button"
            aria-current={section === key ? 'page' : undefined}
            onClick={() => navigate(`${base}${suffix}`)}
            className={
              section === key
                ? 'min-h-10 rounded-lg bg-white px-3 text-xs font-semibold text-[#1F4E6D] shadow-sm'
                : 'min-h-10 rounded-lg px-3 text-xs text-slate-600'
            }
          >
            {label}
          </button>
        ))}
      </nav>

      {section === 'detail' && (
        <div className="space-y-4">
          <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              [
                'Monto',
                formatMoney(request.amount, request.currency_code),
              ],
              ['Secuencia actual', String(request.current_sequence)],
              ['Enviada', formatDate(request.submitted_at)],
              ['Completada', formatDate(request.completed_at)],
              ['Organización', request.organization_id],
              ['ID de recurso', request.subject_id],
              ['ID de revisión', request.subject_revision_id ?? '—'],
              ['ID de sello', request.audit_seal_id ?? '—'],
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

          {subjectIsPurchaseOrder && (
            <button
              type="button"
              onClick={() =>
                navigate(
                  `/logistics/purchasing/purchase-orders/${request.subject_id}`,
                )
              }
              className="min-h-11 rounded-lg border border-[#1F4E6D]/30 bg-[#1F4E6D]/5 px-4 text-sm font-semibold text-[#1F4E6D]"
            >
              Abrir orden de compra
            </button>
          )}

          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            El contrato no publica pasos, asignaciones, decisiones,
            capabilities ni cadena para este detalle. No se reconstruyen
            localmente desde snapshots.
          </div>
        </div>
      )}

      {section === 'history' && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <h2 className="text-base font-bold text-amber-950">
            Historial no publicado
          </h2>
          <p className="mt-2 text-sm text-amber-900">
            No existe endpoint de historial para solicitudes en el OpenAPI
            actual.
          </p>
        </div>
      )}

      {section === 'integrity' && (
        <div className="space-y-3">
          {!seal ? (
            <EmptyState title="El backend no devolvió un sello reconocible" />
          ) : (
            <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[
                ['ID de sello', seal.id ?? '—'],
                ['Estado', seal.status ?? '—'],
                ['Algoritmo', seal.algorithm ?? '—'],
                ['ID de clave', seal.key_id ?? '—'],
                ['Creado', formatDate(seal.created_at)],
                ['Verificación', seal.verification_status ?? 'No publicada'],
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
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
            No se muestra firma, digest completo ni cadena canónica. El backend
            no publica una operación de verificación; por ello no se etiqueta
            el sello como “firma digital verificada”.
          </div>
        </div>
      )}
    </section>
  )
}
