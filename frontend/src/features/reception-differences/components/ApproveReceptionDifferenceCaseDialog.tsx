import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceCasesApi } from '../api/receptionDifferenceCasesApi'
import type { ReceptionDifferenceCaseDetail } from '../types/reception-differences'

interface ApproveReceptionDifferenceCaseDialogProps {
  caseData: ReceptionDifferenceCaseDetail
  _open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function ApproveReceptionDifferenceCaseDialog({
  caseData,
  onOpenChange,
  onSuccess,
}: ApproveReceptionDifferenceCaseDialogProps) {
  const [decision, setDecision] = useState<'APPROVE' | 'REQUEST_CHANGES'>('APPROVE')
  const [comment, setComment] = useState('')
  const [changesDescription, setChangesDescription] = useState('')

  const approveMutation = useMutation(
    (id: string) =>
      receptionDifferenceCasesApi.approve(id, {
        decision: 'APPROVE',
        comments: comment || undefined,
      }),
    { onSuccess: () => { onOpenChange(false); onSuccess?.() } }
  )

  const requestChangesMutation = useMutation(
    (id: string) =>
      receptionDifferenceCasesApi.requestChanges(id, {
        reason: changesDescription,
      }),
    { onSuccess: () => { onOpenChange(false); onSuccess?.() } }
  )

  const handleSubmit = () => {
    if (decision === 'APPROVE') {
      approveMutation.mutate(caseData.case_id)
    } else {
      if (!changesDescription.trim()) return
      requestChangesMutation.mutate(caseData.case_id)
    }
  }

  const loading = approveMutation.isPending || requestChangesMutation.isPending

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Revisión del caso</h2>
        <p className="mb-4 text-xs text-slate-500">
          Revise la información y decida: aprobar, solicitar cambios o rechazar.
        </p>

        <div className="mb-4 flex gap-2">
          <button
            type="button"
            onClick={() => setDecision('APPROVE')}
            className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
              decision === 'APPROVE'
                ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                : 'border-slate-200 text-slate-600'
            }`}
          >
            Aprobar
          </button>
          <button
            type="button"
            onClick={() => setDecision('REQUEST_CHANGES')}
            className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
              decision === 'REQUEST_CHANGES'
                ? 'border-amber-300 bg-amber-50 text-amber-700'
                : 'border-slate-200 text-slate-600'
            }`}
          >
            Solicitar cambios
          </button>
        </div>

        {decision === 'REQUEST_CHANGES' && (
          <label className="mb-3 block text-xs text-slate-600">
            Cambios solicitados *
            <textarea
              value={changesDescription}
              onChange={(e) => setChangesDescription(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
              rows={3}
              placeholder="Describa los cambios necesarios..."
            />
          </label>
        )}

        <label className="mb-4 block text-xs text-slate-600">
          Comentario (opcional)
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
            rows={2}
          />
        </label>

        {(approveMutation.error || requestChangesMutation.error) && (
          <p className="mb-3 text-xs text-rose-500">
            {String(approveMutation.error || requestChangesMutation.error)}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || (decision === 'REQUEST_CHANGES' && !changesDescription.trim())}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {loading ? 'Procesando...' : decision === 'APPROVE' ? 'Aprobar' : 'Solicitar cambios'}
          </button>
        </div>
      </div>
    </div>
  )
}
