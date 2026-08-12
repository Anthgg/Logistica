import { useState } from 'react'
import { Button } from '../common/Button'

interface BlockProps {
  isOpen: boolean
  isSubmitting: boolean
  vehiclePlate: string
  onBlock: (reason: string) => void
  onClose: () => void
}

export function BlockVehicleDialog({
  isOpen,
  isSubmitting,
  vehiclePlate,
  onBlock,
  onClose,
}: BlockProps) {
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return
    onBlock(reason.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="block-vehicle-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="block-vehicle-title" className="text-base font-bold text-red-700">
          Bloquear Vehículo (Placa: {vehiclePlate})
        </h3>

        <p className="text-slate-600">
          El bloqueo impedirá la asignación a nuevas operaciones. Esta acción requiere justificación y Step-Up Authentication.
        </p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo del Bloqueo *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              required
              placeholder="Indica la razón del bloqueo operativo o normativo..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Bloqueando..."
            >
              Confirmar Bloqueo
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

interface UnblockProps {
  isOpen: boolean
  isSubmitting: boolean
  vehiclePlate: string
  onUnblock: (reason: string) => void
  onClose: () => void
}

export function UnblockVehicleDialog({
  isOpen,
  isSubmitting,
  vehiclePlate,
  onUnblock,
  onClose,
}: UnblockProps) {
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return
    onUnblock(reason.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="unblock-vehicle-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="unblock-vehicle-title" className="text-base font-bold text-slate-800">
          Desbloquear Vehículo (Placa: {vehiclePlate})
        </h3>

        <p className="text-slate-600">
          Al desbloquear, el backend reevaluará los documentos y la asignación del transportista para determinar el nuevo estado operativo.
        </p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo del Desbloqueo *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              required
              placeholder="Indica la resolución del motivo de bloqueo..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Desbloqueando..."
            >
              Confirmar Desbloqueo
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
