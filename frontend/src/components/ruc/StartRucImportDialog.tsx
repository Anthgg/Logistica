import { useState } from 'react'
import { Button } from '../common/Button'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  onStart: (datasetType: string, reason: string) => void
  onClose: () => void
}

export function StartRucImportDialog({
  isOpen,
  isSubmitting,
  onStart,
  onClose,
}: Props) {
  const [datasetType, setDatasetType] = useState('PADRON_REDUCIDO')
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim() || isSubmitting) return
    onStart(datasetType, reason.trim())
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
        aria-labelledby="start-import-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="start-import-title" className="text-base font-bold text-slate-800">
          Ejecutar Importación Manual Autorizada
        </h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Tipo de Dataset *</label>
            <select
              value={datasetType}
              onChange={(e) => setDatasetType(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
            >
              <option value="PADRON_REDUCIDO">Padrón Reducido SUNAT (Oficial)</option>
              <option value="LOCALES_ANEXOS">Padrón de Locales Anexos</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo de importación *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              required
              placeholder="Justificación de la ejecución manual..."
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
              loadingLabel="Iniciando..."
            >
              Iniciar Importación
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
