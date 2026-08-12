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
  QualityQuarantineCaseDetailApi,
  QualityRejectionApi,
  QualityRejectionRequestApi,
} from '../types/phase042-api'

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase()
}

export function QuarantineRejectionPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestRejection)
  const canExecute = hasPermission(LOGISTICS_PERMISSIONS.quarantine.executeRejection)
  const [form, setForm] = useState<QualityRejectionRequestApi>({
    allocation_id: '',
    quality_decision_id: '',
    rejection_type: 'TOTAL',
    quantity: '',
    unit_id: '',
    base_quantity: '',
    reason: '',
    future_disposition_recommendation: '',
  })

  const detail = useQuery<QualityQuarantineCaseDetailApi>(
    ['phase042', 'case', caseId ?? ''],
    `/logistics/quality-quarantine-cases/${caseId}`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const rejections = useQuery<QualityRejectionApi[]>(
    ['phase042', 'rejections', caseId ?? ''],
    `/logistics/quality-quarantine-cases/${caseId}/rejection-authorizations`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const createRejection = useMutation(
    (payload: QualityRejectionRequestApi) => qualityQuarantineApi.createRejectionAuthorization(caseId ?? '', payload),
    { onSuccess: () => void rejections.refetch() },
  )
  const executeRejection = useMutation(
    (rejectionId: string) => qualityQuarantineApi.executeRejection(rejectionId),
    { onSuccess: () => void rejections.refetch() },
  )

  if (detail.isLoading) return <div className="space-y-4"><PageHeader title="Rechazo de cuarentena" /><LoadingSkeleton rows={5} /></div>
  if (detail.isError || !detail.data) return <div className="space-y-4"><PageHeader title="Rechazo de cuarentena" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canRequest || createRejection.isPending) return
    void createRejection.mutate({
      ...form,
      reason_code: form.reason_code?.trim() || undefined,
      reason: form.reason?.trim() || undefined,
      future_disposition_recommendation: form.future_disposition_recommendation?.trim() || undefined,
    })
  }

  return (
    <QualityCaseWorkflowFrame
      title="Rechazo controlado"
      description="Registra y ejecuta el rechazo sin mezclarlo con operaciones de aprobación que el backend no publica."
      caseData={detail.data}
    >
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form onSubmit={submit} className="space-y-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-rose-600">Nueva autorización</p><h2 className="mt-2 text-xl font-bold text-slate-950">Solicitar rechazo</h2><p className="mt-2 text-sm text-slate-500">La recomendación futura queda separada de la ejecución para no inventar movimientos de inventario.</p></div>
          <div className="grid gap-3 sm:grid-cols-2">{(['TOTAL', 'PARTIAL'] as const).map((value) => <label key={value} className={`cursor-pointer rounded-2xl border p-4 text-sm font-semibold ${form.rejection_type === value ? 'border-rose-700 bg-rose-700 text-white' : 'border-slate-200 text-slate-700'}`}><input className="sr-only" type="radio" checked={form.rejection_type === value} onChange={() => setForm((current) => ({ ...current, rejection_type: value }))} />{value === 'TOTAL' ? 'Rechazo total' : 'Rechazo parcial'}</label>)}</div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="ID de asignación" value={form.allocation_id} onChange={(event) => setForm((current) => ({ ...current, allocation_id: event.target.value }))} required />
            <Input label="ID de decisión de calidad" value={form.quality_decision_id} onChange={(event) => setForm((current) => ({ ...current, quality_decision_id: event.target.value }))} required />
            <Input label="Cantidad" type="number" min="0" step="any" value={form.quantity} onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))} required />
            <Input label="Cantidad base" type="number" min="0" step="any" value={form.base_quantity} onChange={(event) => setForm((current) => ({ ...current, base_quantity: event.target.value }))} required />
            <Input label="ID de unidad" value={form.unit_id} onChange={(event) => setForm((current) => ({ ...current, unit_id: event.target.value }))} required />
            <Input label="Código de motivo" value={form.reason_code ?? ''} onChange={(event) => setForm((current) => ({ ...current, reason_code: event.target.value }))} placeholder="Opcional" />
          </div>
          <label className="block text-sm font-semibold text-slate-700">Motivo<textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-rose-700" value={form.reason ?? ''} onChange={(event) => setForm((current) => ({ ...current, reason: event.target.value }))} /></label>
          <label className="block text-sm font-semibold text-slate-700">Recomendación de disposición futura<textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-rose-700" value={form.future_disposition_recommendation ?? ''} onChange={(event) => setForm((current) => ({ ...current, future_disposition_recommendation: event.target.value }))} /></label>
          {!canRequest && <Alert variant="warning">Tu rol puede consultar el expediente, pero no solicitar rechazos.</Alert>}
          {createRejection.error && <Alert variant="error">{getErrorMessage(createRejection.error)}</Alert>}
          <Button type="submit" variant="danger" disabled={!canRequest || !form.allocation_id || !form.quality_decision_id || !form.quantity || !form.base_quantity || !form.unit_id} isLoading={createRejection.isPending}>Crear autorización</Button>
        </form>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-rose-600">Ejecución</p><h2 className="mt-2 text-xl font-bold text-slate-950">Rechazos registrados</h2><p className="mt-2 text-sm text-slate-500">La ruta contractual disponible ejecuta una autorización existente; no existe una aprobación separada.</p>
          {rejections.isLoading ? <div className="mt-5"><LoadingSkeleton rows={4} /></div> : rejections.isError ? <div className="mt-5"><Alert variant="error">{getErrorMessage(rejections.error)}</Alert></div> : (rejections.data ?? []).length === 0 ? <p className="mt-5 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">No hay rechazos para este caso.</p> : <div className="mt-5 space-y-3">{(rejections.data ?? []).map((rejection) => <article key={rejection.id} className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold capitalize text-slate-950">{humanize(rejection.rejection_type)}</p><p className="mt-1 text-xs text-slate-500">{rejection.quantity} · {rejection.unit_id}</p></div><span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold capitalize text-rose-700">{humanize(rejection.status)}</span></div>{rejection.reason && <p className="mt-3 text-sm text-slate-600">{rejection.reason}</p>}{canExecute && rejection.status !== 'EXECUTED' && <Button className="mt-4" size="small" variant="danger" onClick={() => void executeRejection.mutate(rejection.id)} isLoading={executeRejection.isPending}>Ejecutar rechazo</Button>}</article>)}</div>}
          {executeRejection.error && <div className="mt-4"><Alert variant="error">{getErrorMessage(executeRejection.error)}</Alert></div>}
        </section>
      </div>
    </QualityCaseWorkflowFrame>
  )
}
