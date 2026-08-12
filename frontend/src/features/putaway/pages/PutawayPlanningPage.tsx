import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { getErrorMessage } from '../../../utils/errors'
import { PutawayPhaseNav } from '../components/PutawayPhaseNav'
import { putawayOrdersApi } from '../api/putawayOrdersApi'
import type { PutawayOrderApi } from '../types/putaway-api'

export function PutawayPlanningPage() {
  const navigate = useNavigate()
  const { orderId = '' } = useParams()
  const { hasPermission } = useLogisticsPermissions()
  const canPlan = hasPermission(LOGISTICS_PERMISSIONS.putaway.planOrder)

  const order = useQuery<PutawayOrderApi>(['putaway', 'order', orderId], `/logistics/putaway/orders/${orderId}`, undefined, { enabled: canPlan && Boolean(orderId) })
  const issue = useMutation<void, PutawayOrderApi>(() => putawayOrdersApi.issueOrder(orderId) as Promise<PutawayOrderApi>, { onSuccess: (result) => navigate(`/logistics/putaway/orders/${result.id}`) })

  if (!canPlan) return <div className="space-y-4"><PageHeader title="Preparar orden" /><Alert variant="error">No tienes permisos para emitir órdenes de ubicación.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Emisión" title="Preparar orden de ubicación" description={order.data ? `Revisa ${order.data.order_code} antes de convertirla en trabajo ejecutable.` : 'Revisa la orden antes de emitirla.'} actions={<Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>} />
      <PutawayPhaseNav />
      {order.isLoading && <LoadingSkeleton rows={5} />}
      {order.isError && <Alert variant="error">{getErrorMessage(order.error)}</Alert>}
      {order.data && <section className="grid gap-6 lg:grid-cols-[1fr_0.7fr]"><div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Orden lista para revisión</p><h2 className="mt-2 text-2xl font-bold text-slate-950">{order.data.order_code}</h2><p className="mt-2 text-sm text-slate-500">Fuente {order.data.source_type.replaceAll('_', ' ')} · Revisión {order.data.current_revision_number}</p></div><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">{order.data.status.replaceAll('_', ' ')}</span></div><dl className="mt-7 grid gap-3 sm:grid-cols-3"><div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs text-slate-500">Tareas</dt><dd className="mt-1 text-2xl font-bold text-slate-950">{order.data.task_count}</dd></div><div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs text-slate-500">Completadas</dt><dd className="mt-1 text-2xl font-bold text-slate-950">{order.data.completed_task_count}</dd></div><div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs text-slate-500">Excepciones</dt><dd className="mt-1 text-2xl font-bold text-slate-950">{order.data.exception_task_count}</dd></div></dl>{issue.error && <p className="mt-4 text-sm text-red-600" role="alert">{issue.error}</p>}<Button className="mt-7 w-full justify-center" onClick={() => issue.mutate(undefined)} isLoading={issue.isPending} loadingLabel="Emitiendo…" disabled={order.data.status === 'ISSUED' || order.data.status === 'IN_PROGRESS' || order.data.status === 'COMPLETED'}>Emitir orden</Button></div><aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 text-sky-300"><LogisticsIcon name="shield" size={21} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold">Las políticas viven en el backend</h2><p className="mt-3 text-sm leading-6 text-slate-300">Rotación, capacidad, compatibilidad y proximidad se resuelven mediante versiones de política. Esta pantalla no envía parámetros inventados de planificación.</p></aside></section>}
    </div>
  )
}
