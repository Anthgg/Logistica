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
  QualityReleaseApi,
  QualityReleaseRequestApi,
} from '../types/phase042-api'

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase()
}

export function QuarantineReleasePage() {
  const { caseId } = useParams<{ caseId: string }>()
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestRelease)
  const canExecute = hasPermission(LOGISTICS_PERMISSIONS.quarantine.executeRelease)
  const [form, setForm] = useState<QualityReleaseRequestApi>({
    allocation_id: '',
    quality_decision_id: '',
    release_type: 'TOTAL',
    quantity: '',
    unit_id: '',
    base_quantity: '',
    release_reason: '',
  })

  const detail = useQuery<QualityQuarantineCaseDetailApi>(
    ['phase042', 'case', caseId ?? ''],
    `/logistics/quality-quarantine-cases/${caseId}`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const releases = useQuery<QualityReleaseApi[]>(
    ['phase042', 'releases', caseId ?? ''],
    `/logistics/quality-quarantine-cases/${caseId}/release-authorizations`,
    undefined,
    { enabled: Boolean(caseId) },
  )
  const createRelease = useMutation(
    (payload: QualityReleaseRequestApi) => qualityQuarantineApi.createReleaseAuthorization(caseId ?? '', payload),
    { onSuccess: () => void releases.refetch() },
  )
  const executeRelease = useMutation(
    (releaseId: string) => qualityQuarantineApi.executeRelease(releaseId),
    { onSuccess: () => void releases.refetch() },
  )

  if (detail.isLoading) return <div className="space-y-4"><PageHeader title="Liberación de cuarentena" /><LoadingSkeleton rows={5} /></div>
  if (detail.isError || !detail.data) return <div className="space-y-4"><PageHeader title="Liberación de cuarentena" /><Alert variant="error">{detail.error ? getErrorMessage(detail.error) : 'Caso no encontrado.'}</Alert></div>

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canRequest || createRelease.isPending) return
    void createRelease.mutate({ ...form, release_reason: form.release_reason?.trim() || undefined })
  }

  return (
    <QualityCaseWorkflowFrame
      title="Liberación de cuarentena"
      description="Solicita y ejecuta una liberación usando únicamente las operaciones publicadas por la Fase 042."
      caseData={detail.data}
    >
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form onSubmit={submit} className="space-y-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Nueva autorización</p><h2 className="mt-2 text-xl font-bold text-slate-950">Solicitar liberación</h2><p className="mt-2 text-sm text-slate-500">La decisión de calidad debe existir antes de liberar la asignación.</p></div>
          <div className="grid gap-3 sm:grid-cols-2">
            {(['TOTAL', 'PARTIAL'] as const).map((value) => <label key={value} className={`cursor-pointer rounded-2xl border p-4 text-sm font-semibold ${form.release_type === value ? 'border-emerald-700 bg-emerald-700 text-white' : 'border-slate-200 text-slate-700'}`}><input className="sr-only" type="radio" checked={form.release_type === value} onChange={() => setForm((current) => ({ ...current, release_type: value }))} />{value === 'TOTAL' ? 'Liberación total' : 'Liberación parcial'}</label>)}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="ID de asignación" value={form.allocation_id} onChange={(event) => setForm((current) => ({ ...current, allocation_id: event.target.value }))} required />
            <Input label="ID de decisión aprobada" value={form.quality_decision_id} onChange={(event) => setForm((current) => ({ ...current, quality_decision_id: event.target.value }))} required />
            <Input label="Cantidad" type="number" min="0" step="any" value={form.quantity} onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))} required />
            <Input label="Cantidad base" type="number" min="0" step="any" value={form.base_quantity} onChange={(event) => setForm((current) => ({ ...current, base_quantity: event.target.value }))} required />
            <Input label="ID de unidad" value={form.unit_id} onChange={(event) => setForm((current) => ({ ...current, unit_id: event.target.value }))} required />
          </div>
          <label className="block text-sm font-semibold text-slate-700">Motivo de liberación<textarea className="mt-2 min-h-28 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-emerald-700" value={form.release_reason ?? ''} onChange={(event) => setForm((current) => ({ ...current, release_reason: event.target.value }))} /></label>
          {!canRequest && <Alert variant="warning">Tu rol puede consultar el expediente, pero no solicitar liberaciones.</Alert>}
          {createRelease.error && <Alert variant="error">{getErrorMessage(createRelease.error)}</Alert>}
          <Button type="submit" disabled={!canRequest || !form.allocation_id || !form.quality_decision_id || !form.quantity || !form.base_quantity || !form.unit_id} isLoading={createRelease.isPending}>Crear autorización</Button>
        </form>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Ejecución</p>
          <h2 className="mt-2 text-xl font-bold text-slate-950">Autorizaciones registradas</h2>
          <p className="mt-2 text-sm text-slate-500">El backend actual no publica una aprobación separada para liberaciones: la operación disponible es ejecutar la autorización creada.</p>
          {releases.isLoading ? <div className="mt-5"><LoadingSkeleton rows={4} /></div> : releases.isError ? <div className="mt-5"><Alert variant="error">{getErrorMessage(releases.error)}</Alert></div> : (releases.data ?? []).length === 0 ? <p className="mt-5 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">No hay autorizaciones para este caso.</p> : <div className="mt-5 space-y-3">{(releases.data ?? []).map((release) => <article key={release.id} className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold capitalize text-slate-950">{humanize(release.release_type)}</p><p className="mt-1 text-xs text-slate-500">{release.quantity} · {release.unit_id}</p></div><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold capitalize text-emerald-700">{humanize(release.status)}</span></div>{canExecute && !release.executed_at && <Button className="mt-4" size="small" onClick={() => void executeRelease.mutate(release.id)} isLoading={executeRelease.isPending}>Ejecutar liberación</Button>}</article>)}</div>}
          {executeRelease.error && <div className="mt-4"><Alert variant="error">{getErrorMessage(executeRelease.error)}</Alert></div>}
        </section>
      </div>
    </QualityCaseWorkflowFrame>
  )
}
