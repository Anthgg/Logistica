import { useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { Modal } from '../../supplier-evaluation/components/ui/Overlay'
import type {
  ApprovalAssignmentSummary,
  ApprovalDecisionType,
} from '../types/phase035-contract'

export function ApprovalDecisionDialog({
  assignment,
  isSubmitting,
  errorMessage,
  onClose,
  onConfirm,
}: {
  assignment: ApprovalAssignmentSummary | null
  isSubmitting: boolean
  errorMessage: string | null
  onClose: () => void
  onConfirm: (decision: ApprovalDecisionType, reason: string) => void
}) {
  const [decision, setDecision] = useState<ApprovalDecisionType | null>(null)
  const [reason, setReason] = useState('')

  useEffect(() => {
    setDecision(null)
    setReason('')
  }, [assignment?.id])

  const reasonRequired = decision === 'REJECT' || decision === 'RETURN'
  const valid =
    decision !== null &&
    (!reasonRequired || reason.trim().length >= 20)

  return (
    <Modal
      open={assignment !== null}
      onOpenChange={(open) => {
        if (!open && !isSubmitting) onClose()
      }}
      title="Registrar decisión"
      description={
        assignment
          ? `${assignment.request_code ?? 'Solicitud'} · ${assignment.step_name ?? 'Paso pendiente'}`
          : undefined
      }
      footer={
        <>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            className="min-h-10 rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-700 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={!valid || isSubmitting}
            onClick={() => {
              if (decision) onConfirm(decision, reason.trim())
            }}
            className="min-h-10 rounded-lg bg-[#1F4E6D] px-3 text-xs font-semibold text-white disabled:opacity-50"
          >
            {isSubmitting ? 'Registrando…' : 'Confirmar decisión'}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Decisión
          </span>
          <Select
            value={decision ?? ''}
            onValueChange={(value) =>
              setDecision(value as ApprovalDecisionType)
            }
          >
            <SelectTrigger className="min-h-11 w-full">
              <SelectValue placeholder="Selecciona una decisión" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="APPROVE">Aprobar</SelectItem>
              <SelectItem value="REJECT">Rechazar</SelectItem>
              <SelectItem value="RETURN">Devolver para cambios</SelectItem>
            </SelectContent>
          </Select>
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Motivo {reasonRequired ? '(mínimo 20 caracteres)' : '(opcional)'}
          </span>
          <textarea
            rows={4}
            value={reason}
            disabled={isSubmitting}
            onChange={(event) => setReason(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>

        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
          La acción requiere reverificación continua. El frontend no marca el
          paso como completado localmente; volverá a consultar la bandeja.
        </p>

        {errorMessage && (
          <p role="alert" className="text-sm font-medium text-rose-700">
            {errorMessage}
          </p>
        )}
      </div>
    </Modal>
  )
}
