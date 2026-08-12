import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceDocumentsApi } from '../api/receptionDifferenceDocumentsApi'
import type { ReceptionDifferenceDocument } from '../types/reception-differences'

interface CancelReceptionDifferenceDocumentDialogProps {
  caseId: string
  document: ReceptionDifferenceDocument
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function CancelReceptionDifferenceDocumentDialog({
  caseId,
  document: doc,
  open,
  onOpenChange,
  onSuccess,
}: CancelReceptionDifferenceDocumentDialogProps) {
  const [reason, setReason] = useState('')

  const cancelMutation = useMutation(
    (id: string) =>
      receptionDifferenceDocumentsApi.cancel(id, {
        reason,
      }),
    {
      onSuccess: () => {
        onOpenChange(false)
        onSuccess?.()
      },
    }
  )

  const handleCancel = () => {
    if (!reason.trim()) return
    cancelMutation.mutate(caseId)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Cancelar documento DIF</h2>
        <p className="mb-4 text-xs text-slate-500">
          El documento del caso <strong>{doc.case_code}</strong> será marcado como cancelado.
        </p>

        <div className="mb-4 rounded-lg border border-slate-200 p-3 text-xs">
          <p><strong>Caso:</strong> {doc.case_code}</p>
          <p><strong>Estado:</strong> {doc.status}</p>
          <p><strong>Emitido:</strong> {doc.issued_at ?? '—'}</p>
        </div>

        <label className="mb-4 block text-xs text-slate-600">
          Motivo de cancelación *
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
            rows={3}
            placeholder="Indique el motivo de la cancelación..."
          />
        </label>

        {cancelMutation.error && (
          <p className="mb-3 text-xs text-rose-500">{String(cancelMutation.error)}</p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600"
          >
            Volver
          </button>
          <button
            type="button"
            onClick={handleCancel}
            disabled={!reason.trim() || cancelMutation.isPending}
            className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
          >
            {cancelMutation.isPending ? 'Cancelando...' : 'Cancelar documento'}
          </button>
        </div>
      </div>
    </div>
  )
}
