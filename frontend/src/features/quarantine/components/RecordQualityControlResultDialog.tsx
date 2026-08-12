import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type { QualityInspectionControl } from '../types/quarantine'
import { Button } from '../../../components/common/Button'

type ResultType = 'PASS' | 'FAIL' | 'OBSERVATION' | 'NOT_APPLICABLE'

const RESULT_OPTIONS: Array<{ value: ResultType; label: string; description: string }> = [
  { value: 'PASS', label: 'PASS', description: 'El control cumple con los criterios de aceptación.' },
  { value: 'FAIL', label: 'FAIL', description: 'El control no cumple con los criterios de aceptación.' },
  { value: 'OBSERVATION', label: 'OBSERVACIÓN', description: 'El control presenta observaciones menores.' },
  { value: 'NOT_APPLICABLE', label: 'NO APLICABLE', description: 'El control no aplica para esta inspección.' },
]

export function RecordQualityControlResultDialog({
  isOpen,
  controlId,
  onClose,
  onResultRecorded,
}: {
  isOpen: boolean
  controlId: string
  onClose: () => void
  onResultRecorded?: () => void
}) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canRecord = hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordControlResult)

  const [selectedResult, setSelectedResult] = useState<ResultType>('PASS')
  const [resultValue, setResultValue] = useState('')
  const [resultText, setResultText] = useState('')
  const [observation, setObservation] = useState('')

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
    mutate: recordResult,
    isPending,
    error,
  } = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionsApi.recordControlResult(controlId, input),
    {
      onSuccess: () => {
        onResultRecorded?.()
        onClose()
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return undefined
    setSelectedResult('PASS')
    setResultValue('')
    setResultText('')
    setObservation('')
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

  const hasBackendSuggestedResult = control?.result_value != null && control.result_status === 'PENDING'
  const backendSuggestedValue = control?.result_value ?? null
  const hasMeasurements = control?.measurements && control.measurements.length > 0
  const requiresMeasurement = control?.result_value_type === 'MEASUREMENT'

  const isPassDisabled = requiresMeasurement && !hasMeasurements

  const canSubmit =
    canRecord &&
    !isPending &&
    (selectedResult !== 'PASS' || !isPassDisabled)

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
        aria-labelledby="record-result-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Resultado de control</p>
            <h2 id="record-result-dialog-title">Registrar resultado de control</h2>
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
                {control?.unit && (
                  <div className="flex flex-col">
                    <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Unidad
                    </dt>
                    <dd className="text-sm text-slate-800">
                      {control.unit.symbol} ({control.unit.name})
                    </dd>
                  </div>
                )}
                {control?.expected_value && (
                  <div className="flex flex-col">
                    <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Valor esperado
                    </dt>
                    <dd className="text-sm text-slate-800">{control.expected_value}</dd>
                  </div>
                )}
                {control?.min_value && control?.max_value && (
                  <div className="flex flex-col">
                    <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Tolerancia
                    </dt>
                    <dd className="text-sm text-slate-800">
                      {control.min_value} — {control.max_value} {control.unit?.symbol ?? ''}
                    </dd>
                  </div>
                )}
              </dl>

              {hasBackendSuggestedResult && (
                <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-[11px] text-blue-700">
                  <span className="font-medium">Resultado sugerido por el backend:</span>{' '}
                  {backendSuggestedValue}
                </div>
              )}

              <div>
                <label className="mb-2 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Resultado del control
                </label>
                <div className="space-y-1.5">
                  {RESULT_OPTIONS.map((opt) => {
                    const isDisabled = opt.value === 'PASS' && isPassDisabled
                    return (
                      <label
                        key={opt.value}
                        className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-xs transition-colors ${
                          isDisabled
                            ? 'cursor-not-allowed border-slate-100 bg-slate-50 text-slate-400'
                            : selectedResult === opt.value
                              ? 'border-primary bg-primary-xlight text-primary'
                              : 'cursor-pointer border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="control-result"
                          value={opt.value}
                          checked={selectedResult === opt.value}
                          onChange={() => setSelectedResult(opt.value)}
                          disabled={isDisabled}
                          className="sr-only"
                        />
                        <span
                          className={`mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border-2 ${
                            selectedResult === opt.value
                              ? 'border-primary'
                              : isDisabled
                                ? 'border-slate-200'
                                : 'border-slate-300'
                          }`}
                        >
                          {selectedResult === opt.value && (
                            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          )}
                        </span>
                        <div>
                          <span className="font-medium">{opt.label}</span>
                          <p className="text-[10px] text-slate-500">{opt.description}</p>
                          {isDisabled && (
                            <p className="text-[10px] text-amber-600">
                              No puede seleccionar PASS si se requiere medición y no existe ninguna
                              registrada.
                            </p>
                          )}
                        </div>
                      </label>
                    )
                  })}
                </div>
              </div>

              {selectedResult !== 'NOT_APPLICABLE' && (
                <>
                  <div>
                    <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Valor del resultado
                    </label>
                    <input
                      value={resultValue}
                      onChange={(e) => setResultValue(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Ingrese el valor del resultado..."
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Texto del resultado (opcional)
                    </label>
                    <input
                      value={resultText}
                      onChange={(e) => setResultText(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Descripción adicional del resultado..."
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Observación (opcional)
                    </label>
                    <textarea
                      value={observation}
                      onChange={(e) => setObservation(e.target.value)}
                      rows={2}
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Notas adicionales sobre el resultado..."
                    />
                  </div>
                </>
              )}

              {control?.sample_references && control.sample_references.length > 0 && (
                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                  <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Muestras asociadas
                  </h3>
                  <p className="text-xs text-slate-700">
                    {control.sample_references.length} muestra(s) vinculada(s) a este control.
                  </p>
                </div>
              )}
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
            loadingLabel="Registrando..."
            disabled={!canSubmit}
            onClick={() =>
              recordResult({
                result_value: selectedResult === 'NOT_APPLICABLE' ? undefined : resultValue || undefined,
                result_text: resultText || undefined,
                result_boolean: selectedResult === 'PASS' ? true : selectedResult === 'FAIL' ? false : undefined,
                notes: observation || undefined,
              })
            }
          >
            Registrar resultado
          </Button>
        </div>
      </div>
    </div>
  )
}
