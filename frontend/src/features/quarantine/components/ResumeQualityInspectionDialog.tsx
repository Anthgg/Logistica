import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type { QualityInspection } from '../types/quarantine'
import { Button } from '../../../components/common/Button'

function formatDuration(pausedAt: string | null): string {
  if (!pausedAt) return '—'
  const diff = Date.now() - new Date(pausedAt).getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (hours > 0) {
    return `${hours}h ${remainingMinutes}min`
  }
  return `${minutes} min`
}

export function ResumeQualityInspectionDialog({
  isOpen,
  inspectionId,
  onClose,
  onResume,
}: {
  isOpen: boolean
  inspectionId: string
  onClose: () => void
  onResume?: () => void
}) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canResume = hasPermission(LOGISTICS_PERMISSIONS.quarantine.resumeInspection)

  const [confirmed, setConfirmed] = useState(false)

  const {
    data: inspection,
    isLoading,
  } = useQuery<QualityInspection>(
    ['inspection', inspectionId],
    `/logistics/quality-inspections/inspections/${inspectionId}`,
    undefined,
    { enabled: isOpen },
  )

  const {
    mutate: resumeInspection,
    isPending,
    error,
  } = useMutation(
    () => qualityInspectionsApi.resume(inspectionId),
    {
      onSuccess: () => {
        onResume?.()
        onClose()
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return undefined
    setConfirmed(false)
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
        aria-labelledby="resume-inspection-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Inspección de calidad</p>
            <h2 id="resume-inspection-title">Reanudar inspección</h2>
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
          {isLoading ? (
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
                    Motivo de pausa
                  </dt>
                  <dd className="text-sm text-slate-800">
                    {inspection?.cancellation_reason ?? 'No especificado'}
                  </dd>
                </div>
                <div className="flex flex-col">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Tiempo en pausa
                  </dt>
                  <dd className="text-sm text-slate-800">
                    {formatDuration(inspection?.paused_at ?? null)}
                  </dd>
                </div>
              </dl>

              <label
                className={`flex cursor-pointer items-start gap-2 rounded-lg border px-3 py-2 text-xs transition-colors ${
                  confirmed
                    ? 'border-primary bg-primary-xlight text-primary'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded border-slate-300 text-primary focus:ring-primary"
                />
                <span>
                  Confirmo que la inspección debe reanudarse con los controles y mediciones en su
                  estado actual.
                </span>
              </label>
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
            loadingLabel="Reanudando..."
            disabled={!canResume || !confirmed || isPending}
            onClick={() => resumeInspection(undefined as never)}
          >
            Reanudar inspección
          </Button>
        </div>
      </div>
    </div>
  )
}
