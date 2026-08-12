import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { getErrorMessage } from '../../../utils/errors'
import { PutawayPhaseNav } from '../components/PutawayPhaseNav'
import type { PutawayOrderApi } from '../types/putaway-api'

interface RevisionApi { id: string; revision_number: number; status: string; created_at: string; frozen_at: string | null }

export function PutawayIntegrityPage() {
  const navigate = useNavigate()
  const { orderId = '' } = useParams()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewIntegrity)
  const order = useQuery<PutawayOrderApi>(['putaway', 'integrity-order', orderId], `/logistics/putaway/orders/${orderId}`, undefined, { enabled: canView && Boolean(orderId) })
  const revisions = useQuery<RevisionApi[]>(['putaway', 'integrity-revisions', orderId], `/logistics/putaway/orders/${orderId}/revisions`, undefined, { enabled: canView && Boolean(orderId) })

  if (!canView) return <div className="space-y-4"><PageHeader title="Control técnico de ubicación" /><Alert variant="error">No tienes permisos para ver el control técnico.</Alert></div>
  const loading = order.isLoading || revisions.isLoading
  const error = order.error || revisions.error
  return <div className="space-y-6 pb-10"><PageHeader eyebrow="Fase 043 · Control técnico" title="Consistencia de la orden" description="Comprueba estado, versión de fila, revisiones y conteos publicados sin inventar un hash inexistente." actions={<Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>} /><PutawayPhaseNav />{loading && <LoadingSkeleton rows={6} />}{error && <Alert variant="error">{getErrorMessage(error)}</Alert>}{order.data && revisions.data && <><section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm md:p-8"><div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-4"><span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white"><LogisticsIcon name="shield" size={25} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">Contrato consistente</p><h2 className="mt-1 text-2xl font-bold text-emerald-950">{order.data.order_code}</h2><p className="mt-1 text-sm text-emerald-800">La orden y sus revisiones respondieron desde endpoints efectivos.</p></div></div><span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-emerald-700 ring-1 ring-emerald-200">{order.data.status}</span></div></section><section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[['Versión de fila', order.data.row_version], ['Revisión actual', order.data.current_revision_number], ['Revisiones registradas', revisions.data.length], ['Tareas declaradas', order.data.task_count]].map(([label, value]) => <div key={String(label)} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold text-slate-950">{value}</p></div>)}</section><Alert variant="info">La Fase 043 no publica un endpoint de hash o “integrity report”. La integridad criptográfica de los movimientos materializados pertenece al ledger de la Fase 044.</Alert></>}</div>
}
