import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import type { ProductSummary, CreateExpirationObservationRequest } from '../../types/inbound-receiving'

interface ExpirationObservationDialogProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: CreateExpirationObservationRequest) => void
  product: ProductSummary
  lineId: string
  lotCode?: string
  submitting?: boolean
}

export function ExpirationObservationDialog({
  open,
  onClose,
  onSubmit,
  product,
  lineId,
  lotCode,
  submitting = false,
}: ExpirationObservationDialogProps) {
  const [manufacturingDate, setManufacturingDate] = useState('')
  const [expirationDate, setExpirationDate] = useState('')
  const [comment, setComment] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!expirationDate) return
    onSubmit({
      line_id: lineId,
      lot_code: lotCode,
      manufacturing_date: manufacturingDate || undefined,
      expiration_date: expirationDate,
      source: 'MANUAL',
      comment: comment || undefined,
    })
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-5 shadow-2xl">
          <Dialog.Title className="text-sm font-bold text-slate-800">Observación de vencimiento</Dialog.Title>
          <Dialog.Description className="mt-1 text-xs text-slate-500">
            {product.name} {lotCode ? `· Lote: ${lotCode}` : ''}
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="mt-4 space-y-3">
            <div>
              <label htmlFor="exp-mfg" className="mb-1 block text-xs font-bold text-slate-700">Fecha de fabricación</label>
              <input id="exp-mfg" type="date" value={manufacturingDate} onChange={(e) => setManufacturingDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>

            <div>
              <label htmlFor="exp-date" className="mb-1 block text-xs font-bold text-slate-700">
                Fecha de vencimiento <span className="text-rose-500">*</span>
              </label>
              <input id="exp-date" type="date" value={expirationDate} onChange={(e) => setExpirationDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" required autoFocus />
            </div>

            <div>
              <label htmlFor="exp-comment" className="mb-1 block text-xs font-bold text-slate-700">Comentario</label>
              <input id="exp-comment" type="text" value={comment} onChange={(e) => setComment(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>

            <p className="text-[10px] text-slate-400">
              La aceptación final del vencimiento la determina el backend.
            </p>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
              <button type="submit" disabled={!expirationDate || submitting} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
                {submitting ? 'Registrando…' : 'Registrar'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
