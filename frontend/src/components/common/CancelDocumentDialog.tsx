import { useState } from 'react'
import { ResourceDialog } from './ResourceDialog'
import { Input } from './Input'
import { TextareaField } from './FormControls'
import type { DocumentItem } from '../../types/logistics-documents'

interface CancelDocumentDialogProps {
  isOpen: boolean
  document: DocumentItem | null
  isSubmitting?: boolean
  onClose: () => void
  onSubmit: (reason: string, confirmCode: string) => Promise<void>
}

export function CancelDocumentDialog({
  isOpen,
  document,
  isSubmitting,
  onClose,
  onSubmit,
}: CancelDocumentDialogProps) {
  const [reason, setReason] = useState('')
  const [confirmCodeInput, setConfirmCodeInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (!document) return null

  const handleConfirm = async () => {
    if (reason.trim().length < 10) {
      setError('Debes especificar un motivo detallado de al menos 10 caracteres.')
      return
    }
    if (confirmCodeInput.trim() !== document.code) {
      setError(`Debes escribir exactamente el código del documento (${document.code}) para confirmar.`)
      return
    }
    setError(null)
    await onSubmit(reason.trim(), confirmCodeInput.trim())
    setReason('')
    setConfirmCodeInput('')
  }

  return (
    <ResourceDialog
      isOpen={isOpen}
      title={`Anular documento — ${document.code}`}
      submitLabel="Confirmar anulación"
      isSubmitting={isSubmitting}
      onClose={onClose}
      onSubmit={() => void handleConfirm()}
    >
      <div className="space-y-4 text-xs">
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-rose-900">
          <p className="font-bold">¡Atención! Acción irreversible:</p>
          <p className="mt-1 leading-relaxed">
            La anulación marcará el documento como <strong>SIN VALIDEZ LEGAL NI LOGÍSTICA</strong>. El código asignado{' '}
            <code className="font-mono">{document.code}</code> no será liberado ni reutilizado. El documento permanecerá visible
            en el historial con estado <strong>ANULADO</strong>.
          </p>
        </div>

        <TextareaField
          label="Motivo justificado de anulación (Obligatorio)"
          value={reason}
          onChange={(e) => {
            setReason(e.target.value)
            if (error) setError(null)
          }}
          placeholder="Ej: Cancelación del despacho por solicitud formal del cliente o error en la guía original."
          rows={3}
          required
        />

        <Input
          label={`Para confirmar la anulación, escribe el código exactamente: ${document.code}`}
          value={confirmCodeInput}
          onChange={(e) => {
            setConfirmCodeInput(e.target.value)
            if (error) setError(null)
          }}
          placeholder={document.code}
          required
        />

        {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}
      </div>
    </ResourceDialog>
  )
}
