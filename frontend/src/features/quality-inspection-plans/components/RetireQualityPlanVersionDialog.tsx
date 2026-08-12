import { useState } from 'react'
import { useMutation } from '../../../features/inbound-docks/hooks/useQuery'
import { qualityPlanVersionsApi } from '../api/qualityPlanVersionsApi'
import type { QualityInspectionPlanVersion } from '../types/quality-inspection-plans'
import { Button } from '../../../components/common/Button'

interface RetireQualityPlanVersionDialogProps {
  version: QualityInspectionPlanVersion
  onRetire: () => void
}

export function RetireQualityPlanVersionDialog({
  version,
  onRetire,
}: RetireQualityPlanVersionDialogProps) {
  const [reason, setReason] = useState('')
  const [effectiveDate, setEffectiveDate] = useState('')
  const [successorVersionId, setSuccessorVersionId] = useState('')

  const retireMutation = useMutation(
    async () => {
      return qualityPlanVersionsApi.retire(version.version_id, {
        reason,
        effective_date: effectiveDate || undefined,
        successor_version_id: successorVersionId || undefined,
      })
    },
    { onSuccess: () => onRetire() },
  )

  const handleRetire = () => {
    if (!reason.trim()) return
    retireMutation.mutate(undefined as never)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onRetire} />
      <div className="relative z-10 w-full max-w-md rounded-xl bg-white p-6 shadow-xl text-xs">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Retirar versión</h2>
        <p className="mb-4 text-slate-500">
          Indique el motivo y fecha de retiro. Esta acción es irreversible.
        </p>

        <dl className="mb-3 grid grid-cols-2 gap-1 text-[11px]">
          <dt className="text-slate-500">Versión:</dt>
          <dd className="font-semibold text-slate-800">v{version.version_number}</dd>
          <dt className="text-slate-500">Vigencia:</dt>
          <dd>{version.valid_from ?? '—'} → {version.valid_until ?? '—'}</dd>
          <dt className="text-slate-500">Estado:</dt>
          <dd>{version.status}</dd>
          <dt className="text-slate-500">Conflictos:</dt>
          <dd>{version.conflict_count}</dd>
        </dl>

        <label className="mb-3 block text-[11px] text-slate-600">
          Motivo de retiro *
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-[11px]"
            rows={3}
            placeholder="Describa el motivo del retiro..."
          />
        </label>

        <label className="mb-3 block text-[11px] text-slate-600">
          Fecha efectiva (opcional)
          <input
            type="datetime-local"
            value={effectiveDate}
            onChange={(e) => setEffectiveDate(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
          />
        </label>

        <label className="mb-4 block text-[11px] text-slate-600">
          Versión sucesora (opcional)
          <input
            type="text"
            value={successorVersionId}
            onChange={(e) => setSuccessorVersionId(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
            placeholder="version_id de la versión que reemplazará esta"
          />
        </label>

        {retireMutation.error && (
          <p className="mb-3 text-rose-500">{retireMutation.error}</p>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="secondary" size="small" onClick={onRetire}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            size="small"
            isLoading={retireMutation.isPending}
            disabled={!reason.trim()}
            onClick={handleRetire}
          >
            Retirar
          </Button>
        </div>
      </div>
    </div>
  )
}
