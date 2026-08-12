import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import type { InboundScanEvent, CompensateScanRequest } from '../../types/inbound-receiving'

interface CompensateScanDialogProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: CompensateScanRequest) => void
  event: InboundScanEvent
  submitting?: boolean
}

export function CompensateScanDialog({ open, onClose, onSubmit, event, submitting = false }: CompensateScanDialogProps) {
  const [reason, setReason] = useState('')
  const [quantityToCompensate, setQuantityToCompensate] = useState('')
  const [confirmed, setConfirmed] = useState(false)

  const quantityPattern = /^\d{0,12}(\.\d{0,6})?$/

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || !confirmed) return
    onSubmit({
      event_id: event.event_id,
      reason: reason.trim(),
      quantity_to_compensate: quantityToCompensate || undefined,
    })
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-5 shadow-2xl">
          <Dialog.Title className="text-sm font-bold text-slate-800">Compensar escaneo</Dialog.Title>

          <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs">
            <p><span className="font-semibold">Código:</span> {event.raw_code}</p>
            {event.product && <p><span className="font-semibold">Producto:</span> {event.product.name}</p>}
            <p><span className="font-semibold">Cantidad:</span> {event.applied_quantity ?? '—'} {event.unit?.symbol ?? ''}</p>
            <p><span className="font-semibold">Hora:</span> {event.server_timestamp}</p>
            <p><span className="font-semibold">Operador:</span> {event.operator.display_name}</p>
          </div>

          <p className="mt-2 text-[10px] text-amber-700">
            El evento original no será eliminado. La compensación quedará registrada.
          </p>

          <form onSubmit={handleSubmit} className="mt-3 space-y-3">
            <div>
              <label htmlFor="comp-reason" className="mb-1 block text-xs font-bold text-slate-700">
                Motivo <span className="text-rose-500">*</span>
              </label>
              <input id="comp-reason" type="text" value={reason} onChange={(e) => setReason(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" required autoFocus />
            </div>

            <div>
              <label htmlFor="comp-qty" className="mb-1 block text-xs font-bold text-slate-700">Cantidad a compensar</label>
              <input
                id="comp-qty"
                type="text"
                inputMode="decimal"
                value={quantityToCompensate}
                onChange={(e) => { if (e.target.value === '' || quantityPattern.test(e.target.value)) setQuantityToCompensate(e.target.value) }}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
                placeholder="Dejar vacío para compensación total"
                autoComplete="off"
              />
            </div>

            <label className="flex items-center gap-2 text-xs">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} className="h-4 w-4 rounded border-slate-300" />
              <span>Confirmo que deseo compensar este escaneo</span>
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
              <button type="submit" disabled={!reason.trim() || !confirmed || submitting} className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50">
                {submitting ? 'Compensando…' : 'Compensar'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
