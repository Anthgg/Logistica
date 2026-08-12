import { useState } from 'react'
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
import type { PutawayListApi, PutawayOrderApi } from '../types/putaway-api'

const STATUS_OPTIONS = [
  ['DRAFT', 'Borrador'], ['PLANNING', 'Planificación'], ['READY_FOR_ISSUE', 'Lista para emitir'],
  ['ISSUED', 'Emitida'], ['ASSIGNED', 'Asignada'], ['IN_PROGRESS', 'En progreso'],
  ['PARTIALLY_COMPLETED', 'Parcial'], ['COMPLETED', 'Completada'],
  ['COMPLETED_WITH_EXCEPTIONS', 'Completada con excepciones'], ['CANCELLED', 'Cancelada'],
] as const

function statusLabel(status: string): string {
  return STATUS_OPTIONS.find(([value]) => value === status)?.[1] ?? status.replaceAll('_', ' ')
}

function statusStyle(status: string): string {
  if (status === 'COMPLETED') return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
  if (status === 'CANCELLED' || status === 'COMPLETED_WITH_EXCEPTIONS') return 'bg-red-50 text-red-700 ring-red-200'
  if (status === 'IN_PROGRESS' || status === 'PARTIALLY_COMPLETED') return 'bg-orange-50 text-orange-700 ring-orange-200'
  if (status === 'ISSUED' || status === 'ASSIGNED') return 'bg-blue-50 text-blue-700 ring-blue-200'
  return 'bg-slate-100 text-slate-700 ring-slate-200'
}

export function PutawayOrdersPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewOrders)
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.putaway.createOrder)
  const organizationId = currentContext.organization_id
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')

  const orders = useQuery<PutawayListApi<PutawayOrderApi>>(
    ['putaway', 'orders', organizationId, status, search],
    '/logistics/putaway/orders',
    { page: 1, page_size: 50, status: status || undefined, search: search || undefined, sort_by: 'created_at', sort_order: 'desc' },
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) return <div className="space-y-4"><PageHeader title="Órdenes de ubicación" /><Alert variant="error">No tienes permisos para ver las órdenes de ubicación.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Planificación" title="Órdenes de ubicación" description="Organiza y emite el trabajo que mueve mercancía desde staging hacia almacenamiento." actions={canCreate ? <Button onClick={() => navigate('/logistics/putaway/orders/new')}>Nueva orden</Button> : undefined} />
      <PutawayPhaseNav />

      {!organizationId && <PutawayContextEmptyState title="Selecciona la organización de las órdenes" description="La cola de putaway se mantiene aislada por contexto operativo." />}

      {organizationId && (
        <>
          <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm md:p-5" aria-label="Filtros de órdenes">
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_260px_auto]">
              <label className="relative"><span className="sr-only">Buscar órdenes</span><LogisticsIcon name="search" size={18} className="pointer-events-none absolute left-4 top-3.5 text-slate-400" aria-hidden="true" /><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por código o fuente" className="min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 py-2.5 pl-11 pr-4 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label>
              <label><span className="sr-only">Estado de la orden</span><select value={status} onChange={(event) => setStatus(event.target.value)} className="min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"><option value="">Todos los estados</option>{STATUS_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
              {(status || search) && <Button variant="ghost" onClick={() => { setStatus(''); setSearch('') }}>Limpiar</Button>}
            </div>
          </section>

          {orders.isLoading && <LoadingSkeleton rows={7} />}
          {orders.isError && <Alert variant="error">{getErrorMessage(orders.error)}</Alert>}

          {orders.data && (
            <section aria-labelledby="putaway-orders-title">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Cola operativa</p><h2 id="putaway-orders-title" className="mt-1 text-xl font-bold text-slate-950">{orders.data.total} orden(es)</h2></div><p className="text-sm text-slate-500">Página {orders.data.page}</p></div>
              {orders.data.items.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="package" size={25} aria-hidden="true" /></span><h3 className="mt-5 font-bold text-slate-950">No hay órdenes con estos filtros</h3><p className="mt-2 text-sm text-slate-500">Ajusta la búsqueda o crea una nueva orden de ubicación.</p></div>
              ) : (
                <div className="grid gap-4 xl:grid-cols-2">{orders.data.items.map((order) => {
                  const progress = order.task_count ? Math.round((order.completed_task_count / order.task_count) * 100) : 0
                  return <button type="button" key={order.id} onClick={() => navigate(`/logistics/putaway/orders/${order.id}`)} className="group rounded-3xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 items-center gap-3"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="package" size={21} aria-hidden="true" /></span><div className="min-w-0"><h3 className="truncate font-bold text-slate-950">{order.order_code}</h3><p className="mt-1 truncate text-sm text-slate-500">{order.source_type.replaceAll('_', ' ')} · Prioridad {order.priority}</p></div></div><span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${statusStyle(order.status)}`}>{statusLabel(order.status)}</span></div><div className="mt-5"><div className="flex items-center justify-between text-xs text-slate-500"><span>Progreso de tareas</span><span>{order.completed_task_count}/{order.task_count}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-600" style={{ width: `${progress}%` }} /></div></div><div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4 text-xs text-slate-500"><span>{new Date(order.created_at).toLocaleString('es-PE')}</span><span className={order.exception_task_count ? 'font-semibold text-red-600' : ''}>{order.exception_task_count} excepción(es)</span></div></button>
                })}</div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  )
}
