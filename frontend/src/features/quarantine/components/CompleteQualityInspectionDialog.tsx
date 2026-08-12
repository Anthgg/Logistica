import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type {
  QualityInspection,
  QualityInspectionControl,
  QualityInspectionOverallResult,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'

const RESULT_OPTIONS: Array<{ value: QualityInspectionOverallResult; label: string }> = [
  { value: 'PASS', label: 'Aprobado' },
  { value: 'PASS_WITH_OBSERVATIONS', label: 'Aprobado con observaciones' },
  { value: 'FAIL', label: 'Rechazado' },
  { value: 'INCONCLUSIVE', label: 'Inconcluso' },
  { value: 'REINSPECTION_REQUIRED', label: 'Reinspección requerida' },
]



export function CompleteQualityInspectionDialog({
  isOpen,
  inspectionId,
  onClose,
  onComplete,
}: {
  isOpen: boolean
  inspectionId: string
  onClose: () => void
  onComplete?: () => void
}) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canComplete = hasPermission(LOGISTICS_PERMISSIONS.quarantine.completeInspection)

  const [selectedResult, setSelectedResult] = useState<QualityInspectionOverallResult>('PASS')
  const [notes, setNotes] = useState('')

  const {
    data: inspection,
    isLoading: isLoadingInspection,
  } = useQuery<QualityInspection>(
    ['inspection', inspectionId],
    `/logistics/quality-inspections/inspections/${inspectionId}`,
    undefined,
    { enabled: isOpen },
  )

  const {
    data: controls,
    isLoading: isLoadingControls,
  } = useQuery<QualityInspectionControl[]>(
    ['inspection-controls', inspectionId],
    `/logistics/quality-inspections/inspections/${inspectionId}/controls`,
    undefined,
    { enabled: isOpen },
  )

  const {
    mutate: completeInspection,
    isPending,
    error,
  } = useMutation(
    (input: { overall_result: QualityInspectionOverallResult; notes?: string }) =>
      qualityInspectionsApi.complete(inspectionId, input),
    {
      onSuccess: () => {
        onComplete?.()
        onClose()
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return undefined
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

  const isLoading = isLoadingInspection || isLoadingControls
  const controlsPassed = controls?.filter((c) => c.status === 'COMPLETED' && c.result_status !== 'PENDING').length ?? 0
  const controlsFailed = controls?.filter((c) => c.status === 'FAILED' || c.result_status === 'SUPERSEDED').length ?? 0
  const totalMeasurements = controls?.reduce((acc, c) => acc + c.measurements.length, 0) ?? 0
  const totalSamples = controls?.reduce((acc, c) => acc + c.sample_references.length, 0) ?? 0
  const totalCertificates = inspection?.certificate_review_count ?? 0
  const totalEvidence = inspection?.evidence_count ?? 0

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
        aria-labelledby="complete-inspection-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Inspección de calidad</p>
            <h2 id="complete-inspection-title">Completar inspección</h2>
            <p className="text-xs text-slate-500">
              Completar la inspección no libera la mercadería. La aprobación y liberación son
              acciones separadas.
            </p>
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
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
              ))}
            </div>
          ) : (
            <>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-3">
                <div className="flex flex-col">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Producto
                  </dt>
                  <dd className="text-sm text-slate-800">
                    {inspection?.product?.name ?? '—'}
                  </dd>
                </div>
                <div className="flex flex-col">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Cantidad total
                  </dt>
                  <dd className="text-sm text-slate-800">
                    {inspection?.total_quantity ?? '—'} {inspection?.unit?.symbol ?? ''}
                  </dd>
                </div>
                <div className="flex flex-col">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Plan de inspección
                  </dt>
                  <dd className="text-sm text-slate-800">
                    {inspection?.plan_code ?? '—'} v{inspection?.plan_version_id?.slice(0, 6) ?? '—'}
                  </dd>
                </div>
              </dl>

              <div className="grid grid-cols-4 gap-2">
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-2 text-center">
                  <p className="text-lg font-bold text-slate-800">{controlsPassed}</p>
                  <p className="text-[10px] text-slate-500">Controles completados</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-2 text-center">
                  <p className="text-lg font-bold text-rose-700">{controlsFailed}</p>
                  <p className="text-[10px] text-slate-500">Controles fallidos</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-2 text-center">
                  <p className="text-lg font-bold text-slate-800">{totalMeasurements}</p>
                  <p className="text-[10px] text-slate-500">Mediciones</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-2 text-center">
                  <p className="text-lg font-bold text-slate-800">{totalSamples}</p>
                  <p className="text-[10px] text-slate-500">Muestras</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2">
                  <span className="font-medium text-slate-600">Certificados:</span>
                  <span className="text-slate-800">{totalCertificates}</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2">
                  <span className="font-medium text-slate-600">Evidencia:</span>
                  <span className="text-slate-800">{totalEvidence}</span>
                </div>
              </div>

              <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-[11px] text-blue-700">
                Completar la inspección no libera la mercadería. La aprobación y liberación son
                acciones separadas.
              </div>

              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Resultado calculado por el backend
                </label>
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2 text-sm font-medium text-slate-800">
                  {inspection?.overall_result === 'NOT_COMPUTED'
                    ? 'Sin calcular'
                    : inspection?.overall_result ?? '—'}
                </div>
              </div>

              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Resultado de la inspección
                </label>
                <div className="space-y-1.5">
                  {RESULT_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-colors ${
                        selectedResult === opt.value
                          ? 'border-primary bg-primary-xlight text-primary'
                          : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="inspection-result"
                        value={opt.value}
                        checked={selectedResult === opt.value}
                        onChange={() => setSelectedResult(opt.value)}
                        className="sr-only"
                      />
                      <span
                        className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border-2 ${
                          selectedResult === opt.value
                            ? 'border-primary'
                            : 'border-slate-300'
                        }`}
                      >
                        {selectedResult === opt.value && (
                          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                        )}
                      </span>
                      {opt.label}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Notas (opcional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Observaciones adicionales sobre la inspección..."
                />
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
            loadingLabel="Completando..."
            disabled={!canComplete || isPending}
            onClick={() =>
              completeInspection({ overall_result: selectedResult, notes: notes || undefined })
            }
          >
            Completar inspección
          </Button>
        </div>
      </div>
    </div>
  )
}
