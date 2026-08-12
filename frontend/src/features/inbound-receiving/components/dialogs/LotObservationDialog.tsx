import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import type { ProductSummary, UnitOfMeasureSummary, CreateLotObservationRequest } from '../../types/inbound-receiving'

interface LotObservationDialogProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: CreateLotObservationRequest) => void
  product: ProductSummary
  lineId: string
  availableUnits: UnitOfMeasureSummary[]
  submitting?: boolean
}

export function LotObservationDialog({
  open,
  onClose,
  onSubmit,
  product,
  lineId,
  availableUnits,
  submitting = false,
}: LotObservationDialogProps) {
  const [lotCode, setLotCode] = useState('')
  const [quantity, setQuantity] = useState('')
  const [unitId, setUnitId] = useState(availableUnits[0]?.unit_id ?? '')
  const [manufacturingDate, setManufacturingDate] = useState('')
  const [expirationDate, setExpirationDate] = useState('')
  const [comment, setComment] = useState('')

  const quantityPattern = /^\d{0,12}(\.\d{0,6})?$/

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!lotCode.trim() || !quantity || !unitId) return
    onSubmit({
      line_id: lineId,
      lot_code: lotCode.trim(),
      quantity,
      unit_id: unitId,
      manufacturing_date: manufacturingDate || undefined,
      expiration_date: expirationDate || undefined,
      source: 'MANUAL',
      comment: comment || undefined,
    })
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-5 shadow-2xl">
          <Dialog.Title className="text-sm font-bold text-slate-800">Observación de lote</Dialog.Title>
          <Dialog.Description className="mt-1 text-xs text-slate-500">
            {product.name} (SKU: {product.sku})
          </Dialog.Description>

          <p className="mt-2 rounded bg-blue-50 px-2 py-1 text-[10px] text-blue-700">
            Esta es una observación de recepción, no un lote inventariado.
          </p>

          <form onSubmit={handleSubmit} className="mt-3 space-y-3">
            <div>
              <label htmlFor="lot-code" className="mb-1 block text-xs font-bold text-slate-700">
                Lote <span className="text-rose-500">*</span>
              </label>
              <input
                id="lot-code"
                type="text"
                value={lotCode}
                onChange={(e) => setLotCode(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
                autoFocus
                required
                autoComplete="off"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="lot-qty" className="mb-1 block text-xs font-bold text-slate-700">
                  Cantidad <span className="text-rose-500">*</span>
                </label>
                <input
                  id="lot-qty"
                  type="text"
                  inputMode="decimal"
                  value={quantity}
                  onChange={(e) => { if (e.target.value === '' || quantityPattern.test(e.target.value)) setQuantity(e.target.value) }}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
                  required
                  autoComplete="off"
                />
              </div>
              <div>
                <label htmlFor="lot-unit" className="mb-1 block text-xs font-bold text-slate-700">
                  Unidad <span className="text-rose-500">*</span>
                </label>
                <select
                  id="lot-unit"
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
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="lot-mfg" className="mb-1 block text-xs font-bold text-slate-700">Fabricación</label>
                <input id="lot-mfg" type="date" value={manufacturingDate} onChange={(e) => setManufacturingDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label htmlFor="lot-exp" className="mb-1 block text-xs font-bold text-slate-700">Vencimiento</label>
                <input id="lot-exp" type="date" value={expirationDate} onChange={(e) => setExpirationDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </div>
            </div>

            <div>
              <label htmlFor="lot-comment" className="mb-1 block text-xs font-bold text-slate-700">Comentario</label>
              <input id="lot-comment" type="text" value={comment} onChange={(e) => setComment(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
              <button type="submit" disabled={!lotCode.trim() || !quantity || submitting} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
                {submitting ? 'Registrando…' : 'Registrar lote'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
