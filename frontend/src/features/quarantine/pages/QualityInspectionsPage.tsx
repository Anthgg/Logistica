import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { QualityInspectionSummaryApi } from '../types/phase042-api'

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLocaleLowerCase('es-PE')
}

export function QualityInspectionsPage() {
  const navigate = useNavigate()
  const [draftCaseId, setDraftCaseId] = useState('')
  const [caseId, setCaseId] = useState('')

  const inspections = useQuery<QualityInspectionSummaryApi[]>(
    ['quality-quarantine', 'inspections', caseId],
    '/logistics/quality-inspections',
    caseId ? { quarantine_case_id: caseId } : undefined,
    { enabled: Boolean(caseId) },
  )

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 042 · Ejecución" title="Inspecciones de calidad" description="Consulta la inspección activa de un expediente sin inventar una bandeja global que el backend no publica." />
      <QualityQuarantinePhaseNav />

      <section className="grid gap-6 lg:grid-cols-[1fr_0.7fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm md:p-6"><Input label="ID del caso de cuarentena" placeholder="UUID del expediente" value={draftCaseId} onChange={(event) => setDraftCaseId(event.target.value)} /><div className="mt-5 flex flex-wrap gap-3"><Button onClick={() => setCaseId(draftCaseId.trim())} disabled={!draftCaseId.trim()}>Consultar inspección</Button><Button variant="ghost" onClick={() => navigate('/logistics/quality/quarantine/cases')}>Buscar en casos</Button></div></div>
        <aside className="rounded-3xl bg-slate-950 p-6 text-white shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Contrato real</p><h2 className="mt-2 text-xl font-bold">Una inspección por caso activo</h2><p className="mt-3 text-sm leading-6 text-slate-300">`GET /quality-inspections` exige `quarantine_case_id` para devolver la inspección activa; sin ese alcance responde una lista vacía.</p></aside>
      </section>

      {inspections.isLoading && <LoadingSkeleton rows={4} />}
      {inspections.isError && <Alert variant="error">{getErrorMessage(inspections.error)}</Alert>}

      {caseId && !inspections.isLoading && !inspections.isError && (inspections.data ?? []).length === 0 && <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="search" size={24} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-slate-950">El caso no tiene una inspección activa</h2><p className="mt-2 text-sm text-slate-500">Ábrelo para materializar la inspección o revisar su estado.</p><Button className="mt-6" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}`)}>Abrir caso</Button></section>}

      {(inspections.data ?? []).map((row) => <article key={row.id} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><div><p className="font-mono text-xs font-bold text-violet-700">{row.inspection_code}</p><h2 className="mt-2 text-2xl font-bold text-slate-950">Inspección vinculada</h2><p className="mt-2 text-sm text-slate-500">Resultado: {humanize(row.overall_result)}</p></div><span className="w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700 ring-1 ring-blue-100">{humanize(row.status)}</span></div><div className="mt-6 flex flex-wrap gap-3"><Button onClick={() => navigate(`/logistics/quality/inspections/${row.id}`)}>Abrir inspección</Button><Button variant="ghost" onClick={() => navigate(`/logistics/quality/quarantine/${caseId}`)}>Ver caso</Button></div></article>)}
    </div>
  )
}
