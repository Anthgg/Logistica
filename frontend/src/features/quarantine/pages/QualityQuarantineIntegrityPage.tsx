import { useParams } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { QualityCaseWorkflowFrame } from '../components/QualityCaseWorkflowFrame'
import type { QualityIntegrityApi, QualityQuarantineCaseDetailApi } from '../types/phase042-api'

export function QualityQuarantineIntegrityPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const detail = useQuery<QualityQuarantineCaseDetailApi>(['phase042', 'case', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}`, undefined, { enabled: Boolean(caseId) })
  const integrity = useQuery<QualityIntegrityApi>(['phase042', 'integrity', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}/integrity`, undefined, { enabled: Boolean(caseId) })

  if (detail.isLoading || integrity.isLoading) return <div className="space-y-4"><PageHeader title="Integridad del expediente" /><LoadingSkeleton rows={5} /></div>
  if (detail.isError || !detail.data) return <div className="space-y-4"><PageHeader title="Integridad del expediente" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>

  return (
    <QualityCaseWorkflowFrame title="Integridad del expediente" description="Verifica la huella canónica que entrega el backend para el caso y sus asignaciones observadas." caseData={detail.data}>
      {integrity.isError || !integrity.data ? <Alert variant="error">{integrity.error ? getErrorMessage(integrity.error) : 'No hay respuesta de integridad.'}</Alert> : <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <section className={`rounded-3xl border p-6 shadow-sm ${integrity.data.verified ? 'border-emerald-200 bg-emerald-50' : 'border-rose-200 bg-rose-50'}`}>
          <p className={`text-xs font-semibold uppercase tracking-[0.16em] ${integrity.data.verified ? 'text-emerald-700' : 'text-rose-700'}`}>Resultado de verificación</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-950">{integrity.data.verified ? 'Huella válida' : 'Revisión requerida'}</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">La Fase 042 calcula una huella canónica; no es blockchain ni una firma digital.</p>
          <div className="mt-6 rounded-2xl border border-black/5 bg-white/70 p-4"><p className="text-xs font-semibold text-slate-500">Hash general</p><p className="mt-2 break-all font-mono text-xs text-slate-800">{integrity.data.overall_hash}</p></div>
        </section>
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Componentes</p><h2 className="mt-2 text-xl font-bold text-slate-950">Material incluido</h2>
          <dl className="mt-5 grid gap-3 sm:grid-cols-2">{Object.entries(integrity.data.components).map(([key, value]) => <div key={key} className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><dt className="text-xs font-semibold capitalize text-slate-500">{key.replaceAll('_', ' ')}</dt><dd className="mt-2 break-all font-mono text-xs text-slate-900">{String(value)}</dd></div>)}</dl>
        </section>
      </div>}
    </QualityCaseWorkflowFrame>
  )
}
