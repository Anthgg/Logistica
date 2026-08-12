import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import {
  EmptyState,
  ErrorState,
  StatusPill,
  TableSkeleton,
} from '../../supplier-evaluation/components/ui/SharedState'
import { procurementApprovalsApi } from '../api/procurementApprovalsApi'
import type { ProcurementApprovalPolicy } from '../types/phase035-contract'

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-PE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function ApprovalPoliciesPage() {
  const navigate = useNavigate()
  const authorization = useLogisticsPermissions()
  const [subjectType, setSubjectType] = useState('ALL')
  const [items, setItems] = useState<ProcurementApprovalPolicy[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const canCreate = authorization.hasPermission(
    LOGISTICS_PERMISSIONS.procurementApprovals.policiesCreate,
  )

  const load = useCallback(async () => {
    const organizationId = authorization.context.organization_id
    if (!organizationId) {
      setItems([])
      setIsLoading(false)
      setErrorMessage(
        'Selecciona una organización en el contexto logístico.',
      )
      return
    }

    setIsLoading(true)
    setErrorMessage(null)
    try {
      setItems(
        await procurementApprovalsApi.listPolicies(
          organizationId,
          subjectType === 'ALL' ? undefined : subjectType,
        ),
      )
    } catch (error: unknown) {
      setItems([])
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudieron cargar las políticas.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [authorization.context.organization_id, subjectType])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <section className="space-y-4" aria-labelledby="approval-policies-title">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
            Fase 035 · Configuración
          </p>
          <h1
            id="approval-policies-title"
            className="mt-1 text-xl font-bold text-slate-950"
          >
            Políticas de aprobación
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            La prioridad, vigencia y selección autoritativa pertenecen al
            backend.
          </p>
        </div>
        {canCreate && (
          <button
            type="button"
            onClick={() =>
              navigate('/logistics/purchasing/approval-policies/new')
            }
            className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 text-sm font-semibold text-white"
          >
            Nueva política
          </button>
        )}
      </header>

      <div className="max-w-xs rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-600">
            Tipo de recurso
          </span>
          <Select value={subjectType} onValueChange={setSubjectType}>
            <SelectTrigger className="min-h-11 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos</SelectItem>
              <SelectItem value="PURCHASE_ORDER">
                Orden de compra
              </SelectItem>
              <SelectItem value="PURCHASE_REQUISITION">
                Requerimiento
              </SelectItem>
            </SelectContent>
          </Select>
        </label>
      </div>

      {errorMessage ? (
        <ErrorState message={errorMessage} onRetry={() => void load()} />
      ) : isLoading ? (
        <TableSkeleton />
      ) : items.length === 0 ? (
        <EmptyState
          title="No hay políticas"
          description="El backend no devolvió políticas para este contexto."
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3 text-left">Código</th>
                  <th className="px-3 py-3 text-left">Nombre</th>
                  <th className="px-3 py-3 text-left">Recurso</th>
                  <th className="px-3 py-3 text-right">Prioridad</th>
                  <th className="px-3 py-3 text-left">Versión activa</th>
                  <th className="px-3 py-3 text-left">Fallback</th>
                  <th className="px-3 py-3 text-left">Estado</th>
                  <th className="px-3 py-3 text-left">Actualización</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((policy) => (
                  <tr key={policy.id} className="hover:bg-slate-50/70">
                    <td className="px-3 py-3">
                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/logistics/purchasing/approval-policies/${policy.id}`,
                          )
                        }
                        className="min-h-10 font-mono text-xs font-bold text-[#1F4E6D] hover:underline"
                      >
                        {policy.code}
                      </button>
                    </td>
                    <td className="px-3 py-3 text-xs">{policy.name}</td>
                    <td className="px-3 py-3 text-xs">
                      {policy.subject_type}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-xs">
                      {policy.priority}
                    </td>
                    <td className="px-3 py-3 font-mono text-xs">
                      {policy.active_version_id ?? '—'}
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {policy.is_fallback ? 'Sí' : 'No'}
                    </td>
                    <td className="px-3 py-3">
                      <StatusPill>{policy.status}</StatusPill>
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs text-slate-500">
                      {formatDate(policy.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
