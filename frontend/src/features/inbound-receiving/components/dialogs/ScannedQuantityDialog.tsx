import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import type { InboundScanEvent, UnitOfMeasureSummary } from '../../types/inbound-receiving'

interface ScannedQuantityDialogProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: { quantity: string; unit_id: string; lot_code?: string; expiration_date?: string; comment?: string }) => void
  event: InboundScanEvent
  availableUnits: UnitOfMeasureSummary[]
  requiresLot: boolean
  requiresExpiration: boolean
  submitting?: boolean
}

export function ScannedQuantityDialog({
  open,
  onClose,
  onSubmit,
  event,
  availableUnits,
  requiresLot,
  requiresExpiration,
  submitting = false,
}: ScannedQuantityDialogProps) {
  const [quantity, setQuantity] = useState('')
  const [unitId, setUnitId] = useState(availableUnits[0]?.unit_id ?? '')
  const [lotCode, setLotCode] = useState('')
  const [expirationDate, setExpirationDate] = useState('')
  const [comment, setComment] = useState('')

  const quantityPattern = /^\d{0,12}(\.\d{0,6})?$/

  const handleQuantityChange = (raw: string) => {
    if (raw === '' || quantityPattern.test(raw)) {
      setQuantity(raw)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!quantity || !unitId) return
    onSubmit({
      quantity,
      unit_id: unitId,
      lot_code: lotCode || undefined,
      expiration_date: expirationDate || undefined,
      comment: comment || undefined,
    })
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-5 shadow-2xl">
          <Dialog.Title className="text-sm font-bold text-slate-800">Ingresar cantidad</Dialog.Title>
          <Dialog.Description className="mt-1 text-xs text-slate-500">
            Producto: {event.product?.name ?? event.raw_code}
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="mt-4 space-y-3">
            <div>
              <label htmlFor="qty-input" className="mb-1 block text-xs font-bold text-slate-700">
                Cantidad <span className="text-rose-500">*</span>
              </label>
              <input
                id="qty-input"
                type="text"
                inputMode="decimal"
                value={quantity}
                onChange={(e) => handleQuantityChange(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
                autoFocus
                required
                autoComplete="off"
              />
            </div>

            <div>
              <label htmlFor="qty-unit" className="mb-1 block text-xs font-bold text-slate-700">
                Unidad <span className="text-rose-500">*</span>
              </label>
              <select
                id="qty-unit"
                value={unitId}
                onChange={(e) => setUnitId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                required
              >
                {availableUnits.map((u) => (
                  <option key={u.unit_id} value={u.unit_id}>{u.name} ({u.symbol})</option>
                ))}
              </select>
            </div>

            {requiresLot && (
              <div>
                <label htmlFor="qty-lot" className="mb-1 block text-xs font-bold text-slate-700">Lote</label>
                <input
                  id="qty-lot"
                  type="text"
                  value={lotCode}
                  onChange={(e) => setLotCode(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
                  autoComplete="off"
                />
              </div>
            )}

            {requiresExpiration && (
              <div>
                <label htmlFor="qty-exp" className="mb-1 block text-xs font-bold text-slate-700">Vencimiento</label>
                <input
                  id="qty-exp"
                  type="date"
                  value={expirationDate}
                  onChange={(e) => setExpirationDate(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            )}

            <div>
              <label htmlFor="qty-comment" className="mb-1 block text-xs font-bold text-slate-700">Comentario</label>
              <input
                id="qty-comment"
                type="text"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                Cancelar
              </button>
              <button type="submit" disabled={!quantity || !unitId || submitting} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
                {submitting ? 'Aplicando…' : 'Aplicar'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
