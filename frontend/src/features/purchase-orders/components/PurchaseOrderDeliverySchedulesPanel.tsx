import { useState } from 'react'
import { purchaseOrderSchedulesApi } from '../api/purchaseOrderSchedulesApi'
import type {
  PurchaseOrderCapabilities,
  PurchaseOrderDeliverySchedule,
  PurchaseOrderLine,
} from '../types/purchase-orders-v2'
import { EmptyState, ErrorState, StatusPill } from './ui'
import { Modal, DecimalInput } from './ui'

export function PurchaseOrderDeliverySchedulesPanel({
  purchaseOrderId,
  schedules,
  lines,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  schedules: PurchaseOrderDeliverySchedule[]
  lines: PurchaseOrderLine[]
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [date, setDate] = useState('')
  const [timeStart, setTimeStart] = useState('')
  const [timeEnd, setTimeEnd] = useState('')
  const [timezone, setTimezone] = useState('America/Lima')
  const [warehouseId, setWarehouseId] = useState('')
  const [instructions, setInstructions] = useState('')
  const [quantities, setQuantities] = useState<Record<string, string>>({})

  const readOnly = !capabilities.can_manage_schedules

  const handleCreate = async () => {
    if (!date) { setError('Fecha obligatoria.'); return }
    setSubmitting(true)
    setError(null)
    try {
      await purchaseOrderSchedulesApi.create(purchaseOrderId, {
        date,
        time_start: timeStart || null,
        time_end: timeEnd || null,
        timezone,
        destination_warehouse_id: warehouseId || null,
        instructions: instructions || null,
        lines: lines.map((l) => ({ line_id: l.id, quantity_this_delivery: quantities[l.id] ?? '0' })).filter((x) => x.quantity_this_delivery && x.quantity_this_delivery !== '0'),
      })
      setOpen(false)
      setDate(''); setTimeStart(''); setTimeEnd(''); setInstructions('')
      setQuantities({})
      onChanged()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la entrega.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">No se marca como recibida o completada desde aquí.</p>
        {!readOnly && (
          <button type="button" onClick={() => setOpen(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
            Nueva entrega
          </button>
        )}
      </div>

      {schedules.length === 0 ? (
        <EmptyState title="Sin entregas programadas" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">N.º</th>
                <th className="px-3 py-2.5 text-left">Fecha</th>
                <th className="px-3 py-2.5 text-left">Ventana</th>
                <th className="px-3 py-2.5 text-left">Zona horaria</th>
                <th className="px-3 py-2.5 text-left">Destino</th>
                <th className="px-3 py-2.5 text-right">Líneas</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {schedules.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 font-mono">{s.schedule_number}</td>
                  <td className="px-3 py-2">{s.date}</td>
                  <td className="px-3 py-2">{s.time_start ?? '—'} - {s.time_end ?? '—'}</td>
                  <td className="px-3 py-2">{s.timezone}</td>
                  <td className="px-3 py-2">{s.destination_warehouse_id ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{s.lines.length}</td>
                  <td className="px-3 py-2"><StatusPill tone={s.status === 'CANCELLED' ? 'danger' : s.status === 'VALIDATED' ? 'success' : 'muted'}>{s.status}</StatusPill></td>
                  <td className="px-3 py-2 text-right">
                    {!readOnly && s.status === 'DRAFT' && (
                      <button type="button" onClick={async () => { try { await purchaseOrderSchedulesApi.validate(purchaseOrderId, s.id); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo validar.') } }} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Validar</button>
                    )}
                    {!readOnly && s.status !== 'CANCELLED' && (
                      <button type="button" onClick={async () => { try { await purchaseOrderSchedulesApi.cancel(purchaseOrderId, s.id); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo cancelar.') } }} className="ml-1 rounded border border-rose-200 px-2 py-0.5 text-[11px] font-semibold text-rose-700 hover:bg-rose-50">Cancelar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Nueva entrega parcial"
        size="lg"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Creando…' : 'Crear'}</button>
          </>
        }
      >
        <div className="space-y-3">
          {error && <ErrorState message={error} />}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Fecha</label><input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Zona horaria</label><input value={timezone} onChange={(e) => setTimezone(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Hora inicial</label><input type="time" value={timeStart} onChange={(e) => setTimeStart(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
            <div><label className="mb-1 block text-xs font-bold text-slate-700">Hora final</label><input type="time" value={timeEnd} onChange={(e) => setTimeEnd(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
          </div>
          <div><label className="mb-1 block text-xs font-bold text-slate-700">ID almacén destino</label><input value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" /></div>
          <textarea value={instructions} onChange={(e) => setInstructions(e.target.value)} placeholder="Instrucciones" rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <div className="rounded-lg border border-slate-100">
            <div className="bg-slate-50 px-2 py-1 text-[11px] font-semibold uppercase text-slate-500">Líneas</div>
            <ul className="divide-y divide-slate-100">
              {lines.map((l) => (
                <li key={l.id} className="grid grid-cols-3 items-center gap-2 px-2 py-1.5 text-xs">
                  <span className="col-span-2">{l.product_name}</span>
                  <DecimalInput value={quantities[l.id] ?? ''} onChange={(v) => setQuantities((q) => ({ ...q, [l.id]: v }))} maxDecimals={6} placeholder={`Ordenado: ${l.ordered_quantity}`} />
                </li>
              ))}
            </ul>
          </div>
          <p className="text-[11px] text-slate-500">Los cálculos finales de pendiente/disponible vienen del backend.</p>
        </div>
      </Modal>
    </div>
  )
}