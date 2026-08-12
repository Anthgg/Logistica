import { useState } from 'react'
import { Button } from '../common/Button'
import type { RucDataset } from '../../types/ruc-integration'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  activeDataset: RucDataset
  targetDataset: RucDataset
  onRollback: (reason: string) => void
  onClose: () => void
}

export function RollbackRucDatasetDialog({
  isOpen,
  isSubmitting,
  activeDataset,
  targetDataset,
  onRollback,
  onClose,
}: Props) {
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return
    onRollback(reason.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4 text-xs"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rollback-dataset-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="rollback-dataset-title" className="text-base font-bold text-slate-800">
          Ejecutar Rollback de Padrón
        </h3>

        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 space-y-1 text-amber-900">
          <p><strong>Dataset actual (Revertir):</strong> v{activeDataset.version}</p>
          <p><strong>Dataset destino (Restaurar):</strong> v{targetDataset.version}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo del Rollback *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              required
              placeholder="Indica la razón del rollback administrativo..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-xs"
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
              loadingLabel="Revirtiendo..."
            >
              Confirmar Rollback
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
