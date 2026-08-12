import { useState } from 'react'
import { vehiclesApi } from '../../api/vehicles-api'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  vehicleId: string
  currentPlate: string
  onChangePlate: (newPlate: string, reason: string) => void
  onClose: () => void
}

export function ChangeVehiclePlateDialog({
  isOpen,
  isSubmitting,
  vehicleId,
  currentPlate,
  onChangePlate,
  onClose,
}: Props) {
  const [newPlate, setNewPlate] = useState('')
  const [reason, setReason] = useState('')
  const [preview, setPreview] = useState<{ normalized_plate: string; warnings: string[]; conflicts: string[] } | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)

  if (!isOpen) return null

  const handlePreview = async () => {
    if (!newPlate.trim()) return
    setLoadingPreview(true)
    try {
      const res = await vehiclesApi.previewPlateChange(vehicleId, newPlate.trim())
      setPreview(res)
    } catch {
      setPreview(null)
    } finally {
      setLoadingPreview(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPlate.trim() || !reason.trim() || isSubmitting) return
    onChangePlate(newPlate.trim().toUpperCase(), reason.trim())
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
        aria-labelledby="change-plate-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="change-plate-title" className="text-base font-bold text-slate-800">
          Cambiar Placa de Rodaje
        </h3>

        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-900 space-y-1">
          <p>Placa actual: <strong className="font-mono font-bold text-base">{currentPlate}</strong></p>
          <p className="text-[11px] text-amber-800 flex items-start gap-1.5">
            <LogisticsIcon name="alert" size={14} aria-hidden /> <span><strong>Nota histórica:</strong> Los documentos y operaciones históricas conservarán la placa registrada en su snapshot inmutable.</span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Nueva Placa de Rodaje *</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newPlate}
                onChange={(e) => {
                  setNewPlate(e.target.value.toUpperCase())
                  setPreview(null)
                }}
                placeholder="Ej. XYZ-789"
                required
                className="flex-1 font-mono uppercase font-bold rounded-lg border border-slate-300 px-3 py-2 text-slate-800"
              />
              <Button type="button" variant="secondary" onClick={handlePreview} isLoading={loadingPreview}>
                Previsualizar
              </Button>
            </div>
          </div>

          {preview && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-1 font-mono text-[11px]">
              <p>Placa normalizada: <strong className="text-indigo-700">{preview.normalized_plate}</strong></p>
              {preview.warnings.length > 0 && (
                <div className="text-amber-700">
                  <span>Advertencias:</span>
                  <ul className="list-disc list-inside">
                    {preview.warnings.map((w, idx) => <li key={idx}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo del Cambio *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              required
              placeholder="Justificación del cambio de placa de rodaje..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!newPlate.trim() || !reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Cambiando..."
            >
              Confirmar Cambio de Placa
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
