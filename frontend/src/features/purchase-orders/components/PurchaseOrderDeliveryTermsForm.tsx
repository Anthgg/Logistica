import { useCallback, useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { purchaseOrderSchedulesApi } from '../api/purchaseOrderSchedulesApi'
import type {
  DeliveryModality,
  FreightResponsibility,
  PurchaseOrderCapabilities,
  PurchaseOrderDeliveryTerms,
} from '../types/purchase-orders-v2'
import { deliveryModalityLabel, freightResponsibilityLabel } from '../format'
import { ErrorState } from './ui'
import { DecimalInput } from './ui'

const MODALITIES: DeliveryModality[] = ['DELIVERY', 'PICKUP', 'FCA', 'FAS', 'FOB', 'CIF', 'DAP', 'DDP', 'OTHER']
const RESPONSIBILITIES: FreightResponsibility[] = ['SUPPLIER', 'BUYER', 'SHARED']

export function PurchaseOrderDeliveryTermsForm({
  purchaseOrderId,
  capabilities,
}: {
  purchaseOrderId: string
  capabilities: PurchaseOrderCapabilities
}) {
  const [, setTerms] = useState<PurchaseOrderDeliveryTerms | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [modality, setModality] = useState<DeliveryModality>('DELIVERY')
  const [freight, setFreight] = useState<FreightResponsibility>('SUPPLIER')
  const [warehouseId, setWarehouseId] = useState<string | null>(null)
  const [partials, setPartials] = useState(false)
  const [early, setEarly] = useState(false)
  const [tolerance, setTolerance] = useState('')
  const [window, setWindow] = useState('')
  const [appointment, setAppointment] = useState(false)
  const [packaging, setPackaging] = useState('')
  const [labelling, setLabelling] = useState('')
  const [incoterm, setIncoterm] = useState('')
  const [notes, setNotes] = useState('')

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const t = await purchaseOrderSchedulesApi.getDeliveryTerms(purchaseOrderId)
      setTerms(t)
      if (t) {
        setModality(t.modality); setFreight(t.freight_responsibility)
        setWarehouseId(t.destination_warehouse_id); setPartials(t.partial_deliveries_allowed)
        setEarly(t.early_delivery_allowed); setTolerance(t.tolerance_percentage ?? '')
        setWindow(t.schedule_window ?? ''); setAppointment(t.appointment_required)
        setPackaging(t.packaging ?? ''); setLabelling(t.labelling ?? '')
        setIncoterm(t.incoterm ?? ''); setNotes(t.notes ?? '')
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las condiciones.')
    } finally {
      setIsLoading(false)
    }
  }, [purchaseOrderId])

  useEffect(() => { void load() }, [load])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await purchaseOrderSchedulesApi.updateDeliveryTerms(purchaseOrderId, {
        modality, freight_responsibility: freight,
        destination_warehouse_id: warehouseId,
        partial_deliveries_allowed: partials, early_delivery_allowed: early,
        tolerance_percentage: tolerance || null, schedule_window: window || null,
        appointment_required: appointment, packaging: packaging || null,
        labelling: labelling || null, incoterm: incoterm || null, notes: notes || null,
      })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <div className="text-xs text-slate-500">Cargando…</div>

  const readOnly = !capabilities.can_manage_terms

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <h2 className="text-sm font-bold text-slate-800">Condiciones de entrega</h2>
      {error && <ErrorState message={error} />}
      <div className="mt-3 grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Modalidad</label>
          <Select value={modality} onValueChange={(v) => setModality(v as DeliveryModality)} disabled={readOnly}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{MODALITIES.map((m) => <SelectItem key={m} value={m}>{deliveryModalityLabel(m)}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Responsable del flete</label>
          <Select value={freight} onValueChange={(v) => setFreight(v as FreightResponsibility)} disabled={readOnly}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{RESPONSIBILITIES.map((r) => <SelectItem key={r} value={r}>{freightResponsibilityLabel(r)}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">ID almacén destino</label>
          <input value={warehouseId ?? ''} onChange={(e) => setWarehouseId(e.target.value || null)} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
        </div>
        <DecimalInput label="Tolerancia (%)" value={tolerance} onChange={setTolerance} maxDecimals={4} disabled={readOnly} />
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Ventana horaria</label>
          <input value={window} onChange={(e) => setWindow(e.target.value)} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Incoterm</label>
          <input value={incoterm} onChange={(e) => setIncoterm(e.target.value)} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Empaque</label>
          <input value={packaging} onChange={(e) => setPackaging(e.target.value)} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Etiquetado</label>
          <input value={labelling} onChange={(e) => setLabelling(e.target.value)} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-4">
        <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
          <input type="checkbox" checked={partials} onChange={(e) => setPartials(e.target.checked)} disabled={readOnly} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
          Entregas parciales permitidas
        </label>
        <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
          <input type="checkbox" checked={early} onChange={(e) => setEarly(e.target.checked)} disabled={readOnly} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
          Entrega anticipada
        </label>
        <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
          <input type="checkbox" checked={appointment} onChange={(e) => setAppointment(e.target.checked)} disabled={readOnly} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
          Cita requerida
        </label>
      </div>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} disabled={readOnly} rows={2} placeholder="Observaciones" className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <p className="mt-2 rounded-lg border border-indigo-100 bg-indigo-50/40 p-2 text-[11px] text-indigo-700">
        La cita de recepción se gestionará en la Fase 036.
      </p>
      {!readOnly && (
        <button type="button" disabled={saving} onClick={handleSave} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
          {saving ? 'Guardando…' : 'Guardar condiciones'}
        </button>
      )}
    </div>
  )
}