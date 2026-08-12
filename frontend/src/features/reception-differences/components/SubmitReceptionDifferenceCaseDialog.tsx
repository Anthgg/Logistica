import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceCasesApi } from '../api/receptionDifferenceCasesApi'
import type { ReceptionDifferenceCaseDetail } from '../types/reception-differences'

interface SubmitReceptionDifferenceCaseDialogProps {
  caseData: ReceptionDifferenceCaseDetail
  _open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function SubmitReceptionDifferenceCaseDialog({
  caseData,
  onOpenChange,
  onSuccess,
}: SubmitReceptionDifferenceCaseDialogProps) {
  const [comment, setComment] = useState('')
  const submitMutation = useMutation(
    (id: string) => receptionDifferenceCasesApi.submit(id),
    {
      onSuccess: () => {
        onOpenChange(false)
        onSuccess?.()
      },
    }
  )

  const handleSubmit = () => {
    submitMutation.mutate(caseData.case_id)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Enviar caso para revisión</h2>
        <p className="mb-4 text-xs text-slate-500">
          El caso cambiará a <strong>EN_REVISION</strong>. No podrá editarse mientras se revisa.
        </p>

        <label className="mb-4 block text-xs text-slate-600">
          Comentario para el revisor
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
            rows={3}
            placeholder="Describa brevemente el contexto..."
          />
        </label>

        {submitMutation.error && (
          <p className="mb-3 text-xs text-rose-500">{String(submitMutation.error)}</p>
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
            disabled={submitMutation.isPending}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {submitMutation.isPending ? 'Enviando...' : 'Enviar para revisión'}
          </button>
        </div>
      </div>
    </div>
  )
}
