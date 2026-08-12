import { Button } from '../common/Button'
import type { RucAssistedVerification } from '../../types/ruc-integration'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  verification: RucAssistedVerification
  onApprove: () => void
  onClose: () => void
}

export function ApproveAssistedVerificationDialog({
  isOpen,
  isSubmitting,
  verification,
  onApprove,
  onClose,
}: Props) {
  if (!isOpen) return null

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
        aria-labelledby="approve-assisted-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="approve-assisted-title" className="text-base font-bold text-slate-800">
          Aprobar Validación Asistida
        </h3>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2">
          <div>
            <span className="text-slate-400 font-bold uppercase text-[10px] block">RUC</span>
            <span className="font-mono font-bold text-slate-800">{verification.ruc}</span>
          </div>
          <div>
            <span className="text-slate-400 font-bold uppercase text-[10px] block">Razón Social</span>
            <span className="font-medium text-slate-800">{verification.observed_legal_name}</span>
          </div>
          <div>
            <span className="text-slate-400 font-bold uppercase text-[10px] block">Revisor</span>
            <span className="text-slate-700">{verification.created_by_user_name}</span>
          </div>
        </div>

        <p className="text-slate-600">
          ¿Confirmas la aprobación del dictamen asistido? Esta acción requiere privilegios supervisores y registrará la auditoría de cambio.
        </p>

        <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            onClick={onApprove}
            isLoading={isSubmitting}
            loadingLabel="Aprobando..."
          >
            Aprobar Dictamen
          </Button>
        </div>
      </div>
    </div>
  )
}
