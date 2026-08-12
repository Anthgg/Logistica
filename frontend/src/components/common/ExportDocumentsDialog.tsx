import { useState } from 'react'
import { ResourceDialog } from './ResourceDialog'

interface ExportDocumentsDialogProps {
  isOpen: boolean
  selectedCount: number
  isSubmitting?: boolean
  onClose: () => void
  onSubmit: (options: {
    exportFormat: 'ZIP' | 'COMBINED_PDF'
    includeManifest: boolean
    includeChecksums: boolean
    reason?: string
  }) => Promise<void>
}

export function ExportDocumentsDialog({
  isOpen,
  selectedCount,
  isSubmitting,
  onClose,
  onSubmit,
}: ExportDocumentsDialogProps) {
  const [exportFormat, setExportFormat] = useState<'ZIP' | 'COMBINED_PDF'>('ZIP')
  const [includeManifest, setIncludeManifest] = useState(true)
  const [includeChecksums, setIncludeChecksums] = useState(true)
  const [reason] = useState('')

  if (!isOpen) return null

  const handleConfirm = async () => {
    await onSubmit({
      exportFormat,
      includeManifest,
      includeChecksums,
      reason: reason.trim() || undefined,
    })
  }

  return (
    <ResourceDialog
      isOpen={isOpen}
      title={`Solicitar paquete de exportación (${selectedCount} documentos)`}
      submitLabel="Generar exportación"
      isSubmitting={isSubmitting}
      onClose={onClose}
      onSubmit={() => void handleConfirm()}
    >
      <div className="space-y-4 text-xs">
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-blue-900">
          <p className="font-bold">Procesamiento asíncrono en segundo plano:</p>
          <p className="mt-1 leading-relaxed">
            Se creará una tarea de empaquetado para los {selectedCount} documentos seleccionados. Podrás consultar el progreso y
            descargar el archivo final desde el panel de exportaciones.
          </p>
        </div>

        <div className="field">
          <label className="field__label">Formato de entrega</label>
          <div className="grid grid-cols-2 gap-2 mt-1">
            <button
              type="button"
              className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-colors ${
                exportFormat === 'ZIP'
                  ? 'border-blue-700 bg-blue-50 text-blue-900 font-bold'
                  : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
              }`}
              onClick={() => setExportFormat('ZIP')}
            >
              <span>Archivo ZIP comprimido</span>
              <small className="text-[10px] text-slate-500 font-normal mt-1">
                Incluye archivos PDF individuales por documento.
              </small>
            </button>
            <button
              type="button"
              className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-colors ${
                exportFormat === 'COMBINED_PDF'
                  ? 'border-blue-700 bg-blue-50 text-blue-900 font-bold'
                  : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
              }`}
              onClick={() => setExportFormat('COMBINED_PDF')}
            >
              <span>PDF Unificado</span>
              <small className="text-[10px] text-slate-500 font-normal mt-1">
                Combina todas las páginas en un único tomo PDF.
              </small>
            </button>
          </div>
        </div>

        <div className="space-y-2 pt-2 border-t border-slate-100">
          <label className="checkbox">
            <input
              type="checkbox"
              checked={includeManifest}
              onChange={(e) => setIncludeManifest(e.target.checked)}
            />
            <span>Incluir archivo de manifiesto (`manifest.json`)</span>
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={includeChecksums}
              onChange={(e) => setIncludeChecksums(e.target.checked)}
            />
            <span>Incluir resumen de integridad SHA-256 (`checksums.sha256`)</span>
          </label>
        </div>
      </div>
    </ResourceDialog>
  )
}
