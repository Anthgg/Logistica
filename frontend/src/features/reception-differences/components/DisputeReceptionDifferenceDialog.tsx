import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceResponsibilityApi } from '../api/receptionDifferenceResponsibilityApi'
import type { ReceptionDifferenceResponsibleParty } from '../types/reception-differences'

interface DisputeReceptionDifferenceDialogProps {
  caseId: string
  party: ReceptionDifferenceResponsibleParty
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function DisputeReceptionDifferenceDialog({
  caseId: _caseId,
  party,
  open,
  onOpenChange,
  onSuccess,
}: DisputeReceptionDifferenceDialogProps) {
  const [disputeType, setDisputeType] = useState<'FACTS' | 'RESPONSIBILITY'>('FACTS')
  const [reason, setReason] = useState('')

  const disputeMutation = useMutation(
    ({ respId }: { respId: string }) =>
      receptionDifferenceResponsibilityApi.dispute(respId, {
        dispute_type: disputeType,
        reason,
      }),
    {
      onSuccess: () => {
        onOpenChange(false)
        onSuccess?.()
      },
    }
  )

  const handleSubmit = () => {
    if (!reason.trim()) return
    disputeMutation.mutate({ respId: party.responsibility_id })
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Disputar responsabilidad</h2>
        <p className="mb-4 text-xs text-slate-500">
          Indique por qué no está de acuerdo con la asignación a <strong>{party.party_name}</strong>.
        </p>

        <div className="mb-4 rounded-lg border border-slate-200 p-3 text-xs">
          <p><strong>Responsable:</strong> {party.party_name}</p>
          <p><strong>Rol:</strong> {party.role}</p>
          <p><strong>Porcentaje:</strong> {party.percentage ?? '—'}%</p>
          <p><strong>Razón:</strong> {party.rationale ?? '—'}</p>
        </div>

        <label className="mb-3 block text-xs text-slate-600">
          Tipo de disputa
          <select
            value={disputeType}
            onChange={(e) => setDisputeType(e.target.value as 'FACTS' | 'RESPONSIBILITY')}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
          >
            <option value="FACTS">Hechos</option>
            <option value="RESPONSIBILITY">Responsabilidad</option>
          </select>
        </label>

        <label className="mb-3 block text-xs text-slate-600">
          Motivo de la disputa *
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
            rows={3}
            placeholder="Explique por qué disputa esta asignación..."
          />
        </label>

        {disputeMutation.error && (
          <p className="mb-3 text-xs text-rose-500">{String(disputeMutation.error)}</p>
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
            disabled={!reason.trim() || disputeMutation.isPending}
            className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
          >
            {disputeMutation.isPending ? 'Enviando...' : 'Disputar'}
          </button>
        </div>
      </div>
    </div>
  )
}
