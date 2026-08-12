import { useMemo } from 'react'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useParams } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { QualityCaseWorkflowFrame } from '../components/QualityCaseWorkflowFrame'
import type {
  QualityDecisionApi,
  QualityQuarantineCaseDetailApi,
  QualityRejectionApi,
  QualityReleaseApi,
} from '../types/phase042-api'

interface TimelineItem {
  id: string
  title: string
  description: string
  timestamp: string
  tone: string
}

export function QualityQuarantineHistoryPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const detail = useQuery<QualityQuarantineCaseDetailApi>(['phase042', 'case', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}`, undefined, { enabled: Boolean(caseId) })
  const decisions = useQuery<QualityDecisionApi[]>(['phase042', 'history-decisions', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}/decisions`, undefined, { enabled: Boolean(caseId) })
  const releases = useQuery<QualityReleaseApi[]>(['phase042', 'history-releases', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}/release-authorizations`, undefined, { enabled: Boolean(caseId) })
  const rejections = useQuery<QualityRejectionApi[]>(['phase042', 'history-rejections', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}/rejection-authorizations`, undefined, { enabled: Boolean(caseId) })

  const items = useMemo<TimelineItem[]>(() => {
    if (!detail.data) return []
    const result: TimelineItem[] = [{ id: `case-${detail.data.id}`, title: 'Caso registrado', description: `Estado inicial: ${detail.data.status}`, timestamp: detail.data.created_at, tone: 'bg-blue-600' }]
    if (detail.data.opened_at) result.push({ id: `opened-${detail.data.id}`, title: 'Cuarentena activada', description: `Severidad ${detail.data.severity}`, timestamp: detail.data.opened_at, tone: 'bg-orange-500' })
    for (const decision of decisions.data ?? []) {
      result.push({ id: `decision-${decision.id}`, title: 'Decisión propuesta', description: `${decision.decision_type} · ${decision.quantity}`, timestamp: decision.proposed_at, tone: 'bg-violet-600' })
      if (decision.approved_at) result.push({ id: `decision-approved-${decision.id}`, title: 'Decisión aprobada', description: decision.decision_type, timestamp: decision.approved_at, tone: 'bg-emerald-600' })
    }
    for (const release of releases.data ?? []) {
      result.push({ id: `release-${release.id}`, title: 'Liberación solicitada', description: `${release.release_type} · ${release.quantity}`, timestamp: release.requested_at, tone: 'bg-cyan-600' })
      if (release.executed_at) result.push({ id: `release-executed-${release.id}`, title: 'Liberación ejecutada', description: release.status, timestamp: release.executed_at, tone: 'bg-emerald-600' })
    }
    for (const rejection of rejections.data ?? []) result.push({ id: `rejection-${rejection.id}`, title: 'Rechazo solicitado', description: `${rejection.rejection_type} · ${rejection.quantity}`, timestamp: rejection.requested_at, tone: 'bg-rose-600' })
    return result.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }, [detail.data, decisions.data, releases.data, rejections.data])

  if (detail.isLoading) return <div className="space-y-4"><PageHeader title="Historial del expediente" /><LoadingSkeleton rows={6} /></div>
  if (detail.isError || !detail.data) return <div className="space-y-4"><PageHeader title="Historial del expediente" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>

  const secondaryError = decisions.error ?? releases.error ?? rejections.error

  return (
    <QualityCaseWorkflowFrame title="Historia contractual" description="Cronología derivada de casos, decisiones, liberaciones y rechazos reales; no consulta un endpoint de historial inexistente." caseData={detail.data}>
      {secondaryError && <Alert variant="warning">Parte de la cronología no pudo cargarse: {getErrorMessage(secondaryError)}</Alert>}
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Trazabilidad</p><h2 className="mt-2 text-xl font-bold text-slate-950">Eventos observables</h2></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length} eventos</span></div>
        <div className="relative mt-8 space-y-6 before:absolute before:bottom-2 before:left-[7px] before:top-2 before:w-px before:bg-slate-200">
          {items.map((item) => <article key={item.id} className="relative grid grid-cols-[16px_1fr] gap-4"><span className={`relative z-10 mt-2 h-4 w-4 rounded-full border-4 border-white ${item.tone}`} /><div className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-slate-950">{item.title}</h3><p className="mt-1 text-sm capitalize text-slate-500">{item.description.replaceAll('_', ' ').toLowerCase()}</p></div><time className="text-xs text-slate-400">{new Date(item.timestamp).toLocaleString('es-PE')}</time></div></div></article>)}
        </div>
      </section>
    </QualityCaseWorkflowFrame>
  )
}
