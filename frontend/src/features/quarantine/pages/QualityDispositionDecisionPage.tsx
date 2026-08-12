import { useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
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
import type {
  QualityDecisionApi,
  QualityDecisionRequestApi,
  QualityQuarantineCaseDetailApi,
} from '../types/phase042-api'

const DECISION_OPTIONS = [
  ['APPROVE_QUALITY', 'Aprobar calidad', 'El inventario cumple el control aplicado.'],
  ['KEEP_IN_QUARANTINE', 'Mantener segregado', 'El inventario continúa bloqueado hasta nueva evidencia.'],
  ['REQUEST_REINSPECTION', 'Solicitar reinspección', 'Se requiere una nueva evaluación antes de decidir.'],
] as const

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase()
}

export function QualityDispositionDecisionPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const { hasPermission } = useLogisticsPermissions()
  const canPropose = hasPermission(LOGISTICS_PERMISSIONS.quarantine.proposeDecision)
  const canApprove = hasPermission(LOGISTICS_PERMISSIONS.quarantine.approveQuality)
  const [form, setForm] = useState<QualityDecisionRequestApi>({
    allocation_id: '',
    decision_type: 'APPROVE_QUALITY',
    quantity: '',
    unit_id: '',
    base_quantity: '',
    reason: '',
  })

  const detail = useQuery<QualityQuarantineCaseDetailApi>(
    ['phase042', 'case', caseId ?? ''],
    `/logistics/quality-quarantine-cases/${caseId}`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const decisions = useQuery<QualityDecisionApi[]>(
    ['phase042', 'decisions', caseId ?? ''],
    `/logistics/quality-quarantine-cases/${caseId}/decisions`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const createDecision = useMutation(
    (payload: QualityDecisionRequestApi) => qualityQuarantineApi.createDecision(caseId ?? '', payload),
    { onSuccess: () => void decisions.refetch() },
  )
  const approveDecision = useMutation(
    (decisionId: string) => qualityQuarantineApi.approveDecision(decisionId),
    { onSuccess: () => void decisions.refetch() },
  )

  if (detail.isLoading) {
    return <div className="space-y-4"><PageHeader title="Decisión de calidad" /><LoadingSkeleton rows={5} /></div>
  }
  if (detail.isError || !detail.data) {
    return <div className="space-y-4"><PageHeader title="Decisión de calidad" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canPropose || createDecision.isPending) return
    void createDecision.mutate({
      ...form,
      inspection_id: form.inspection_id?.trim() || undefined,
      reason: form.reason?.trim() || undefined,
    })
  }

  return (
    <QualityCaseWorkflowFrame
      title="Decisión de disposición"
      description="Propón una decisión con la asignación, unidad y cantidades exigidas por el contrato real."
      caseData={detail.data}
    >
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form onSubmit={submit} className="space-y-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Nueva propuesta</p>
            <h2 className="mt-2 text-xl font-bold text-slate-950">Definir disposición</h2>
            <p className="mt-2 text-sm text-slate-500">Los identificadores se mantienen visibles porque el backend aún no publica un selector de asignaciones por caso.</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {DECISION_OPTIONS.map(([value, label, description]) => (
              <label key={value} className={`cursor-pointer rounded-2xl border p-4 transition ${form.decision_type === value ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 hover:border-slate-400'}`}>
                <input className="sr-only" type="radio" name="decision_type" checked={form.decision_type === value} onChange={() => setForm((current) => ({ ...current, decision_type: value }))} />
                <span className="block text-sm font-semibold">{label}</span>
                <span className={`mt-2 block text-xs leading-5 ${form.decision_type === value ? 'text-slate-300' : 'text-slate-500'}`}>{description}</span>
              </label>
            ))}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="ID de asignación" value={form.allocation_id} onChange={(event) => setForm((current) => ({ ...current, allocation_id: event.target.value }))} required />
            <Input label="ID de inspección" value={form.inspection_id ?? ''} onChange={(event) => setForm((current) => ({ ...current, inspection_id: event.target.value }))} placeholder="Opcional" />
            <Input label="Cantidad" type="number" min="0" step="any" value={form.quantity} onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))} required />
            <Input label="Cantidad base" type="number" min="0" step="any" value={form.base_quantity} onChange={(event) => setForm((current) => ({ ...current, base_quantity: event.target.value }))} required />
            <Input label="ID de unidad" value={form.unit_id} onChange={(event) => setForm((current) => ({ ...current, unit_id: event.target.value }))} required />
            <Input label="Código de motivo" value={form.reason_code ?? ''} onChange={(event) => setForm((current) => ({ ...current, reason_code: event.target.value }))} placeholder="Opcional" />
          </div>
          <label className="block text-sm font-semibold text-slate-700">Justificación<textarea className="mt-2 min-h-28 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-950" value={form.reason ?? ''} onChange={(event) => setForm((current) => ({ ...current, reason: event.target.value }))} /></label>
          {!canPropose && <Alert variant="warning">Tu rol puede consultar decisiones, pero no proponerlas.</Alert>}
          {createDecision.error && <Alert variant="error">{getErrorMessage(createDecision.error)}</Alert>}
          <Button type="submit" disabled={!canPropose || !form.allocation_id || !form.quantity || !form.base_quantity || !form.unit_id} isLoading={createDecision.isPending}>Registrar propuesta</Button>
        </form>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Trazabilidad</p>
          <h2 className="mt-2 text-xl font-bold text-slate-950">Decisiones registradas</h2>
          {decisions.isLoading ? <div className="mt-5"><LoadingSkeleton rows={4} /></div> : decisions.isError ? <div className="mt-5"><Alert variant="error">{getErrorMessage(decisions.error)}</Alert></div> : (decisions.data ?? []).length === 0 ? <p className="mt-5 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">Aún no hay propuestas para este caso.</p> : <div className="mt-5 space-y-3">{(decisions.data ?? []).map((decision) => <article key={decision.id} className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold capitalize text-slate-950">{humanize(decision.decision_type)}</p><p className="mt-1 text-xs text-slate-500">{decision.quantity} · {decision.unit_id}</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-700">{humanize(decision.decision_status)}</span></div>{decision.reason && <p className="mt-3 text-sm text-slate-600">{decision.reason}</p>}{canApprove && decision.decision_status !== 'APPROVED' && <Button className="mt-4" size="small" variant="secondary" onClick={() => void approveDecision.mutate(decision.id)} isLoading={approveDecision.isPending}>Aprobar decisión</Button>}</article>)}</div>}
          {approveDecision.error && <div className="mt-4"><Alert variant="error">{getErrorMessage(approveDecision.error)}</Alert></div>}
        </section>
      </div>
    </QualityCaseWorkflowFrame>
  )
}
