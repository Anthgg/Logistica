import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { PutawayPhaseNav } from '../components/PutawayPhaseNav'
import { PutawayContextEmptyState } from '../components/PutawayContextEmptyState'
import type { PutawayListApi, PutawayTaskApi } from '../types/putaway-api'

const STATUS_OPTIONS = [
  ['CREATED', 'Creada'], ['RECOMMENDATION_PENDING', 'Esperando recomendación'], ['READY', 'Lista'],
  ['ASSIGNED', 'Asignada'], ['IN_PROGRESS', 'En progreso'], ['PRODUCT_SCAN_REQUIRED', 'Escanear producto'],
  ['LOCATION_SCAN_REQUIRED', 'Escanear ubicación'], ['QUANTITY_CONFIRMATION_REQUIRED', 'Confirmar cantidad'],
  ['PARTIALLY_COMPLETED', 'Parcial'], ['COMPLETED', 'Completada'], ['EXCEPTION', 'Excepción'],
  ['REPLAN_REQUIRED', 'Replanificar'], ['PAUSED', 'Pausada'], ['CANCELLED', 'Cancelada'],
] as const

function statusLabel(status: string): string {
  return STATUS_OPTIONS.find(([value]) => value === status)?.[1] ?? status.replaceAll('_', ' ')
}

function statusStyle(status: string): string {
  if (status === 'COMPLETED') return 'bg-emerald-50 text-emerald-700'
  if (status === 'EXCEPTION' || status === 'REPLAN_REQUIRED' || status === 'CANCELLED') return 'bg-red-50 text-red-700'
  if (status === 'IN_PROGRESS' || status.includes('REQUIRED')) return 'bg-orange-50 text-orange-700'
  if (status === 'ASSIGNED' || status === 'READY') return 'bg-blue-50 text-blue-700'
  return 'bg-slate-100 text-slate-700'
}

export function PutawayTasksPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewTasks)
  const organizationId = currentContext.organization_id
  const [status, setStatus] = useState('')

  const tasks = useQuery<PutawayListApi<PutawayTaskApi>>(
    ['putaway', 'tasks', organizationId, status],
    '/logistics/putaway/tasks',
    { page: 1, page_size: 50, status: status || undefined, sort_by: 'priority', sort_order: 'desc' },
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) return <div className="space-y-4"><PageHeader title="Tareas de ubicación" /><Alert variant="error">No tienes permisos para ver las tareas de ubicación.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Ejecución" title="Tareas de ubicación" description="Asigna, escanea y confirma el traslado físico hacia la posición recomendada." />
      <PutawayPhaseNav />
      {!organizationId && <PutawayContextEmptyState title="Selecciona la organización de las tareas" description="La cola móvil y las cantidades pendientes se consultan dentro del contexto elegido." />}

      {organizationId && (
        <>
          <section className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-end sm:justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Cola de ejecución</p><h2 className="mt-1 text-xl font-bold text-slate-950">Prioriza el siguiente movimiento</h2><p className="mt-2 text-sm text-slate-500">Los estados reflejan el flujo real del backend, incluidos escaneos y confirmaciones.</p></div>
            <label className="w-full sm:w-72"><span className="text-sm font-semibold text-slate-700">Estado</span><select value={status} onChange={(event) => setStatus(event.target.value)} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"><option value="">Todos los estados</option>{STATUS_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          </section>

          {tasks.isLoading && <LoadingSkeleton rows={8} />}
          {tasks.isError && <Alert variant="error">{getErrorMessage(tasks.error)}</Alert>}

          {tasks.data && (
            <section aria-labelledby="putaway-tasks-title">
              <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Trabajo disponible</p><h2 id="putaway-tasks-title" className="mt-1 text-xl font-bold text-slate-950">{tasks.data.total} tarea(s)</h2></div>
              {tasks.data.items.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700"><LogisticsIcon name="check" size={24} aria-hidden="true" /></span><h3 className="mt-5 font-bold text-slate-950">Sin tareas en esta cola</h3><p className="mt-2 text-sm text-slate-500">Cambia el estado o revisa las órdenes pendientes de emisión.</p></div>
              ) : (
                <div className="space-y-3">{tasks.data.items.map((task) => {
                  const required = Number(task.required_quantity) || 0
                  const placed = Number(task.placed_quantity) || 0
                  const progress = required > 0 ? Math.min(100, Math.round((placed / required) * 100)) : 0
                  return (
                    <button
                      type="button"
                      key={task.id}
                      onClick={() => navigate(`/logistics/putaway/tasks/${task.id}`)}
                      className="group grid w-full gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-blue-200 hover:shadow-md md:grid-cols-[minmax(0,1fr)_180px_150px] md:items-center"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="location" size={20} aria-hidden="true" /></span>
                        <div className="min-w-0"><h3 className="truncate font-bold text-slate-950">{task.task_number}</h3><p className="mt-1 truncate text-xs text-slate-500">Producto {task.expected_product_id.slice(0, 8)} · Política {task.scan_policy.replaceAll('_', ' ')}</p></div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-slate-500"><span>Ubicado</span><span>{placed}/{required}</span></div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-600" style={{ width: `${progress}%` }} /></div>
                      </div>
                      <div className="flex items-center justify-between gap-2 md:justify-end">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyle(task.status)}`}>{statusLabel(task.status)}</span>
                        {task.exception_count > 0 && <span className="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-xs font-bold text-red-700" aria-label={`${task.exception_count} excepciones`}>{task.exception_count}</span>}
                      </div>
                    </button>
                  )
                })}</div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  )
}
