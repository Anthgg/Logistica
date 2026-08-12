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
import type { PutawayListApi, PutawayTaskApi } from '../types/putaway-api'

export function PutawayMobileWorkspacePage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canAccess = hasPermission(LOGISTICS_PERMISSIONS.putaway.mobileAccess)
  const organizationId = currentContext.organization_id
  const tasks = useQuery<PutawayListApi<PutawayTaskApi>>(['putaway', 'mobile', organizationId], '/logistics/putaway/tasks', { page: 1, page_size: 50, sort_by: 'priority', sort_order: 'desc' }, { enabled: canAccess && Boolean(organizationId) })
  const actionable = (tasks.data?.items ?? []).filter((task) => !['COMPLETED', 'CANCELLED', 'SUPERSEDED'].includes(task.status))

  if (!canAccess) return <div className="space-y-4"><PageHeader title="Workspace móvil" /><Alert variant="error">No tienes permisos para ejecutar tareas de ubicación.</Alert></div>
  return <div className="space-y-6 pb-10"><PageHeader eyebrow="Fase 043 · Operación móvil" title="Workspace móvil de ubicación" description="Cola táctil para abrir la tarea correcta antes de escanear producto o ubicación." actions={<Button variant="secondary" onClick={() => navigate('/logistics/putaway')}>Volver al tablero</Button>} /><PutawayPhaseNav />{!organizationId && <PutawayContextEmptyState title="Selecciona la operación móvil" description="La cola de tareas y los escaneos deben ejecutarse dentro de una organización concreta." />}{organizationId && <>{tasks.isLoading && <LoadingSkeleton rows={6} />}{tasks.isError && <Alert variant="error">{getErrorMessage(tasks.error)}</Alert>}{tasks.data && <section className="mx-auto max-w-2xl"><div className="rounded-3xl bg-slate-950 p-5 text-white shadow-sm"><div className="flex items-center justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Cola del operario</p><h2 className="mt-1 text-2xl font-bold">{actionable.length} tarea(s) disponibles</h2></div><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-sky-300"><LogisticsIcon name="sessions" size={22} aria-hidden="true" /></span></div><p className="mt-3 text-sm leading-6 text-slate-300">El escaneo se habilita dentro de la tarea y su sesión. No existe un endpoint seguro de escaneo global.</p></div>{actionable.length === 0 ? <div className="mt-4 rounded-3xl border border-emerald-200 bg-emerald-50 px-6 py-12 text-center"><LogisticsIcon name="check" size={26} className="mx-auto text-emerald-700" aria-hidden="true" /><h2 className="mt-4 text-xl font-bold text-emerald-950">Cola completada</h2><p className="mt-2 text-sm text-emerald-800">No hay tareas ejecutables en este contexto.</p></div> : <div className="mt-4 space-y-3">{actionable.map((task, index) => <button type="button" key={task.id} onClick={() => navigate(`/logistics/putaway/tasks/${task.id}`)} className="flex min-h-24 w-full items-center gap-4 rounded-3xl border border-slate-200 bg-white p-4 text-left shadow-sm transition active:scale-[0.99]"><span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-lg font-bold text-white">{index + 1}</span><span className="min-w-0 flex-1"><span className="block truncate font-bold text-slate-950">{task.task_number}</span><span className="mt-1 block truncate text-sm text-slate-500">Restante {task.remaining_quantity} · {task.status.replaceAll('_', ' ')}</span></span><LogisticsIcon name="arrow-right" size={20} className="shrink-0 text-slate-400" aria-hidden="true" /></button>)}</div>}</section>}</>}</div>
}
