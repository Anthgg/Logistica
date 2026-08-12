import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { qualityQuarantineApi } from '../api/qualityQuarantineApi'
import { QualityCaseWorkflowFrame } from '../components/QualityCaseWorkflowFrame'
import type { QualityInspectionSummaryApi, QualityQuarantineCaseDetailApi } from '../types/phase042-api'

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase()
}

export function QualityInspectionWorkspacePage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.quarantine.materializeInspection)
  const [allocationId, setAllocationId] = useState('')
  const detail = useQuery<QualityQuarantineCaseDetailApi>(['phase042', 'case', caseId ?? ''], `/logistics/quality-quarantine-cases/${caseId}`, undefined, { enabled: Boolean(caseId) })
  const inspections = useQuery<QualityInspectionSummaryApi[]>(['phase042', 'case-inspections', caseId ?? ''], '/logistics/quality-inspections', { quarantine_case_id: caseId }, { enabled: Boolean(caseId) })
  const materialize = useMutation(
    (input: { caseId: string; allocationId: string }) => qualityQuarantineApi.materializeInspection(input.caseId, { quarantine_case_id: input.caseId, allocation_id: input.allocationId }),
    { onSuccess: (inspection) => navigate(`/logistics/quality/inspections/${inspection.id}`) },
  )

  if (detail.isLoading) return <div className="space-y-4"><PageHeader title="Inspección de calidad" /><LoadingSkeleton rows={5} /></div>
  if (detail.isError || !detail.data) return <div className="space-y-4"><PageHeader title="Inspección de calidad" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!caseId || !allocationId || !canCreate) return
    void materialize.mutate({ caseId, allocationId })
  }

  return (
    <QualityCaseWorkflowFrame title="Inspección de calidad" description="Consulta la inspección activa del caso o materializa una nueva con la asignación que exige el backend." caseData={detail.data}>
      <div className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">Inspección activa</p><h2 className="mt-2 text-xl font-bold text-slate-950">Control asociado al caso</h2>
          {inspections.isLoading ? <div className="mt-5"><LoadingSkeleton rows={4} /></div> : inspections.isError ? <div className="mt-5"><Alert variant="error">{getErrorMessage(inspections.error)}</Alert></div> : (inspections.data ?? []).length === 0 ? <div className="mt-5 rounded-2xl bg-slate-50 p-5"><p className="font-semibold text-slate-900">Aún no existe una inspección activa.</p><p className="mt-2 text-sm text-slate-500">Materialízala usando el ID de una asignación del caso.</p></div> : <div className="mt-5 space-y-3">{(inspections.data ?? []).map((inspection) => <article key={inspection.id} className="rounded-2xl border border-slate-200 p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold text-slate-950">{inspection.inspection_code}</p><p className="mt-1 text-sm capitalize text-slate-500">Resultado: {humanize(inspection.overall_result)}</p></div><span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold capitalize text-violet-700">{humanize(inspection.status)}</span></div><Button className="mt-5" size="small" onClick={() => navigate(`/logistics/quality/inspections/${inspection.id}`)}>Abrir inspección</Button></article>)}</div>}
        </section>
        <form onSubmit={submit} className="space-y-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Materialización</p><h2 className="mt-2 text-xl font-bold text-slate-950">Crear inspección</h2><p className="mt-2 text-sm leading-6 text-slate-500">El backend genera los controles predeterminados de embalaje, peso, temperatura y certificado.</p></div>
          <Input label="ID de asignación" value={allocationId} onChange={(event) => setAllocationId(event.target.value)} required />
          {!canCreate && <Alert variant="warning">Tu rol no puede materializar inspecciones.</Alert>}
          {materialize.error && <Alert variant="error">{getErrorMessage(materialize.error)}</Alert>}
          <Button type="submit" disabled={!canCreate || !allocationId || (inspections.data ?? []).length > 0} isLoading={materialize.isPending}>Materializar inspección</Button>
        </form>
      </div>
    </QualityCaseWorkflowFrame>
  )
}
