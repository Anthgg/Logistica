import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type { QualityInspectionControl } from '../types/quarantine'
import { Button } from '../../../components/common/Button'

export function RequestQualityControlResultCorrectionDialog({
  isOpen,
  controlId,
  onClose,
  onCorrectionRequested,
}: {
  isOpen: boolean
  controlId: string
  onClose: () => void
  onCorrectionRequested?: () => void
}) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canCorrect = hasPermission(LOGISTICS_PERMISSIONS.quarantine.correctControl)

  const [proposedValue, setProposedValue] = useState('')
  const [reason, setReason] = useState('')
  const [evidence, setEvidence] = useState('')

  const {
    data: control,
    isLoading: isLoadingControl,
  } = useQuery<QualityInspectionControl>(
    ['control', controlId],
    `/logistics/quality-inspections/controls/${controlId}`,
    undefined,
    { enabled: isOpen },
  )

  const {
    mutate: requestCorrection,
    isPending,
    error,
  } = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionsApi.requestControlResultCorrection(controlId, input),
    {
      onSuccess: () => {
        onCorrectionRequested?.()
        onClose()
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return undefined
    setProposedValue('')
    setReason('')
    setEvidence('')
    const previousFocus = document.activeElement as HTMLElement | null
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isPending) onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previousFocus?.focus()
    }
  }, [isOpen, isPending, onClose])

  if (!isOpen) return null

  const originalValue = control?.result_value ?? control?.result_text ?? '—'
  const requiresStepUp = control?.result_status === 'SUPERSEDED'

  const canSubmit =
    canCorrect &&
    proposedValue.trim() &&
    reason.trim() &&
    !isPending

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={() => {
        if (!isPending) onClose()
      }}
    >
      <div
        ref={dialogRef}
        className="resource-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="correction-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Corrección de resultado</p>
            <h2 id="correction-dialog-title">Solicitar corrección de resultado</h2>
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Cerrar"
            disabled={isPending}
          >
            ×
          </button>
        </div>

        <div className="resource-dialog__body space-y-4">
          {isLoadingControl ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
              ))}
            </div>
          ) : (
            <>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-xs sm:grid-cols-2">
                <div className="flex flex-col">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Control
                  </dt>
                  <dd className="text-sm font-medium text-slate-800">
                    {control?.code ?? '—'} — {control?.name ?? '—'}
                  </dd>
                </div>
                <div className="flex flex-col">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Tipo de resultado
                  </dt>
                  <dd className="text-sm text-slate-800">
                    {control?.result_value_type ?? '—'}
                  </dd>
                </div>
              </dl>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Resultado original
                  </p>
                  <p className="text-sm font-medium text-slate-800">{originalValue}</p>
                </div>
                <div className="rounded-lg border border-amber-100 bg-amber-50/60 p-3">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-amber-600">
                    Resultado propuesto
                  </p>
                  <p className="text-sm font-medium text-amber-800">
                    {proposedValue || '—'}
                  </p>
                </div>
              </div>

              {requiresStepUp && (
                <div className="rounded-lg border border-purple-100 bg-purple-50 px-3 py-2 text-[11px] text-purple-700">
                  Este control tiene un resultado superseded. La corrección creará una nueva
                  revisión sin sobrescribir el resultado anterior.
                </div>
              )}

              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Nuevo valor propuesto
                </label>
                <input
                  value={proposedValue}
                  onChange={(e) => setProposedValue(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Ingrese el nuevo valor..."
                />
              </div>

              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Motivo de la corrección
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Explique por qué es necesaria esta corrección..."
                />
              </div>

              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Evidencia de soporte (opcional)
                </label>
                <textarea
                  value={evidence}
                  onChange={(e) => setEvidence(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Referencia a evidencia documental que soporte la corrección."
                />
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Impacto de la corrección
                </h3>
                <p className="text-xs text-slate-700">
                  La corrección no actualiza el resultado de forma definitiva hasta que el backend
                  confirme. Se creará una nueva revisión del resultado.
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Historial de correcciones
                </h3>
                <p className="text-xs text-slate-500 italic">
                  No hay correcciones previas registradas para este control.
                </p>
              </div>
            </>
          )}

          {error && (
            <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
              {error}
            </div>
          )}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            isLoading={isPending}
            loadingLabel="Enviando..."
            disabled={!canSubmit}
            onClick={() =>
              requestCorrection({
                result_value: proposedValue,
                correction_reason: reason,
                notes: evidence || undefined,
              })
            }
          >
            Solicitar corrección
          </Button>
        </div>
      </div>
    </div>
  )
}
