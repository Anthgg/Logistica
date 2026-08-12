import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
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
import type { PutawayListApi, PutawayOrderApi, PutawayTaskApi } from '../types/putaway-api'

const ACTIVE_ORDER_STATUSES = new Set(['ISSUED', 'ASSIGNED', 'IN_PROGRESS', 'PARTIALLY_COMPLETED'])
const PENDING_TASK_STATUSES = new Set(['CREATED', 'RECOMMENDATION_PENDING', 'READY', 'ASSIGNED'])

function statusLabel(value: string): string {
  return value.toLowerCase().replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase())
}

export function PutawayDashboardPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.view)
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.putaway.createOrder)
  const canUseMobile = hasPermission(LOGISTICS_PERMISSIONS.putaway.mobileAccess)
  const organizationId = currentContext.organization_id

  const orders = useQuery<PutawayListApi<PutawayOrderApi>>(
    ['putaway', 'dashboard', 'orders', organizationId],
    '/logistics/putaway/orders',
    { page: 1, page_size: 50, sort_by: 'created_at', sort_order: 'desc' },
    { enabled: canView && Boolean(organizationId) },
  )

  const tasks = useQuery<PutawayListApi<PutawayTaskApi>>(
    ['putaway', 'dashboard', 'tasks', organizationId],
    '/logistics/putaway/tasks',
    { page: 1, page_size: 50, sort_by: 'created_at', sort_order: 'desc' },
    { enabled: canView && Boolean(organizationId) },
  )

  const metrics = useMemo(() => {
    const orderItems = orders.data?.items ?? []
    const taskItems = tasks.data?.items ?? []
    return {
      activeOrders: orderItems.filter((order) => ACTIVE_ORDER_STATUSES.has(order.status)).length,
      pendingTasks: taskItems.filter((task) => PENDING_TASK_STATUSES.has(task.status)).length,
      inProgress: taskItems.filter((task) => task.status === 'IN_PROGRESS').length,
      exceptions: taskItems.reduce((total, task) => total + task.exception_count, 0),
      completed: taskItems.filter((task) => task.status === 'COMPLETED').length,
    }
  }, [orders.data, tasks.data])

  if (!canView) {
    return <div className="space-y-4"><PageHeader title="Ubicación dirigida" /><Alert variant="error">No tienes permisos para ver la ubicación dirigida.</Alert></div>
  }

  const loading = orders.isLoading || tasks.isLoading
  const error = orders.error || tasks.error

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 043 · Ejecución"
        title="Centro de ubicación dirigida"
        description="Prioriza órdenes, ejecuta tareas y controla excepciones desde una vista operativa única."
        actions={<div className="flex flex-wrap gap-2">{canCreate && <Button onClick={() => navigate('/logistics/putaway/orders/new')}>Nueva orden</Button>}{canUseMobile && <Button variant="secondary" onClick={() => navigate('/logistics/putaway/mobile')}>Workspace móvil</Button>}</div>}
      />

      <PutawayPhaseNav />

      {!organizationId && <PutawayContextEmptyState title="Selecciona dónde ejecutar el putaway" description="Las órdenes, tareas y proyecciones de capacidad pertenecen a una organización concreta." />}

      {organizationId && (
        <>
          {loading && <LoadingSkeleton rows={6} />}
          {error && <Alert variant="error">{getErrorMessage(error)}</Alert>}

          {!loading && !error && (
            <>
              <section className="relative overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-sm md:p-8">
                <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-blue-500/10" aria-hidden="true" />
                <div className="relative flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl"><p className="text-xs font-semibold uppercase tracking-[0.17em] text-orange-300">Pulso operativo</p><h2 className="mt-3 text-2xl font-bold tracking-tight md:text-3xl">Mercancía en movimiento hacia almacenamiento</h2><p className="mt-3 text-sm leading-6 text-slate-300">El tablero se construye con las órdenes y tareas reales de la Fase 043; no usa un endpoint de resumen simulado.</p></div>
                  <div className="flex gap-3"><div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4"><p className="text-xs text-slate-400">Finalizadas</p><p className="mt-1 text-2xl font-bold">{metrics.completed}</p></div><div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4"><p className="text-xs text-slate-400">Con excepción</p><p className="mt-1 text-2xl font-bold text-orange-300">{metrics.exceptions}</p></div></div>
                </div>
              </section>

              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de ubicación dirigida">
                {([
                  ['package' as const, 'Órdenes activas', metrics.activeOrders, 'bg-blue-50 text-blue-700'],
                  ['check-square' as const, 'Tareas pendientes', metrics.pendingTasks, 'bg-violet-50 text-violet-700'],
                  ['activity' as const, 'En ejecución', metrics.inProgress, 'bg-orange-50 text-orange-700'],
                  ['alert' as const, 'Excepciones abiertas', metrics.exceptions, metrics.exceptions ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'],
                ] as const).map(([icon, label, value, color]) => <div key={label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{value}</p></div><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${color}`}><LogisticsIcon name={icon} size={21} aria-hidden="true" /></span></div></div>)}
              </section>

              <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <div>
                  <div className="mb-4 flex items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Cola prioritaria</p><h2 className="mt-1 text-xl font-bold text-slate-950">Tareas que requieren acción</h2></div><button type="button" onClick={() => navigate('/logistics/putaway/tasks')} className="text-sm font-semibold text-blue-700 hover:text-blue-900">Ver todas</button></div>
                  {(tasks.data?.items ?? []).filter((task) => task.status !== 'COMPLETED' && task.status !== 'CANCELLED').slice(0, 5).length === 0 ? (
                    <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700"><LogisticsIcon name="check" size={24} aria-hidden="true" /></span><h3 className="mt-5 font-bold text-slate-950">Sin tareas pendientes</h3><p className="mt-2 text-sm text-slate-500">La cola operativa está al día.</p></div>
                  ) : (
                    <div className="space-y-3">{(tasks.data?.items ?? []).filter((task) => task.status !== 'COMPLETED' && task.status !== 'CANCELLED').slice(0, 5).map((task) => <button type="button" key={task.id} onClick={() => navigate(`/logistics/putaway/tasks/${task.id}`)} className="flex w-full flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-blue-200 hover:shadow-md sm:flex-row sm:items-center sm:justify-between"><div className="flex min-w-0 items-center gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700"><LogisticsIcon name="location" size={19} aria-hidden="true" /></span><div className="min-w-0"><p className="truncate font-semibold text-slate-950">{task.task_number}</p><p className="mt-1 truncate text-xs text-slate-500">Producto {task.expected_product_id.slice(0, 8)} · Restante {task.remaining_quantity}</p></div></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{statusLabel(task.status)}</span></button>)}</div>
                  )}
                </div>

                <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Accesos rápidos</p><h2 className="mt-2 text-xl font-bold text-slate-950">Coordina el flujo</h2>
                  <div className="mt-5 grid gap-3">{([
                    ['/logistics/putaway/orders', 'package' as const, 'Administrar órdenes', 'Planifica y emite trabajo de ubicación.'],
                    ['/logistics/putaway/tasks', 'check-square' as const, 'Ejecutar tareas', 'Asigna, escanea y confirma posiciones.'],
                    ['/logistics/putaway/exceptions', 'alert' as const, 'Resolver excepciones', 'Atiende tareas bloqueadas o desviadas.'],
                    ['/logistics/putaway/capacity', 'layers' as const, 'Consultar capacidad', 'Revisa proyecciones por ubicación.'],
                  ] as const).map(([path, icon, title, description]) => <button key={path} type="button" onClick={() => navigate(path)} className="flex items-center gap-3 rounded-2xl border border-slate-200 p-4 text-left transition hover:border-blue-200 hover:bg-blue-50/40"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700"><LogisticsIcon name={icon} size={18} aria-hidden="true" /></span><span><span className="block text-sm font-semibold text-slate-950">{title}</span><span className="mt-1 block text-xs leading-5 text-slate-500">{description}</span></span></button>)}</div>
                </aside>
              </section>
            </>
          )}
        </>
      )}
    </div>
  )
}
