import { useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityQuarantineApi } from '../api/qualityQuarantineApi'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { QualityQuarantineCaseDetailApi } from '../types/phase042-api'

function humanize(value: string | null): string {
  return value ? value.replaceAll('_', ' ').toLocaleLowerCase('es-PE') : 'pendiente'
}

export function QualityQuarantineDetailPage() {
  const navigate = useNavigate()
  const { caseId } = useParams<{ caseId: string }>()
  const { hasPermission } = useLogisticsPermissions()
  const canActivate = hasPermission(LOGISTICS_PERMISSIONS.quarantine.activateQuarantine)

  const detail = useQuery<QualityQuarantineCaseDetailApi>(
    ['quality-quarantine', 'case', caseId],
    `/logistics/quality-quarantine-cases/${caseId ?? ''}`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const activate = useMutation(
    () => qualityQuarantineApi.activateCase(caseId ?? ''),
    { onSuccess: () => void detail.refetch() },
  )

  if (!caseId) return <Alert variant="error">El identificador del caso es obligatorio.</Alert>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 042 · Expediente"
        title={detail.data?.quarantine_code ?? 'Detalle de cuarentena'}
        description="Vista operativa del origen, estado de calidad, segregación física y siguientes decisiones."
        actions={<Button size="small" variant="ghost" onClick={() => navigate('/logistics/quality/quarantine/cases')}>Volver a casos</Button>}
      />
      <QualityQuarantinePhaseNav />

      {detail.isLoading && <LoadingSkeleton rows={8} />}
      {detail.isError && <Alert variant="error">{getErrorMessage(detail.error)}</Alert>}

      {detail.data && (
        <>
          <section className="relative overflow-hidden rounded-3xl bg-slate-950 p-7 text-white shadow-sm md:p-9">
            <div className="absolute -right-16 -top-24 h-72 w-72 rounded-full bg-violet-500/20 blur-3xl" aria-hidden="true" />
            <div className="relative grid gap-7 lg:grid-cols-[1fr_auto] lg:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">{humanize(detail.data.source_type)}</p><h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">{detail.data.quarantine_reason ?? 'Control de calidad requerido'}</h2><p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300">Producto {detail.data.product_id} · Recepción {detail.data.inbound_receipt_id}</p></div><div className="flex flex-wrap gap-2"><span className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold">{humanize(detail.data.status)}</span><span className="rounded-full bg-orange-400/15 px-3 py-1.5 text-xs font-bold text-orange-200">Severidad {humanize(detail.data.severity)}</span></div></div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {([
              ['search' as const, 'Resultado de calidad', humanize(detail.data.quality_result), 'bg-violet-50 text-violet-700'],
              ['check-square' as const, 'Decisión', humanize(detail.data.quality_decision_status), 'bg-blue-50 text-blue-700'],
              ['lock' as const, 'Liberación', humanize(detail.data.release_status), 'bg-emerald-50 text-emerald-700'],
              ['location' as const, 'Segregación', humanize(detail.data.physical_segregation_status), 'bg-orange-50 text-orange-700'],
            ] as const).map(([icon, title, value, tone]) => <article key={title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-sm text-slate-500">{title}</p><p className="mt-2 font-bold capitalize text-slate-950">{value}</p></div><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${tone}`}><LogisticsIcon name={icon} size={20} aria-hidden="true" /></span></div></article>)}
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Acciones del expediente</p><h2 className="mt-2 text-xl font-bold text-slate-950">Continuar el flujo de calidad</h2><div className="mt-6 grid gap-3 sm:grid-cols-2"><Button variant="secondary" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}/inspection`)}>Inspección</Button><Button variant="secondary" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}/decision`)}>Decisión</Button><Button variant="secondary" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}/release`)}>Liberación</Button><Button variant="secondary" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}/rejection`)}>Rechazo</Button><Button variant="ghost" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}/document`)}>No conformidad</Button><Button variant="ghost" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}/integrity`)}>Integridad</Button></div>{canActivate && detail.data.status === 'DRAFT' && <Button className="mt-5" onClick={() => void activate.mutate(undefined)} isLoading={activate.isPending}>Activar cuarentena</Button>}{activate.error && <div className="mt-4"><Alert variant="error">{getErrorMessage(activate.error)}</Alert></div>}</div>
            <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Trazabilidad base</p><dl className="mt-5 space-y-4 text-sm"><div><dt className="text-slate-500">ID del caso</dt><dd className="mt-1 break-all font-mono text-xs font-semibold text-slate-900">{detail.data.id}</dd></div><div><dt className="text-slate-500">Recepción</dt><dd className="mt-1 break-all font-mono text-xs font-semibold text-slate-900">{detail.data.inbound_receipt_id}</dd></div><div><dt className="text-slate-500">Creado</dt><dd className="mt-1 font-semibold text-slate-900">{new Date(detail.data.created_at).toLocaleString('es-PE')}</dd></div><div><dt className="text-slate-500">Abierto</dt><dd className="mt-1 font-semibold text-slate-900">{detail.data.opened_at ? new Date(detail.data.opened_at).toLocaleString('es-PE') : 'Aún no activado'}</dd></div></dl></aside>
          </section>
        </>
      )}
    </div>
  )
}
