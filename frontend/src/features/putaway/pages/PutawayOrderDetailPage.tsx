import { useState } from 'react'
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

const TERMINAL = new Set(['COMPLETED', 'COMPLETED_WITH_EXCEPTIONS', 'CANCELLED', 'SUPERSEDED'])

export function PutawayOrderDetailPage() {
  const navigate = useNavigate()
  const { orderId = '' } = useParams()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewOrders)
  const canUpdate = hasPermission(LOGISTICS_PERMISSIONS.putaway.updateOrder)
  const [showCancel, setShowCancel] = useState(false)
  const [cancelReason, setCancelReason] = useState('')

  const order = useQuery<PutawayOrderApi>(['putaway', 'order', orderId], `/logistics/putaway/orders/${orderId}`, undefined, { enabled: canView && Boolean(orderId) })
  const issue = useMutation<void, PutawayOrderApi>(() => putawayOrdersApi.issueOrder(orderId) as Promise<PutawayOrderApi>, { onSuccess: (result) => order.setData(result) })
  const cancel = useMutation<void, PutawayOrderApi>(() => putawayOrdersApi.cancelOrder(orderId, cancelReason.trim()) as Promise<PutawayOrderApi>, { onSuccess: (result) => { order.setData(result); setShowCancel(false); setCancelReason('') } })

  if (!canView) return <div className="space-y-4"><PageHeader title="Detalle de orden" /><Alert variant="error">No tienes permisos para ver esta orden.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Orden" title={order.data ? order.data.order_code : 'Detalle de orden de ubicación'} description={order.data ? `${order.data.source_type.replaceAll('_', ' ')} · Revisión ${order.data.current_revision_number}` : 'Cargando orden de ubicación.'} actions={<div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => navigate('/logistics/putaway/orders')}>Volver</Button>{order.data && canUpdate && !TERMINAL.has(order.data.status) && <Button variant="secondary" onClick={() => setShowCancel(true)}>Cancelar orden</Button>}</div>} />
      <PutawayPhaseNav />
      {order.isLoading && <LoadingSkeleton rows={7} />}
      {order.isError && <Alert variant="error">{getErrorMessage(order.error)}</Alert>}
      {order.data && (
        <>
          <section className="relative overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-sm md:p-8"><div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-blue-500/10" aria-hidden="true" /><div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between"><div><span className="inline-flex rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-sky-300">{order.data.status.replaceAll('_', ' ')}</span><h2 className="mt-4 text-2xl font-bold">Trabajo de ubicación #{order.data.order_code}</h2><p className="mt-2 text-sm text-slate-300">Creada {new Date(order.data.created_at).toLocaleString('es-PE')} · Prioridad {order.data.priority}</p></div><div className="flex flex-wrap gap-2">{canUpdate && !TERMINAL.has(order.data.status) && order.data.status !== 'ISSUED' && <Button onClick={() => issue.mutate(undefined)} isLoading={issue.isPending} loadingLabel="Emitiendo…">Emitir orden</Button>}<Button variant="secondary" onClick={() => navigate(`/logistics/putaway/orders/${orderId}/history`)}>Revisiones</Button><Button variant="secondary" onClick={() => navigate(`/logistics/putaway/orders/${orderId}/integrity`)}>Control técnico</Button></div></div></section>
          {(issue.error || cancel.error) && <Alert variant="error">{issue.error || cancel.error}</Alert>}
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de la orden">{([
            ['check-square' as const, 'Tareas', order.data.task_count, 'bg-blue-50 text-blue-700'],
            ['check' as const, 'Completadas', order.data.completed_task_count, 'bg-emerald-50 text-emerald-700'],
            ['alert' as const, 'Con excepción', order.data.exception_task_count, order.data.exception_task_count ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-600'],
            ['timeline' as const, 'Revisión', order.data.current_revision_number, 'bg-violet-50 text-violet-700'],
          ] as const).map(([icon, label, value, color]) => <div key={label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold text-slate-950">{value}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${color}`}><LogisticsIcon name={icon} size={19} aria-hidden="true" /></span></div></div>)}</section>
          <section className="grid gap-6 lg:grid-cols-2"><div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-bold text-slate-950">Alcance operativo</h2><dl className="mt-5 space-y-4 text-sm"><div className="flex justify-between gap-4 border-b border-slate-100 pb-3"><dt className="text-slate-500">Almacén</dt><dd className="truncate font-mono text-xs text-slate-800">{order.data.warehouse_id}</dd></div><div className="flex justify-between gap-4 border-b border-slate-100 pb-3"><dt className="text-slate-500">Organización</dt><dd className="truncate font-mono text-xs text-slate-800">{order.data.organization_id}</dd></div><div className="flex justify-between gap-4"><dt className="text-slate-500">Versión de fila</dt><dd className="font-semibold text-slate-900">{order.data.row_version}</dd></div></dl></div><div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-bold text-slate-950">Hitos de ejecución</h2><dl className="mt-5 space-y-4 text-sm"><div className="flex justify-between gap-4 border-b border-slate-100 pb-3"><dt className="text-slate-500">Emitida</dt><dd className="text-slate-900">{order.data.issued_at ? new Date(order.data.issued_at).toLocaleString('es-PE') : 'Pendiente'}</dd></div><div className="flex justify-between gap-4 border-b border-slate-100 pb-3"><dt className="text-slate-500">Iniciada</dt><dd className="text-slate-900">{order.data.started_at ? new Date(order.data.started_at).toLocaleString('es-PE') : 'Pendiente'}</dd></div><div className="flex justify-between gap-4"><dt className="text-slate-500">Completada</dt><dd className="text-slate-900">{order.data.completed_at ? new Date(order.data.completed_at).toLocaleString('es-PE') : 'Pendiente'}</dd></div></dl></div></section>
        </>
      )}

      {showCancel && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true" aria-labelledby="cancel-putaway-title"><div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-xl"><h2 id="cancel-putaway-title" className="text-xl font-bold text-slate-950">Cancelar orden</h2><p className="mt-2 text-sm text-slate-500">La razón es obligatoria y quedará registrada.</p><label className="mt-5 block"><span className="text-sm font-semibold text-slate-700">Motivo</span><textarea value={cancelReason} onChange={(event) => setCancelReason(event.target.value)} rows={4} className="mt-2 w-full rounded-2xl border border-slate-200 p-3 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></label><div className="mt-5 flex justify-end gap-3"><Button variant="secondary" onClick={() => setShowCancel(false)}>Volver</Button><Button variant="danger" onClick={() => cancel.mutate(undefined)} isLoading={cancel.isPending} loadingLabel="Cancelando…" disabled={!cancelReason.trim()}>Confirmar cancelación</Button></div></div></div>}
    </div>
  )
}
