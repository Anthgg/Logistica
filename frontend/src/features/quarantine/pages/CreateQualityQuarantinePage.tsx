import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityQuarantineApi } from '../api/qualityQuarantineApi'
import { QualityQuarantineContextEmptyState } from '../components/QualityQuarantineContextEmptyState'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { CreateQuarantineCaseRequest } from '../types/quarantine'

const INITIAL_FORM: CreateQuarantineCaseRequest = {
  source_type: 'INBOUND_RECEIPT',
  inbound_receipt_id: '',
  product_id: '',
  quarantine_reason: '',
  reason_description: '',
}

export function CreateQualityQuarantinePage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.quarantine.createQuarantine)
  const [form, setForm] = useState(INITIAL_FORM)

  const create = useMutation(
    (payload: CreateQuarantineCaseRequest) => qualityQuarantineApi.createCase(payload),
    { onSuccess: (result) => navigate(`/logistics/quality/quarantine/${result.id}`, { replace: true }) },
  )

  const update = (field: keyof CreateQuarantineCaseRequest, value: string) => setForm((current) => ({ ...current, [field]: value }))
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!form.inbound_receipt_id.trim() || !form.product_id.trim()) return
    const payload: CreateQuarantineCaseRequest = {
      source_type: form.source_type.trim(),
      inbound_receipt_id: form.inbound_receipt_id.trim(),
      product_id: form.product_id.trim(),
    }
    if (form.product_version_id?.trim()) payload.product_version_id = form.product_version_id.trim()
    if (form.quarantine_reason?.trim()) payload.quarantine_reason = form.quarantine_reason.trim()
    if (form.reason_description?.trim()) payload.reason_description = form.reason_description.trim()
    void create.mutate(payload)
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 042 · Nuevo expediente" title="Crear caso de cuarentena" description="Registra el origen y el producto con el contrato mínimo que acepta el backend." actions={<Button size="small" variant="ghost" onClick={() => navigate('/logistics/quality/quarantine/cases')}>Cancelar</Button>} />
      <QualityQuarantinePhaseNav />

      {!currentContext.warehouse_id && <QualityQuarantineContextEmptyState title="Selecciona el almacén del nuevo caso" description="El backend toma organización, sede y almacén del contexto activo al crear el expediente." />}
      {currentContext.warehouse_id && !canCreate && <Alert variant="error">No tienes permiso para crear casos de cuarentena.</Alert>}

      {currentContext.warehouse_id && canCreate && (
        <form onSubmit={submit} className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8"><div className="flex items-center gap-3"><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-50 text-orange-700"><LogisticsIcon name="archive" size={22} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Datos obligatorios</p><h2 className="mt-1 text-xl font-bold text-slate-950">Origen de la cuarentena</h2></div></div><div className="mt-7 grid gap-5 sm:grid-cols-2"><label><span className="text-sm font-semibold text-slate-700">Tipo de origen</span><select value={form.source_type} onChange={(event) => update('source_type', event.target.value)} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"><option value="INBOUND_RECEIPT">Recepción de entrada</option><option value="RECEPTION_DIFFERENCE">Diferencia de recepción</option><option value="MANUAL">Registro manual</option></select></label><Input label="ID de recepción" required placeholder="UUID de la recepción" value={form.inbound_receipt_id} onChange={(event) => update('inbound_receipt_id', event.target.value)} /><Input label="ID de producto" required placeholder="UUID del producto" value={form.product_id} onChange={(event) => update('product_id', event.target.value)} /><Input label="ID de versión del producto" placeholder="Opcional" value={form.product_version_id ?? ''} onChange={(event) => update('product_version_id', event.target.value)} /></div><div className="mt-5 grid gap-5"><Input label="Motivo de cuarentena" placeholder="Ej. daño visible, temperatura, documentación" value={form.quarantine_reason ?? ''} onChange={(event) => update('quarantine_reason', event.target.value)} /><label><span className="text-sm font-semibold text-slate-700">Descripción</span><textarea value={form.reason_description ?? ''} onChange={(event) => update('reason_description', event.target.value)} rows={5} placeholder="Describe los hallazgos que justifican el control…" className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label></div>{create.error && <div className="mt-5"><Alert variant="error">{getErrorMessage(create.error)}</Alert></div>}<div className="mt-7 flex flex-wrap justify-end gap-3"><Button type="button" variant="ghost" onClick={() => navigate('/logistics/quality/quarantine/cases')}>Volver</Button><Button type="submit" disabled={!form.inbound_receipt_id.trim() || !form.product_id.trim()} isLoading={create.isPending}>Crear expediente</Button></div></section>
          <aside className="h-fit rounded-3xl bg-slate-950 p-7 text-white shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Qué ocurre después</p><h2 className="mt-2 text-2xl font-bold">El caso nace en borrador</h2><p className="mt-4 text-sm leading-6 text-slate-300">La activación abre formalmente la cuarentena. La inspección, decisión y liberación se gestionan como etapas posteriores con permisos separados.</p><div className="mt-7 space-y-3">{['Se conserva la recepción y el producto de origen', 'El almacén viene del contexto logístico', 'No se envían campos que el contrato no reconoce'].map((item) => <div key={item} className="flex gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 text-sm text-slate-200"><LogisticsIcon name="check" size={17} className="mt-0.5 shrink-0 text-emerald-300" aria-hidden="true" /><span>{item}</span></div>)}</div></aside>
        </form>
      )}
    </div>
  )
}
