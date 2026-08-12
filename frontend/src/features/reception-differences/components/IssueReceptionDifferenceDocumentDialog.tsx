import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceDocumentsApi } from '../api/receptionDifferenceDocumentsApi'
import type { ReceptionDifferenceCaseDetail } from '../types/reception-differences'

interface IssueReceptionDifferenceDocumentDialogProps {
  caseData: ReceptionDifferenceCaseDetail
  _open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function IssueReceptionDifferenceDocumentDialog({
  caseData,
  onOpenChange,
  onSuccess,
}: IssueReceptionDifferenceDocumentDialogProps) {
  const [comment, setComment] = useState('')

  const issueMutation = useMutation(
    (id: string) => receptionDifferenceDocumentsApi.issue(id, { confirmation: true }),
    { onSuccess: () => { onOpenChange(false); onSuccess?.() } }
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Generar documento DIF</h2>
        <p className="mb-4 text-xs text-slate-500">
          El sistema generará un documento único del caso que podrá compartirse con el proveedor.
        </p>

        <div className="mb-4 rounded-lg border border-slate-200 p-3 text-xs text-slate-600">
          <p><strong>Caso:</strong> {caseData.case_code}</p>
          <p><strong>Estado:</strong> {caseData.current_status_display}</p>
          <p><strong>Diferencias:</strong> {caseData.items.length} tipos</p>
        </div>

        <label className="mb-4 block text-xs text-slate-600">
          Nota adicional (opcional)
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
            rows={3}
          />
        </label>

        {issueMutation.error && (
          <p className="mb-3 text-xs text-rose-500">{String(issueMutation.error)}</p>
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
            onClick={() => issueMutation.mutate(caseData.case_id)}
            disabled={issueMutation.isPending}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {issueMutation.isPending ? 'Generando...' : 'Generar documento'}
          </button>
        </div>
      </div>
    </div>
  )
}
