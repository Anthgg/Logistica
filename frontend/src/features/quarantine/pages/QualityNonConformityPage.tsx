import { useParams } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { QualityCaseWorkflowFrame } from '../components/QualityCaseWorkflowFrame'
import type { QualityQuarantineCaseDetailApi } from '../types/phase042-api'

export function QualityNonConformityPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const detail = useQuery<QualityQuarantineCaseDetailApi>(['phase042', 'case', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}`, undefined, { enabled: Boolean(caseId) })

  if (detail.isLoading) return <div className="space-y-4"><PageHeader title="No conformidad" /><LoadingSkeleton rows={4} /></div>
  if (detail.isError || !detail.data) return <div className="space-y-4"><PageHeader title="No conformidad" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>

  return (
    <QualityCaseWorkflowFrame title="Documento de no conformidad" description="Estado contractual de la emisión documental asociada al expediente." caseData={detail.data}>
      <section className="overflow-hidden rounded-3xl border border-amber-200 bg-amber-50 shadow-sm">
        <div className="grid gap-8 p-6 lg:grid-cols-[1fr_0.8fr] lg:p-8">
          <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">Operación no publicada</p><h2 className="mt-3 text-2xl font-bold text-slate-950">El backend de la Fase 042 no expone emisión, vista previa ni descarga de NC.</h2><p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600">La interfaz anterior llamaba rutas inexistentes y terminaba en 404. Esta vista conserva el acceso al expediente sin simular un documento ni ofrecer acciones que no pueden ejecutarse.</p></div>
          <dl className="rounded-2xl border border-amber-200 bg-white/70 p-5 text-sm"><div><dt className="text-slate-500">Caso</dt><dd className="mt-1 font-semibold text-slate-950">{detail.data.quarantine_code}</dd></div><div className="mt-4"><dt className="text-slate-500">Resultado de calidad</dt><dd className="mt-1 font-semibold capitalize text-slate-950">{detail.data.quality_result?.replaceAll('_', ' ').toLowerCase() ?? 'pendiente'}</dd></div><div className="mt-4"><dt className="text-slate-500">Siguiente paso válido</dt><dd className="mt-1 font-semibold text-slate-950">Decisión, liberación o rechazo</dd></div></dl>
        </div>
      </section>
    </QualityCaseWorkflowFrame>
  )
}
