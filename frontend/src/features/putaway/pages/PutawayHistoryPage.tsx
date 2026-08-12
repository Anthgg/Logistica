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

interface PutawayOrderRevisionApi { id: string; putaway_order_id: string; revision_number: number; status: string; change_reason: string | null; created_by: string; created_at: string; frozen_at: string | null }

export function PutawayHistoryPage() {
  const navigate = useNavigate()
  const { orderId = '' } = useParams()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewHistory)
  const revisions = useQuery<PutawayOrderRevisionApi[]>(['putaway', 'revisions', orderId], `/logistics/putaway/orders/${orderId}/revisions`, undefined, { enabled: canView && Boolean(orderId) })

  if (!canView) return <div className="space-y-4"><PageHeader title="Revisiones de ubicación" /><Alert variant="error">No tienes permisos para ver las revisiones.</Alert></div>

  return <div className="space-y-6 pb-10"><PageHeader eyebrow="Fase 043 · Evidencia" title="Revisiones de la orden" description="Versiones congeladas y cambios de planificación registrados por el backend." actions={<Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>} /><PutawayPhaseNav />{revisions.isLoading && <LoadingSkeleton rows={6} />}{revisions.isError && <Alert variant="error">{getErrorMessage(revisions.error)}</Alert>}{revisions.data && (revisions.data.length === 0 ? <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><LogisticsIcon name="timeline" size={26} className="mx-auto text-slate-500" aria-hidden="true" /><h2 className="mt-5 text-xl font-bold text-slate-950">Sin revisiones registradas</h2><p className="mt-2 text-sm text-slate-500">La orden todavía conserva únicamente su estado inicial.</p></div> : <ol className="relative space-y-4 border-l-2 border-slate-200 pl-7">{revisions.data.map((revision) => <li key={revision.id} className="relative rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><span className="absolute -left-[2.25rem] top-6 h-4 w-4 rounded-full border-4 border-white bg-blue-600" aria-hidden="true" /><div className="flex flex-wrap items-start justify-between gap-3"><div><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">Revisión {revision.revision_number}</span><h2 className="mt-3 font-bold text-slate-950">{revision.status.replaceAll('_', ' ')}</h2></div><time className="text-xs text-slate-500">{new Date(revision.created_at).toLocaleString('es-PE')}</time></div><p className="mt-3 text-sm leading-6 text-slate-600">{revision.change_reason ?? 'Sin motivo adicional registrado.'}</p><p className="mt-3 font-mono text-xs text-slate-400">Actor {revision.created_by}</p></li>)}</ol>)}</div>
}
