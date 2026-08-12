import { useState, useEffect, useRef } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import { Button } from '../../../components/common/Button'

const PAUSE_REASONS = [
  { value: 'PENDING_EVIDENCE', label: 'Evidencia pendiente' },
  { value: 'PENDING_CERTIFICATE', label: 'Certificado pendiente' },
  { value: 'EQUIPMENT_UNAVAILABLE', label: 'Equipo no disponible' },
  { value: 'SUPERVISOR_REQUIRED', label: 'Supervisor requerido' },
  { value: 'UNIDENTIFIED_PRODUCT', label: 'Producto no identificado' },
  { value: 'PENDING_SAMPLE', label: 'Muestra pendiente' },
  { value: 'INCIDENT', label: 'Incidente' },
  { value: 'OTHER', label: 'Otro' },
] as const

export function PauseQualityInspectionDialog({
  isOpen,
  inspectionId,
  onClose,
  onPause,
}: {
  isOpen: boolean
  inspectionId: string
  onClose: () => void
  onPause?: () => void
}) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canPause = hasPermission(LOGISTICS_PERMISSIONS.quarantine.pauseInspection)

  const [selectedReason, setSelectedReason] = useState<string>('')
  const [otherReason, setOtherReason] = useState('')

  const {
    mutate: pauseInspection,
    isPending,
    error,
  } = useMutation(
    (input: { reason: string }) =>
      qualityInspectionsApi.pause(inspectionId, input),
    {
      onSuccess: () => {
        onPause?.()
        onClose()
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return undefined
    setSelectedReason('')
    setOtherReason('')
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

  const finalReason =
    selectedReason === 'OTHER'
      ? otherReason.trim()
      : PAUSE_REASONS.find((r) => r.value === selectedReason)?.label ?? ''

  const canSubmit = canPause && selectedReason && (selectedReason !== 'OTHER' || otherReason.trim())

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
        aria-labelledby="pause-inspection-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Inspección de calidad</p>
            <h2 id="pause-inspection-title">Pausar inspección</h2>
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
          <div>
            <label className="mb-2 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Motivo de pausa
            </label>
            <div className="space-y-1.5">
              {PAUSE_REASONS.map((reason) => (
                <label
                  key={reason.value}
                  className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-colors ${
                    selectedReason === reason.value
                      ? 'border-primary bg-primary-xlight text-primary'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="pause-reason"
                    value={reason.value}
                    checked={selectedReason === reason.value}
                    onChange={() => setSelectedReason(reason.value)}
                    className="sr-only"
                  />
                  <span
                    className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border-2 ${
                      selectedReason === reason.value
                        ? 'border-primary'
                        : 'border-slate-300'
                    }`}
                  >
                    {selectedReason === reason.value && (
                      <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                    )}
                  </span>
                  {reason.label}
                </label>
              ))}
            </div>
          </div>

          {selectedReason === 'OTHER' && (
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Especifique el motivo
              </label>
              <textarea
                value={otherReason}
                onChange={(e) => setOtherReason(e.target.value)}
                rows={3}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Describa el motivo de la pausa..."
              />
            </div>
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
            variant="danger"
            isLoading={isPending}
            loadingLabel="Pausando..."
            disabled={!canSubmit || isPending}
            onClick={() => pauseInspection({ reason: finalReason })}
          >
            Pausar inspección
          </Button>
        </div>
      </div>
    </div>
  )
}
