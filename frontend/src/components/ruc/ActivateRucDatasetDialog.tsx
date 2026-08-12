import { useState } from 'react'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { RucDataset } from '../../types/ruc-integration'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  dataset: RucDataset
  onActivate: (reason?: string) => void
  onClose: () => void
}

export function ActivateRucDatasetDialog({
  isOpen,
  isSubmitting,
  dataset,
  onActivate,
  onClose,
}: Props) {
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (dataset.has_anomalies && !reason.trim()) return
    onActivate(reason || undefined)
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
        aria-labelledby="activate-dataset-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="activate-dataset-title" className="text-base font-bold text-slate-800">
          Activar Dataset v{dataset.version}
        </h3>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-1">
          <p><strong className="text-slate-700">Filas procesadas:</strong> {dataset.statistics.total_rows.toLocaleString()}</p>
          <p><strong className="text-slate-700">Aceptadas:</strong> {dataset.statistics.accepted_rows.toLocaleString()}</p>
          <p><strong className="text-slate-700">Hash parcial:</strong> <code className="font-mono text-[10px]">{dataset.partial_hash}</code></p>
        </div>

        {dataset.has_anomalies && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 space-y-1 text-red-800">
            <span className="font-bold flex items-center gap-1.5"><LogisticsIcon name="alert" size={14} aria-hidden /> Alerta Crítica de Anomalías</span>
            <p className="text-[11px]">
              El dataset presenta discrepancias o anomalías en la estructura. Se requiere un motivo explícito para forzar la activación.
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          {dataset.has_anomalies && (
            <div>
              <label className="mb-1 block font-bold text-slate-700">Motivo obligatorio *</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                required
                placeholder="Justificación para activar con anomalías..."
                className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-xs"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={(dataset.has_anomalies && !reason.trim()) || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Activando..."
            >
              Confirmar Activación
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
