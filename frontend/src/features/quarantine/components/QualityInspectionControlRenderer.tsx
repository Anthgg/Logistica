import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type {
  QualityInspectionControl,
  QualityInspectionControlStatus,
  QualityInspectionEvidence,
  QualityInspectionSampleReference,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface QualityInspectionControlRendererProps {
  control: QualityInspectionControl
  onControlUpdated: (control: QualityInspectionControl) => void
}

type ResultValueType =
  | 'BOOLEAN'
  | 'DECIMAL'
  | 'INTEGER'
  | 'TEXT_SHORT'
  | 'DATE'
  | 'OPTION'
  | 'DOCUMENT_REFERENCE'
  | 'PHOTO_REFERENCE'
  | 'SAMPLE_SET'

const STATUS_COLORS: Record<QualityInspectionControlStatus, string> = {
  PENDING: 'text-slate-500',
  IN_PROGRESS: 'text-blue-600',
  COMPLETED: 'text-emerald-600',
  NOT_APPLICABLE: 'text-slate-400',
  FAILED: 'text-rose-600',
  CORRECTED: 'text-amber-600',
}

export function QualityInspectionControlRenderer({
  control,
  onControlUpdated,
}: QualityInspectionControlRendererProps) {
  const auth = useLogisticsPermissions()
  const canRecord = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordControlResult)

  const [resultValue, setResultValue] = useState<string>(control.result_value ?? '')
  const [resultText, setResultText] = useState<string>(control.result_text ?? '')
  const [resultBoolean, setResultBoolean] = useState<boolean>(control.result_boolean ?? false)
  const [selectedOption, setSelectedOption] = useState<string>(control.result_value ?? '')
  const [error, setError] = useState<string | null>(null)

  const recordMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionsApi.recordControlResult(control.control_id, input),
    {
      onSuccess: (result) => {
        onControlUpdated(result)
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const startMutation = useMutation(
    () => qualityInspectionsApi.startControl(control.control_id),
    {
      onSuccess: (result) => {
        onControlUpdated(result)
      },
    },
  )

  const skipMutation = useMutation(
    () =>
      qualityInspectionsApi.markControlNotApplicable(control.control_id),
    {
      onSuccess: (result) => {
        onControlUpdated(result)
      },
    },
  )

  const valueType = control.result_value_type as ResultValueType

  function handleRecordResult() {
    setError(null)
    const payload: Record<string, unknown> = {
      control_id: control.control_id,
    }

    switch (valueType) {
      case 'BOOLEAN':
        payload.result_boolean = resultBoolean
        break
      case 'DECIMAL':
      case 'INTEGER':
        payload.result_value = resultValue
        break
      case 'TEXT_SHORT':
        payload.result_text = resultText
        break
      case 'DATE':
        payload.result_value = resultValue
        break
      case 'OPTION':
        payload.result_value = selectedOption
        break
      case 'DOCUMENT_REFERENCE':
      case 'PHOTO_REFERENCE':
        payload.result_value = resultValue
        break
      case 'SAMPLE_SET':
        payload.result_value = resultValue
        break
      default:
        payload.result_value = resultValue
    }

    void recordMutation.mutate(payload)
  }

  const isCompleted = control.status === 'COMPLETED'
  const isInProgress = control.status === 'IN_PROGRESS'
  const isFailed = control.status === 'FAILED'
  const isNotApplicable = control.status === 'NOT_APPLICABLE'

  const previousResult = control.condition_results?.length
    ? control.condition_results.map((cr) => `${cr.condition_field}: ${cr.actual_value ?? '—'}`).join(', ')
    : null

  const evidenceItems: QualityInspectionEvidence[] = control.evidence ?? []
  const sampleRefs: QualityInspectionSampleReference[] = control.sample_references ?? []

  const toleranceLabel = control.tolerance_result
    ? control.tolerance_result.replace(/_/g, ' ')
    : null

  const renderInput = () => {
    switch (valueType) {
      case 'BOOLEAN':
        return (
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input
                type="radio"
                name={`bool-${control.control_id}`}
                checked={resultBoolean === true}
                onChange={() => setResultBoolean(true)}
                disabled={isCompleted || isNotApplicable || recordMutation.isPending}
              />
              Sí
            </label>
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input
                type="radio"
                name={`bool-${control.control_id}`}
                checked={resultBoolean === false}
                onChange={() => setResultBoolean(false)}
                disabled={isCompleted || isNotApplicable || recordMutation.isPending}
              />
              No
            </label>
          </div>
        )
      case 'DECIMAL':
      case 'INTEGER':
        return (
          <Input
            id={`result-${control.control_id}`}
            label="Valor"
            type="text"
            inputMode={valueType === 'INTEGER' ? 'numeric' : 'decimal'}
            value={resultValue}
            onChange={(e) => setResultValue(e.target.value)}
            disabled={isCompleted || isNotApplicable || recordMutation.isPending}
            placeholder={control.expected_value ?? '0'}
            endAdornment={control.unit?.symbol ? <span className="text-xs text-slate-500">{control.unit.symbol}</span> : undefined}
          />
        )
      case 'TEXT_SHORT':
        return (
          <Input
            id={`result-${control.control_id}`}
            label="Valor"
            value={resultText}
            onChange={(e) => setResultText(e.target.value)}
            disabled={isCompleted || isNotApplicable || recordMutation.isPending}
            placeholder="Ingrese el resultado"
          />
        )
      case 'DATE':
        return (
          <Input
            id={`result-${control.control_id}`}
            label="Fecha"
            type="date"
            value={resultValue}
            onChange={(e) => setResultValue(e.target.value)}
            disabled={isCompleted || isNotApplicable || recordMutation.isPending}
          />
        )
      case 'OPTION':
        return (
          <div>
            <label className="field__label text-xs" htmlFor={`option-${control.control_id}`}>
              Opción
            </label>
            <select
              id={`option-${control.control_id}`}
              className="field__input text-xs"
              value={selectedOption}
              onChange={(e) => setSelectedOption(e.target.value)}
              disabled={isCompleted || isNotApplicable || recordMutation.isPending}
            >
              <option value="">Seleccionar…</option>
              <option value="PASS">Aprobado</option>
              <option value="FAIL">Rechazado</option>
              <option value="OBSERVATION">Con observaciones</option>
            </select>
          </div>
        )
      case 'DOCUMENT_REFERENCE':
      case 'PHOTO_REFERENCE':
        return (
          <Input
            id={`result-${control.control_id}`}
            label="Referencia"
            value={resultValue}
            onChange={(e) => setResultValue(e.target.value)}
            disabled={isCompleted || isNotApplicable || recordMutation.isPending}
            placeholder="ID del archivo o referencia"
          />
        )
      case 'SAMPLE_SET':
        return (
          <Input
            id={`result-${control.control_id}`}
            label="Conjunto de muestras"
            value={resultValue}
            onChange={(e) => setResultValue(e.target.value)}
            disabled={isCompleted || isNotApplicable || recordMutation.isPending}
            placeholder="Referencia del conjunto"
          />
        )
      default:
        return (
          <Input
            id={`result-${control.control_id}`}
            label="Valor"
            value={resultValue}
            onChange={(e) => setResultValue(e.target.value)}
            disabled={isCompleted || isNotApplicable || recordMutation.isPending}
          />
        )
    }
  }

  return (
    <div className={`rounded-lg border p-4 text-xs space-y-3 ${
      isFailed ? 'border-rose-200 bg-rose-50/50' :
      isCompleted ? 'border-emerald-200 bg-emerald-50/50' :
      'border-slate-200 bg-white'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-slate-800">{control.name}</span>
            <span className="text-[10px] text-slate-400 font-mono">{control.code}</span>
          </div>
          {control.description && (
            <p className="mt-1 text-slate-500 text-[11px]">{control.description}</p>
          )}
          {control.evidence_required && (
            <span className="inline-flex items-center gap-1 mt-1 text-[10px] text-amber-600 font-medium">
              <span className="h-1 w-1 rounded-full bg-amber-500" />
              Evidencia requerida
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={STATUS_COLORS[control.status]}>
            <StatusBadge value={control.status.toLowerCase().replace(/_/g, ' ')} />
          </span>
          {control.required && (
            <span className="text-[10px] text-slate-400 font-medium">Requerido</span>
          )}
          {control.blocking_future && (
            <span className="text-[10px] text-rose-500 font-medium">Bloqueante</span>
          )}
        </div>
      </div>

      {control.instructions && (
        <div className="rounded bg-slate-100 p-2 text-[11px] text-slate-600">
          <span className="font-medium">Instrucciones: </span>{control.instructions}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {control.unit && (
          <div className="text-[11px] text-slate-500">
            <span className="font-medium">Unidad: </span>{control.unit.name} ({control.unit.symbol})
          </div>
        )}
        {control.expected_value && (
          <div className="text-[11px] text-slate-500">
            <span className="font-medium">Esperado: </span>{control.expected_value}
          </div>
        )}
        {control.min_value && (
          <div className="text-[11px] text-slate-500">
            <span className="font-medium">Mín: </span>{control.min_value}
          </div>
        )}
        {control.max_value && (
          <div className="text-[11px] text-slate-500">
            <span className="font-medium">Máx: </span>{control.max_value}
          </div>
        )}
      </div>

      {toleranceLabel && (
        <div className={`text-[11px] font-medium ${
          control.tolerance_result === 'WITHIN_TOLERANCE' ? 'text-emerald-600' :
          control.tolerance_result === 'OUTSIDE_TOLERANCE' ? 'text-rose-600' :
          'text-slate-500'
        }`}>
          Tolerancia: {toleranceLabel}
        </div>
      )}

      {previousResult && (
        <div className="text-[11px] text-slate-500">
          <span className="font-medium">Resultado anterior: </span>{previousResult}
        </div>
      )}

      {!isCompleted && !isNotApplicable && canRecord && (
        <div className="space-y-2">
          {renderInput()}
          <div className="flex gap-2">
            {!isInProgress && (
              <Button
                type="button"
                variant="ghost"
                size="small"
                onClick={() => void startMutation.mutate(undefined as never)}
                disabled={startMutation.isPending}
              >
                Iniciar
              </Button>
            )}
            <Button
              type="button"
              variant="primary"
              size="small"
              onClick={handleRecordResult}
              isLoading={recordMutation.isPending}
              disabled={recordMutation.isPending}
            >
              Registrar resultado
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="small"
              onClick={() => void skipMutation.mutate({ control_id: control.control_id })}
              disabled={skipMutation.isPending}
            >
              No aplica
            </Button>
          </div>
        </div>
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {evidenceItems.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold text-slate-600 mb-1">Evidencia</h4>
          <div className="space-y-1">
            {evidenceItems.map((ev) => (
              <div key={ev.evidence_id} className="flex items-center gap-2 text-[11px] text-slate-500">
                <StatusBadge value={ev.evidence_type.toLowerCase()} />
                <span>{ev.file?.filename ?? '—'}</span>
                {ev.classification && <span className="text-slate-400">({ev.classification})</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {sampleRefs.length > 0 && (
        <div>
          <h4 className="text-[11px] font-semibold text-slate-600 mb-1">Muestras</h4>
          <div className="flex flex-wrap gap-1">
            {sampleRefs.map((sr) => (
              <span key={sr.reference_id} className="inline-flex items-center rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                #{sr.sample_number}
                {sr.lot_number && ` Lote: ${sr.lot_number}`}
                {sr.serial_number && ` Ser: ${sr.serial_number}`}
              </span>
            ))}
          </div>
        </div>
      )}

      {control.certificate_reviews?.length ? (
        <div>
          <h4 className="text-[11px] font-semibold text-slate-600 mb-1">Certificados</h4>
          <div className="space-y-1">
            {control.certificate_reviews.map((cr) => (
              <div key={cr.review_id} className="flex items-center gap-2 text-[11px] text-slate-500">
                <StatusBadge value={cr.status.toLowerCase()} />
                <span>{cr.requirement_name ?? 'Certificado'}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
