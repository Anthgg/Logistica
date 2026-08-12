import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityMeasurementsApi } from '../api/qualityMeasurementsApi'
import type {
  QualityInspectionControl,
  QualityMeasurement,
  QualityToleranceResult,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface WeightMeasurementControlProps {
  control: QualityInspectionControl
  onMeasurementRecorded: (measurement: QualityMeasurement) => void
}

export function WeightMeasurementControl({
  control,
  onMeasurementRecorded,
}: WeightMeasurementControlProps) {
  const auth = useLogisticsPermissions()
  const canRecord = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordMeasurement)

  const [value, setValue] = useState<string>('')
  const [unit, setUnit] = useState<string>(control.unit?.code ?? '')
  const [scaleReference, setScaleReference] = useState<string>('')
  const [calibrationReference, setCalibrationReference] = useState<string>('')
  const [sample, setSample] = useState<string>('')
  const [evidenceFileId, setEvidenceFileId] = useState<string>('')
  const [comment, setComment] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const recordMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityMeasurementsApi.create(control.control_id, input as Parameters<typeof qualityMeasurementsApi.create>[1]),
    {
      onSuccess: (result) => {
        onMeasurementRecorded(result)
        setValue('')
        setComment('')
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const targetValue = control.expected_value ?? null
  const minValue = control.min_value ?? null
  const maxValue = control.max_value ?? null

  const trimmedValue = value.trim()
  const isValidValue = trimmedValue.length > 0

  let rangeLabel: string | null = null
  if (minValue && maxValue) {
    rangeLabel = `${minValue} – ${maxValue} ${control.unit?.symbol ?? ''}`
  } else if (minValue) {
    rangeLabel = `≥ ${minValue} ${control.unit?.symbol ?? ''}`
  } else if (maxValue) {
    rangeLabel = `≤ ${maxValue} ${control.unit?.symbol ?? ''}`
  }

  let backendToleranceResult: QualityToleranceResult | null = null
  if (isValidValue && targetValue) {
    const numVal = Number(trimmedValue)
    const numTarget = Number(targetValue)
    if (!Number.isNaN(numVal) && !Number.isNaN(numTarget)) {
      const hasRange = Boolean(minValue && maxValue)
      if (hasRange) {
        const numMin = Number(minValue)
        const numMax = Number(maxValue)
        backendToleranceResult = (numVal >= numMin && numVal <= numMax)
          ? 'WITHIN_TOLERANCE'
          : 'OUTSIDE_TOLERANCE'
      } else {
        backendToleranceResult = numVal === numTarget
          ? 'WITHIN_TOLERANCE'
          : 'OUTSIDE_TOLERANCE'
      }
    }
  }

  const originalValue = trimmedValue
  const officialConversion = trimmedValue.length > 0
    ? `${trimmedValue} ${unit || (control.unit?.symbol ?? '')}`
    : null

  function handleRecord() {
    if (!isValidValue || !canRecord) return
    setError(null)

    void recordMutation.mutate({
      control_id: control.control_id,
      measurement_type: 'WEIGHT',
      value: trimmedValue,
      unit_id: control.unit?.unit_id ?? '',
      target_value: targetValue ?? undefined,
      min_value: minValue ?? undefined,
      max_value: maxValue ?? undefined,
      device_id: scaleReference || undefined,
      device_name: scaleReference || undefined,
      calibrated: calibrationReference.length > 0 ? true : undefined,
      calibration_date: calibrationReference || undefined,
      environment_conditions: sample || undefined,
      notes: comment || undefined,
    } as Parameters<typeof qualityMeasurementsApi.create>[1])
  }

  const isCompleted = control.status === 'COMPLETED'

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-sm text-slate-800">Medición de peso</h4>
          <p className="text-[11px] text-slate-500 mt-0.5">{control.description ?? 'Registro de peso del producto'}</p>
        </div>
        <StatusBadge value={control.status.toLowerCase().replace(/_/g, ' ')} />
      </div>

      {targetValue && (
        <div className="rounded bg-blue-50 border border-blue-200 p-2 text-[11px] text-blue-700">
          <span className="font-medium">Objetivo: </span>{targetValue} {control.unit?.symbol ?? ''}
        </div>
      )}

      {rangeLabel && (
        <div className="rounded bg-slate-50 border border-slate-200 p-2 text-[11px] text-slate-600">
          <span className="font-medium">Rango esperado: </span>{rangeLabel}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Input
          id={`weight-value-${control.control_id}`}
          label="Valor (string)"
          type="text"
          inputMode="decimal"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="0.00"
          required
        />

        <Input
          id={`weight-unit-${control.control_id}`}
          label="Unidad"
          value={unit}
          onChange={(e) => setUnit(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder={control.unit?.symbol ?? 'kg'}
        />

        <Input
          id={`weight-scale-${control.control_id}`}
          label="Referencia de báscula"
          value={scaleReference}
          onChange={(e) => setScaleReference(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="ID o nombre de báscula"
        />

        <Input
          id={`weight-calibration-${control.control_id}`}
          label="Referencia de calibración"
          value={calibrationReference}
          onChange={(e) => setCalibrationReference(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Fecha o referencia de calibración"
        />

        <Input
          id={`weight-sample-${control.control_id}`}
          label="Muestra"
          value={sample}
          onChange={(e) => setSample(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Referencia de muestra"
        />

        <Input
          id={`weight-evidence-${control.control_id}`}
          label="ID de evidencia"
          value={evidenceFileId}
          onChange={(e) => setEvidenceFileId(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="File ID"
        />
      </div>

      <div>
        <label className="field__label text-xs" htmlFor={`weight-comment-${control.control_id}`}>
          Comentario
        </label>
        <textarea
          id={`weight-comment-${control.control_id}`}
          className="field__input text-xs min-h-[50px] resize-y"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Notas sobre la medición"
        />
      </div>

      {isValidValue && backendToleranceResult && (
        <div className={`rounded p-2 text-[11px] font-medium ${
          backendToleranceResult === 'WITHIN_TOLERANCE'
            ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-rose-50 border border-rose-200 text-rose-700'
        }`}>
          Resultado de tolerancia backend: {backendToleranceResult.replace(/_/g, ' ')}
        </div>
      )}

      {originalValue && (
        <div className="text-[11px] text-slate-500">
          <span className="font-medium">Valor original: </span>{originalValue}
        </div>
      )}

      {officialConversion && (
        <div className="text-[11px] text-slate-500">
          <span className="font-medium">Conversión oficial: </span>{officialConversion}
        </div>
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {!isCompleted && canRecord && (
        <Button
          type="button"
          variant="primary"
          size="small"
          onClick={handleRecord}
          isLoading={recordMutation.isPending}
          disabled={!isValidValue || recordMutation.isPending}
        >
          Registrar peso
        </Button>
      )}
    </div>
  )
}
