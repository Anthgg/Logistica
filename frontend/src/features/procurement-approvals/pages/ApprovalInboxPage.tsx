import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSensitiveOperationGuard } from '../../continuous-auth/hooks/useSensitiveOperationGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { formatMoney } from '../../purchase-orders/format'
import { useDebouncedValue } from '../../purchase-orders/hooks/useDebouncedValue'
import {
  EmptyState,
  ErrorState,
  StatusPill,
  TableSkeleton,
} from '../../supplier-evaluation/components/ui/SharedState'
import { procurementApprovalsApi } from '../api/procurementApprovalsApi'
import { ApprovalDecisionDialog } from '../components/ApprovalDecisionDialog'
import type {
  ApprovalAssignmentSummary,
  ApprovalDecisionType,
} from '../types/phase035-contract'

function formatDate(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-PE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function matchesSearch(
  assignment: ApprovalAssignmentSummary,
  search: string,
): boolean {
  const normalized = search.trim().toLocaleLowerCase()
  if (!normalized) return true
  return [
    assignment.request_code,
    assignment.subject_code,
    assignment.subject_type,
    assignment.step_name,
  ].some((value) => value?.toLocaleLowerCase().includes(normalized))
}

export function ApprovalInboxPage() {
  const navigate = useNavigate()
  const authorization = useLogisticsPermissions()
  const { guardSensitiveAction, requireReverification } =
    useSensitiveOperationGuard()
  const [items, setItems] = useState<ApprovalAssignmentSummary[]>([])
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [selected, setSelected] =
    useState<ApprovalAssignmentSummary | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [decisionError, setDecisionError] = useState<string | null>(null)

  const canDecide = authorization.hasAnyPermission([
    LOGISTICS_PERMISSIONS.procurementApprovals.decide,
    LOGISTICS_PERMISSIONS.purchaseOrdersV2.approveTransitional,
  ])

  const load = useCallback(async () => {
    if (!authorization.userId) {
      setItems([])
      setErrorMessage(
        'El contexto de autorización no entregó un user_id válido.',
      )
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setErrorMessage(null)
    try {
      setItems(
        await procurementApprovalsApi.listMyPendingAssignments(
          authorization.userId,
        ),
      )
    } catch (error: unknown) {
      setItems([])
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo cargar la bandeja de aprobaciones.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [authorization.userId])

  useEffect(() => {
    void load()
  }, [load])

  const visibleItems = useMemo(
    () =>
      items.filter((assignment) =>
        matchesSearch(assignment, debouncedSearch),
      ),
    [debouncedSearch, items],
  )

  const recordDecision = async (
    decision: ApprovalDecisionType,
    reason: string,
  ) => {
    if (!selected || !authorization.userId || !canDecide) return
    setIsSubmitting(true)
    setDecisionError(null)
    setStatusMessage(null)
    try {
      const executed = await guardSensitiveAction(async () => {
        await procurementApprovalsApi.recordDecision(
          selected.id,
          authorization.userId!,
          {
            decision_type: decision,
            reason: reason || null,
          },
        )
      })
      if (!executed) {
        setSelected(null)
        setErrorMessage(
          'La decisión requiere reverificación continua antes de continuar.',
        )
        return
      }
      setSelected(null)
      setStatusMessage('La decisión fue registrada por el backend.')
      await load()
    } catch (error: unknown) {
      setDecisionError(
        error instanceof Error
          ? error.message
          : 'No se pudo registrar la decisión.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="space-y-4" aria-labelledby="approval-inbox-title">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
            Compras · Fase 035
          </p>
          <h1
            id="approval-inbox-title"
            className="mt-1 text-xl font-bold text-slate-950"
          >
            Mi bandeja de aprobaciones
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            Asignaciones pendientes del usuario activo. No existe aprobación
            masiva.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={isLoading}
          className="min-h-11 rounded-lg border border-slate-200 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          {isLoading ? 'Actualizando…' : 'Actualizar'}
        </button>
      </header>

      <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
        El OpenAPI no tipa la respuesta de esta bandeja ni publica capabilities
        por asignación. Solo se muestran campos seguros reconocidos; la
        transición siempre se valida en el servidor.
      </div>

      <label className="block rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <span className="mb-1 block text-xs font-semibold text-slate-600">
          Buscar en asignaciones pendientes
        </span>
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Solicitud, recurso, código o paso"
          className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
        />
      </label>

      {statusMessage && (
        <div
          role="status"
          className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800"
        >
          {statusMessage}
        </div>
      )}

      {errorMessage ? (
        <ErrorState message={errorMessage} onRetry={() => void load()} />
      ) : isLoading ? (
        <TableSkeleton />
      ) : visibleItems.length === 0 ? (
        <EmptyState
          title="No tienes asignaciones pendientes"
          description="La bandeja está al día para el usuario y contexto actuales."
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <caption className="sr-only">
                Asignaciones de aprobación pendientes
              </caption>
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3 text-left">Solicitud</th>
                  <th className="px-3 py-3 text-left">Recurso</th>
                  <th className="px-3 py-3 text-left">Paso</th>
                  <th className="px-3 py-3 text-right">Monto</th>
                  <th className="px-3 py-3 text-left">Vencimiento</th>
                  <th className="px-3 py-3 text-left">Estado</th>
                  <th className="px-3 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visibleItems.map((assignment) => (
                  <tr key={assignment.id} className="hover:bg-slate-50/70">
                    <td className="px-3 py-3">
                      {assignment.request_id ? (
                        <button
                          type="button"
                          onClick={() =>
                            navigate(
                              `/logistics/purchasing/approvals/${assignment.request_id}`,
                            )
                          }
                          className="min-h-10 font-mono text-xs font-bold text-[#1F4E6D] hover:underline"
                        >
                          {assignment.request_code ?? assignment.request_id}
                        </button>
                      ) : (
                        <span className="font-mono text-xs">
                          {assignment.request_code ?? '—'}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-xs">
                      <div>{assignment.subject_type ?? '—'}</div>
                      <div className="font-mono text-slate-500">
                        {assignment.subject_code ?? assignment.subject_id ?? '—'}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {assignment.step_name ?? '—'}
                      {assignment.step_sequence !== null && (
                        <span className="ml-1 text-slate-500">
                          #{assignment.step_sequence}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-xs">
                      {formatMoney(
                        assignment.amount,
                        assignment.currency_code,
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs">
                      {formatDate(assignment.due_at)}
                    </td>
                    <td className="px-3 py-3">
                      <StatusPill tone={assignment.delegated ? 'info' : 'neutral'}>
                        {assignment.delegated
                          ? 'Delegada'
                          : assignment.status ?? 'Pendiente'}
                      </StatusPill>
                    </td>
                    <td className="px-3 py-3 text-right">
                      {canDecide && (
                        <button
                          type="button"
                          disabled={requireReverification}
                          onClick={() => {
                            setDecisionError(null)
                            setSelected(assignment)
                          }}
                          className="min-h-10 rounded-lg bg-[#1F4E6D] px-3 text-xs font-semibold text-white disabled:opacity-40"
                        >
                          Revisar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ApprovalDecisionDialog
        assignment={selected}
        isSubmitting={isSubmitting}
        errorMessage={decisionError}
        onClose={() => {
          if (!isSubmitting) setSelected(null)
        }}
        onConfirm={(decision, reason) =>
          void recordDecision(decision, reason)
        }
      />
    </section>
  )
}
