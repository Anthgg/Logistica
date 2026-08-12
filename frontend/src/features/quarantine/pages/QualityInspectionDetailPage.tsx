import { useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { QualityInspectionControlApi, QualityInspectionDetailApi } from '../types/phase042-api'

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase()
}

export function QualityInspectionDetailPage() {
  const { inspectionId } = useParams<{ inspectionId: string }>()
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canStart = hasPermission(LOGISTICS_PERMISSIONS.quarantine.startInspection)
  const canComplete = hasPermission(LOGISTICS_PERMISSIONS.quarantine.completeInspection)
  const inspection = useQuery<QualityInspectionDetailApi>(['phase042', 'inspection', inspectionId ?? ''], `/logistics/quality-inspections/${inspectionId}`, undefined, { enabled: Boolean(inspectionId) })
  const controls = useQuery<QualityInspectionControlApi[]>(['phase042', 'inspection-controls', inspectionId ?? ''], `/logistics/quality-inspections/${inspectionId}/controls`, undefined, { enabled: Boolean(inspectionId) })
  const start = useMutation(() => qualityInspectionsApi.start(inspectionId ?? ''), { onSuccess: () => void inspection.refetch() })
  const complete = useMutation(() => qualityInspectionsApi.complete(inspectionId ?? ''), { onSuccess: () => void inspection.refetch() })

  if (inspection.isLoading) return <div className="space-y-4"><PageHeader title="Detalle de inspección" /><LoadingSkeleton rows={6} /></div>
  if (inspection.isError || !inspection.data) return <div className="space-y-4"><PageHeader title="Detalle de inspección" /><Alert variant="error">{inspection.error ? getErrorMessage(inspection.error) : 'Inspección no encontrada.'}</Alert></div>
  const data = inspection.data
  const progress = data.required_control_count > 0 ? Math.round((data.completed_control_count / data.required_control_count) * 100) : 0

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Fase 042 · Inspección" title={data.inspection_code} description="Ejecución de controles y resultado global con el contrato publicado por FastAPI." actions={<Button size="small" variant="secondary" onClick={() => navigate(`/logistics/quality/quarantine/${data.quarantine_case_id}`)}>Volver al caso</Button>} />
      <QualityQuarantinePhaseNav />
      <section className="rounded-3xl bg-slate-950 p-6 text-white shadow-sm lg:p-8">
        <div className="flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">Control en ejecución</p><h2 className="mt-3 text-3xl font-bold capitalize">{humanize(data.status)}</h2><p className="mt-3 text-sm text-slate-300">Asignación {data.allocation_id}</p></div><div className="min-w-72 rounded-2xl border border-white/10 bg-white/5 p-5"><div className="flex justify-between text-xs text-slate-300"><span>Progreso de controles</span><span>{data.completed_control_count}/{data.required_control_count}</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-violet-400" style={{ width: `${Math.min(progress, 100)}%` }} /></div><p className="mt-3 text-right text-2xl font-bold">{progress}%</p></div></div>
      </section>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[["Resultado", humanize(data.overall_result)], ["Controles fallidos", String(data.failed_control_count)], ["Evidencias", String(data.evidence_count)], ["Creada", new Date(data.created_at).toLocaleDateString('es-PE')]].map(([label, value]) => <article key={label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-bold capitalize text-slate-950">{value}</p></article>)}</section>
      <div className="grid gap-6 xl:grid-cols-[1fr_0.75fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">Plan materializado</p><h2 className="mt-2 text-xl font-bold text-slate-950">Controles</h2></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{(controls.data ?? []).length} controles</span></div>{controls.isLoading ? <div className="mt-5"><LoadingSkeleton rows={5} /></div> : controls.isError ? <div className="mt-5"><Alert variant="error">{getErrorMessage(controls.error)}</Alert></div> : <div className="mt-5 space-y-3">{(controls.data ?? []).map((control) => <article key={control.id} className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold text-slate-950">{control.control_code} · {control.name_snapshot}</p><p className="mt-1 text-xs capitalize text-slate-500">{humanize(control.control_type)}{control.required ? ' · obligatorio' : ''}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${control.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{humanize(control.status)}</span></div></article>)}</div>}</section>
        <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Acciones contractuales</p><h2 className="mt-2 text-xl font-bold text-slate-950">Avanzar inspección</h2><p className="mt-3 text-sm leading-6 text-slate-500">La fase publicada permite iniciar, registrar resultados de control y completar. Pausar, reanudar y cancelar no están expuestos.</p><div className="mt-6 space-y-3">{canStart && ['CREATED', 'READY', 'MATERIALIZED', 'PENDING_START'].includes(data.status) && <Button className="w-full" onClick={() => void start.mutate(undefined)} isLoading={start.isPending}>Iniciar inspección</Button>}{canComplete && data.status === 'IN_PROGRESS' && <Button className="w-full" onClick={() => void complete.mutate(undefined)} isLoading={complete.isPending}>Completar inspección</Button>}<Button className="w-full" variant="secondary" onClick={() => navigate(`/logistics/quality/quarantine/${data.quarantine_case_id}/decision`)}>Continuar a decisión</Button></div>{(start.error || complete.error) && <div className="mt-4"><Alert variant="error">{getErrorMessage(start.error ?? complete.error)}</Alert></div>}</aside>
      </div>
    </div>
  )
}
