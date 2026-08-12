import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QualityInspection,
  QualityReinspectionRequest,
} from '../types/quarantine'
import { qualityQuarantineApi } from '../api/qualityQuarantineApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  inspection: QualityInspection | null
  onClose: () => void
  onCreated: (request: QualityReinspectionRequest) => void
}

export function RequestQualityReinspectionDialog({
  quarantineCase,
  inspection,
  isOpen,
  onClose,
  onCreated,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestReinspection)

  const [reason, setReason] = useState('')
  const [specificControls, setSpecificControls] = useState('')
  const [additionalRequirements, setAdditionalRequirements] = useState('')
  const [urgency, setUrgency] = useState('')
  const [planVersion, setPlanVersion] = useState(inspection?.plan_version_id ?? '')
  const [confirmation, setConfirmation] = useState(false)

  const createMutation = useMutation(
    (input: { caseId: string; data: Record<string, unknown> }) =>
      qualityQuarantineApi.requestReinspection(input.caseId, input.data),
    {
      onSuccess: (result) => {
        if (result) onCreated(result as QualityReinspectionRequest)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setReason('')
    setSpecificControls('')
    setAdditionalRequirements('')
    setUrgency('')
    setPlanVersion(inspection?.plan_version_id ?? '')
    setConfirmation(false)
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !createMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, inspection?.plan_version_id, createMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!createMutation.isPending) onClose()
  }

  const canSubmit = reason.trim().length > 0 && confirmation && canRequest

  const handleSubmit = () => {
    if (!canSubmit || !inspection) return
    const controlsList = specificControls
      .split('\n')
      .map((c) => c.trim())
      .filter(Boolean)

    void createMutation.mutate({
      caseId: quarantineCase.case_id,
      data: {
        case_id: quarantineCase.case_id,
        original_inspection_id: inspection.inspection_id,
        reason,
        specific_controls: controlsList.length > 0 ? controlsList : undefined,
        additional_requirements: additionalRequirements.trim() || undefined,
        urgency: urgency.trim() || undefined,
      },
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="reinspection-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 042 — Reinspección</p>
            <h2 id="reinspection-title">Solicitar reinspección de calidad</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={createMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Caso</span>
                <p className="font-medium text-ink">{quarantineCase.case_code ?? quarantineCase.case_id}</p>
              </div>
              <div>
                <span className="text-muted">Inspección anterior</span>
                <p className="font-medium text-ink">{inspection?.inspection_code ?? 'N/A'}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Resultado anterior</span>
                <p className="font-medium text-ink">{inspection?.overall_result ?? 'N/A'}</p>
              </div>
              <div>
                <span className="text-muted">Controles completados</span>
                <p className="font-medium text-ink">{inspection?.controls_completed ?? 0} / {inspection?.control_count ?? 0}</p>
              </div>
            </div>
            {inspection?.plan_code && (
              <div>
                <span className="text-muted">Plan de inspección</span>
                <p className="font-medium text-ink">{inspection.plan_code}</p>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-[11px] text-blue-700">
            La reinspección no modifica la inspección anterior. Se crea una nueva inspección vinculada al caso.
          </div>

          <Input
            label="Motivo de reinspección *"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Explique por qué se requiere reinspección..."
          />

          <div className="field">
            <label className="field__label" htmlFor="reinsp-controls">Controles a repetir (uno por línea)</label>
            <textarea
              id="reinsp-controls"
              className="field__input min-h-[60px]"
              value={specificControls}
              onChange={(e) => setSpecificControls(e.target.value)}
              placeholder="Código o nombre del control&#10;Código del control 2"
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="reinsp-additional">Requisitos adicionales</label>
            <textarea
              id="reinsp-additional"
              className="field__input min-h-[60px]"
              value={additionalRequirements}
              onChange={(e) => setAdditionalRequirements(e.target.value)}
              placeholder="Requisitos adicionales para la reinspección..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Urgencia"
              type="text"
              value={urgency}
              onChange={(e) => setUrgency(e.target.value)}
              placeholder="BAJA, MEDIA, ALTA"
            />
            <Input
              label="Versión del plan"
              type="text"
              value={planVersion}
              onChange={(e) => setPlanVersion(e.target.value)}
              placeholder="ID de versión"
            />
          </div>

          <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={confirmation}
              onChange={(e) => setConfirmation(e.target.checked)}
              className="rounded"
            />
            Confirmo que se requiere una nueva inspección para este caso.
          </label>

          {createMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700">
              {createMutation.error}
            </div>
          )}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={createMutation.isPending}>Cancelar</Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleSubmit}
            isLoading={createMutation.isPending}
            loadingLabel="Procesando..."
            disabled={!canSubmit || createMutation.isPending}
          >
            Solicitar reinspección
          </Button>
        </div>
      </div>
    </div>
  )
}
