import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QualityInspection,
  QualityDispositionDecisionType,
  QualityDispositionDecision,
} from '../types/quarantine'
import { qualityDispositionDecisionsApi } from '../api/qualityDispositionDecisionsApi'

const DECISION_OPTIONS: { value: QualityDispositionDecisionType; label: string; description: string }[] = [
  { value: 'APPROVE_QUALITY', label: 'Aprobar calidad', description: 'La mercancía pasa inspección y queda lista para liberación.' },
  { value: 'KEEP_IN_QUARANTINE', label: 'Mantener en cuarentena', description: 'Retener la mercancía para revisión adicional.' },
  { value: 'REQUEST_REINSPECTION', label: 'Solicitar reinspección', description: 'Repetir la inspección con controles adicionales.' },
  { value: 'REQUEST_ADDITIONAL_EVIDENCE', label: 'Solicitar evidencia adicional', description: 'Pedir documentación o fotos complementarias.' },
  { value: 'REQUEST_DOCUMENT_CORRECTION', label: 'Solicitar corrección documental', description: 'Requiere ajuste en certificados o documentos.' },
  { value: 'REQUEST_SUPERVISOR_REVIEW', label: 'Solicitar revisión de supervisor', description: 'Escalar a supervisión para decisión final.' },
]

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  inspection: QualityInspection | null
  onClose: () => void
  onCreated: (decision: QualityDispositionDecision) => void
}

export function ProposeQualityDispositionDecisionDialog({
  quarantineCase,
  inspection,
  isOpen,
  onClose,
  onCreated,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canPropose = hasPermission(LOGISTICS_PERMISSIONS.quarantine.proposeDecision)

  const [decisionType, setDecisionType] = useState<QualityDispositionDecisionType | ''>('')
  const [rationale, setRationale] = useState('')
  const [proposedQuantity, setProposedQuantity] = useState(quarantineCase.quarantined_quantity)
  const [conditions, setConditions] = useState('')

  const createMutation = useMutation(
    (input: { caseId: string; data: Parameters<typeof qualityDispositionDecisionsApi.create>[1] }) =>
      qualityDispositionDecisionsApi.create(input.caseId, input.data),
    {
      onSuccess: (result) => {
        if (result) onCreated(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setDecisionType('')
    setRationale('')
    setProposedQuantity(quarantineCase.quarantined_quantity)
    setConditions('')
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !createMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, quarantineCase.quarantined_quantity, createMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!createMutation.isPending) onClose()
  }

  const canSubmit = decisionType !== '' && rationale.trim().length > 0 && canPropose

  const handleSubmit = () => {
    if (!canSubmit || !decisionType) return
    const conditionsList = conditions
      .split('\n')
      .map((c) => c.trim())
      .filter(Boolean)

    void createMutation.mutate({
      caseId: quarantineCase.case_id,
      data: {
        case_id: quarantineCase.case_id,
        decision_type: decisionType,
        proposed_quantity: proposedQuantity,
        rationale,
        conditions: conditionsList.length > 0 ? conditionsList : undefined,
        inspection_id: inspection?.inspection_id,
        allocation_id: quarantineCase.allocation_ids[0],
      },
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="propose-disposition-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 042 — Disposición</p>
            <h2 id="propose-disposition-title">Proponer decisión de disposición</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={createMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body space-y-5">
          {/* Read-only context */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Caso</span>
                <p className="font-medium text-ink">{quarantineCase.case_code ?? quarantineCase.case_id}</p>
              </div>
              <div>
                <span className="text-muted">Resultado inspección</span>
                <p className="font-medium text-ink">{inspection?.overall_result ?? 'Sin inspección'}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad total</span>
                <p className="font-medium text-ink">{quarantineCase.total_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
              <div>
                <span className="text-muted">Cantidad en cuarentena</span>
                <p className="font-medium text-ink">{quarantineCase.quarantined_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
            </div>
            {inspection && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-muted">Controles fallidos</span>
                  <p className="font-medium text-ink">{inspection.controls_failed}</p>
                </div>
                <div>
                  <span className="text-muted">Evidencia</span>
                  <p className="font-medium text-ink">{inspection.evidence_count} archivos</p>
                </div>
              </div>
            )}
            {quarantineCase.reason && (
              <div>
                <span className="text-muted">Motivo de cuarentena</span>
                <p className="font-medium text-ink">{quarantineCase.reason}</p>
              </div>
            )}
          </div>

          {/* Decision type selection */}
          <fieldset>
            <legend className="text-xs font-semibold text-ink mb-2">Tipo de decisión</legend>
            <div className="space-y-2">
              {DECISION_OPTIONS.map((opt) => (
                <label key={opt.value} className={`flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${decisionType === opt.value ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300'}`}>
                  <input
                    type="radio"
                    name="disposition-type"
                    value={opt.value}
                    checked={decisionType === opt.value}
                    onChange={() => setDecisionType(opt.value)}
                    className="mt-0.5"
                  />
                  <div>
                    <span className="text-xs font-medium text-ink">{opt.label}</span>
                    <p className="text-[11px] text-muted mt-0.5">{opt.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </fieldset>

          <Input
            label="Cantidad propuesta"
            type="text"
            value={proposedQuantity}
            onChange={(e) => setProposedQuantity(e.target.value)}
            placeholder="Cantidad (cadena)"
          />

          <div className="field">
            <label className="field__label" htmlFor="disposition-rationale">Justificación *</label>
            <textarea
              id="disposition-rationale"
              className="field__input min-h-[80px]"
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Explique la razón de esta decisión..."
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="disposition-conditions">Condiciones (una por línea)</label>
            <textarea
              id="disposition-conditions"
              className="field__input min-h-[60px]"
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              placeholder="Condición 1&#10;Condición 2"
            />
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-700">
            Esta acción propone una decisión. No libera mercancía de forma directa.
          </div>

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
            Proponer decisión
          </Button>
        </div>
      </div>
    </div>
  )
}
