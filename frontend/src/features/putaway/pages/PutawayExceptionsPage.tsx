import { useMemo } from 'react'
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

export function PutawayExceptionsPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewExceptions)
  const organizationId = currentContext.organization_id

  const tasks = useQuery<PutawayListApi<PutawayTaskApi>>(
    ['putaway', 'exceptions', organizationId],
    '/logistics/putaway/tasks',
    { page: 1, page_size: 100, sort_by: 'updated_at', sort_order: 'desc' },
    { enabled: canView && Boolean(organizationId) },
  )

  const affectedTasks = useMemo(() => (tasks.data?.items ?? []).filter((task) => task.exception_count > 0 || task.status === 'EXCEPTION' || task.status === 'REPLAN_REQUIRED'), [tasks.data])
  const totalExceptions = affectedTasks.reduce((total, task) => total + Math.max(1, task.exception_count), 0)

  if (!canView) return <div className="space-y-4"><PageHeader title="Excepciones de ubicación" /><Alert variant="error">No tienes permisos para ver las excepciones de ubicación.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Control operativo" title="Excepciones de ubicación" description="Localiza tareas bloqueadas y abre su expediente para revisar, desviar o resolver la incidencia." />
      <PutawayPhaseNav />
      {!organizationId && <PutawayContextEmptyState title="Selecciona la organización a supervisar" description="Las excepciones están subordinadas a una tarea de putaway y respetan su contexto operativo." />}

      {organizationId && (
        <>
          <section className="grid gap-6 lg:grid-cols-[1fr_0.62fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Bandeja de atención</p><h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">{totalExceptions} excepción(es) detectadas</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">El backend no ofrece un listado global de excepciones. La vista correcta identifica tareas afectadas y abre sus excepciones subordinadas desde el detalle.</p></div><span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${totalExceptions ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}><LogisticsIcon name={totalExceptions ? 'alert' : 'check'} size={23} aria-hidden="true" /></span></div></div>
            <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Flujo seguro</p><ol className="mt-5 space-y-4">{[['01', 'Abre la tarea'], ['02', 'Revisa evidencia y pausas'], ['03', 'Resuelve o solicita override']].map(([number, text]) => <li key={number} className="flex items-center gap-3"><span className="flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-xs font-semibold text-orange-300">{number}</span><span className="text-sm text-slate-200">{text}</span></li>)}</ol></aside>
          </section>

          {tasks.isLoading && <LoadingSkeleton rows={6} />}
          {tasks.isError && <Alert variant="error">{getErrorMessage(tasks.error)}</Alert>}

          {tasks.data && affectedTasks.length === 0 && (
            <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-6 py-12 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white"><LogisticsIcon name="check" size={24} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-emerald-950">Operación sin excepciones abiertas</h2><p className="mt-2 text-sm text-emerald-800">No hay tareas bloqueadas ni pendientes de replanificación.</p></div>
          )}

          {affectedTasks.length > 0 && (
            <section aria-labelledby="affected-putaway-tasks"><div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Atención requerida</p><h2 id="affected-putaway-tasks" className="mt-1 text-xl font-bold text-slate-950">Tareas afectadas ({affectedTasks.length})</h2></div><div className="grid gap-4 xl:grid-cols-2">{affectedTasks.map((task) => <button type="button" key={task.id} onClick={() => navigate(`/logistics/putaway/tasks/${task.id}`)} className="rounded-3xl border border-red-100 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-red-200 hover:shadow-md"><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 items-center gap-3"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-red-50 text-red-700"><LogisticsIcon name="alert" size={20} aria-hidden="true" /></span><div className="min-w-0"><h3 className="truncate font-bold text-slate-950">{task.task_number}</h3><p className="mt-1 text-xs text-slate-500">Actualizada {new Date(task.updated_at).toLocaleString('es-PE')}</p></div></div><span className="rounded-full bg-red-50 px-3 py-1 text-xs font-bold text-red-700">{Math.max(1, task.exception_count)} incidencia(s)</span></div><dl className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Estado</dt><dd className="mt-1 text-sm font-semibold text-slate-900">{task.status.replaceAll('_', ' ')}</dd></div><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Cantidad restante</dt><dd className="mt-1 text-sm font-semibold text-slate-900">{task.remaining_quantity}</dd></div></dl></button>)}</div></section>
          )}
        </>
      )}
    </div>
  )
}
