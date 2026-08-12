import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityMeasurementsApi } from '../api/qualityMeasurementsApi'
import type {
  QualityInspectionControl,
  QualityMeasurement,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface TemperatureMeasurementControlProps {
  control: QualityInspectionControl
  onMeasurementRecorded: (measurement: QualityMeasurement) => void
}

export function TemperatureMeasurementControl({
  control,
  onMeasurementRecorded,
}: TemperatureMeasurementControlProps) {
  const auth = useLogisticsPermissions()
  const canRecord = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordMeasurement)

  const [value, setValue] = useState<string>('')
  const [unit, setUnit] = useState<string>(control.unit?.code ?? 'C')
  const [measurementPoint, setMeasurementPoint] = useState<string>('')
  const [device, setDevice] = useState<string>('')
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

  let expectedRange: string | null = null
  if (minValue && maxValue) {
    expectedRange = `${minValue} – ${maxValue} ${control.unit?.symbol ?? '°C'}`
  } else if (minValue) {
    expectedRange = `≥ ${minValue} ${control.unit?.symbol ?? '°C'}`
  } else if (maxValue) {
    expectedRange = `≤ ${maxValue} ${control.unit?.symbol ?? '°C'}`
  }

  let toleranceResult: string | null = null
  const warnings: string[] = []

  if (isValidValue) {
    const numVal = Number(trimmedValue)
    if (Number.isNaN(numVal)) {
      warnings.push('El valor no es un número válido')
    } else {
      if (numVal < 0) {
        warnings.push('Valor negativo detectado')
      }

      const hasRange = Boolean(minValue && maxValue)
      if (hasRange) {
        const numMin = Number(minValue)
        const numMax = Number(maxValue)
        toleranceResult = (numVal >= numMin && numVal <= numMax)
          ? 'DENTRO_DE_TOLERANCIA'
          : 'FUERA_DE_TOLERANCIA'
      } else if (targetValue) {
        const numTarget = Number(targetValue)
        toleranceResult = numVal === numTarget
          ? 'DENTRO_DE_TOLERANCIA'
          : 'FUERA_DE_TOLERANCIA'
      }

      if (toleranceResult === 'FUERA_DE_TOLERANCIA') {
        warnings.push('La temperatura está fuera del rango esperado')
      }
    }
  }

  function handleRecord() {
    if (!isValidValue || !canRecord) return
    setError(null)

    const pointNumber = measurementPoint ? Number(measurementPoint) : undefined

    void recordMutation.mutate({
      control_id: control.control_id,
      measurement_type: 'TEMPERATURE',
      value: trimmedValue,
      unit_id: control.unit?.unit_id ?? '',
      target_value: targetValue ?? undefined,
      min_value: minValue ?? undefined,
      max_value: maxValue ?? undefined,
      measurement_point: pointNumber,
      device_id: device || undefined,
      device_name: device || undefined,
      environment_conditions: sample || undefined,
      notes: comment || undefined,
    } as Parameters<typeof qualityMeasurementsApi.create>[1])
  }

  const isCompleted = control.status === 'COMPLETED'

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-sm text-slate-800">Medición de temperatura</h4>
          <p className="text-[11px] text-slate-500 mt-0.5">{control.description ?? 'Registro de temperatura del producto'}</p>
        </div>
        <StatusBadge value={control.status.toLowerCase().replace(/_/g, ' ')} />
      </div>

      {targetValue && (
        <div className="rounded bg-blue-50 border border-blue-200 p-2 text-[11px] text-blue-700">
          <span className="font-medium">Objetivo: </span>{targetValue} {control.unit?.symbol ?? '°C'}
        </div>
      )}

      {expectedRange && (
        <div className="rounded bg-slate-50 border border-slate-200 p-2 text-[11px] text-slate-600">
          <span className="font-medium">Rango esperado: </span>{expectedRange}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Input
          id={`temp-value-${control.control_id}`}
          label="Valor (string)"
          type="text"
          inputMode="decimal"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="-20.0"
          required
        />

        <Input
          id={`temp-unit-${control.control_id}`}
          label="Unidad"
          value={unit}
          onChange={(e) => setUnit(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder={control.unit?.symbol ?? '°C'}
        />

        <Input
          id={`temp-point-${control.control_id}`}
          label="Punto de medición"
          value={measurementPoint}
          onChange={(e) => setMeasurementPoint(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Nº punto de medición"
        />

        <Input
          id={`temp-device-${control.control_id}`}
          label="Dispositivo"
          value={device}
          onChange={(e) => setDevice(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="ID o nombre del termómetro"
        />

        <Input
          id={`temp-sample-${control.control_id}`}
          label="Muestra"
          value={sample}
          onChange={(e) => setSample(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Referencia de muestra"
        />

        <Input
          id={`temp-evidence-${control.control_id}`}
          label="ID de evidencia"
          value={evidenceFileId}
          onChange={(e) => setEvidenceFileId(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="File ID"
        />
      </div>

      <div>
        <label className="field__label text-xs" htmlFor={`temp-comment-${control.control_id}`}>
          Comentario
        </label>
        <textarea
          id={`temp-comment-${control.control_id}`}
          className="field__input text-xs min-h-[50px] resize-y"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Notas sobre la medición"
        />
      </div>

      {isValidValue && toleranceResult && (
        <div className={`rounded p-2 text-[11px] font-medium ${
          toleranceResult === 'DENTRO_DE_TOLERANCIA'
            ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-rose-50 border border-rose-200 text-rose-700'
        }`}>
          Evaluación backend: {toleranceResult.replace(/_/g, ' ')}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="space-y-1">
          {warnings.map((w, i) => (
            <Alert key={i} variant="warning">{w}</Alert>
          ))}
        </div>
      )}

      {isValidValue && (
        <div className="text-[11px] text-slate-500">
          <span className="font-medium">Valor registrado: </span>{trimmedValue} {unit || (control.unit?.symbol ?? '°C')}
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
          Registrar temperatura
        </Button>
      )}
    </div>
  )
}
