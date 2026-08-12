import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QuarantineRejectionType,
  QuarantineRejectionAuthorization,
} from '../types/quarantine'
import { quarantineRejectionApi } from '../api/quarantineRejectionApi'

type DisposalRecommendation = 'RETURN' | 'DESTRUCTION' | 'REPROCESSING' | 'CLAIM' | 'KEEP_BLOCKED'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  onClose: () => void
  onCreated: (auth: QuarantineRejectionAuthorization) => void
}

export function RequestQualityRejectionDialog({
  quarantineCase,
  isOpen,
  onClose,
  onCreated,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestRejection)

  const [rejectionType, setRejectionType] = useState<QuarantineRejectionType>('TOTAL')
  const [quantity, setQuantity] = useState(quarantineCase.quarantined_quantity)
  const [reason, setReason] = useState('')
  const [evidence, setEvidence] = useState('')
  const [recommendation, setRecommendation] = useState<DisposalRecommendation | ''>('')
  const [confirmation, setConfirmation] = useState(false)

  const createMutation = useMutation(
    (input: { caseId: string; data: Parameters<typeof quarantineRejectionApi.createAuthorization>[1] }) =>
      quarantineRejectionApi.createAuthorization(input.caseId, input.data),
    {
      onSuccess: (result) => {
        if (result) onCreated(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setRejectionType('TOTAL')
    setQuantity(quarantineCase.quarantined_quantity)
    setReason('')
    setEvidence('')
    setRecommendation('')
    setConfirmation(false)
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

  const canSubmit = reason.trim().length > 0 && confirmation && canRequest

  const handleSubmit = () => {
    if (!canSubmit) return

    void createMutation.mutate({
      caseId: quarantineCase.case_id,
      data: {
        case_id: quarantineCase.case_id,
        rejection_type: rejectionType,
        rejected_quantity: rejectionType === 'PARTIAL' ? quantity : undefined,
        unit_id: quarantineCase.unit?.unit_id,
        reason: [
          reason,
          recommendation ? `Recomendación: ${recommendation}` : '',
          evidence ? `Evidencia: ${evidence}` : '',
        ]
          .filter(Boolean)
          .join('. '),
        disposal_method: recommendation || undefined,
      },
    })
  }

  const recommendationLabels: Record<DisposalRecommendation, string> = {
    RETURN: 'Devolución al proveedor',
    DESTRUCTION: 'Destrucción',
    REPROCESSING: 'Reprocesamiento',
    CLAIM: 'Reclamo',
    KEEP_BLOCKED: 'Mantener bloqueado',
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="reject-request-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 044 — Rechazo</p>
            <h2 id="reject-request-title">Solicitar rechazo de calidad</h2>
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
                <span className="text-muted">Cantidad en cuarentena</span>
                <p className="font-medium text-ink">{quarantineCase.quarantined_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
            </div>
          </div>

          <fieldset>
            <legend className="text-xs font-semibold text-ink mb-2">Tipo de rechazo</legend>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="radio" name="rejection-type" value="TOTAL" checked={rejectionType === 'TOTAL'} onChange={() => setRejectionType('TOTAL')} />
                Total
              </label>
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="radio" name="rejection-type" value="PARTIAL" checked={rejectionType === 'PARTIAL'} onChange={() => setRejectionType('PARTIAL')} />
                Parcial
              </label>
            </div>
          </fieldset>

          {rejectionType === 'PARTIAL' && (
            <Input
              label="Cantidad a rechazar"
              type="text"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="Cantidad (cadena)"
            />
          )}

          <Input
            label="Motivo del rechazo *"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describa el motivo del rechazo..."
          />

          <div className="field">
            <label className="field__label" htmlFor="reject-evidence">Evidencia</label>
            <textarea
              id="reject-evidence"
              className="field__input min-h-[60px]"
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              placeholder="Describa la evidencia que respalda el rechazo..."
            />
          </div>

          <fieldset>
            <legend className="text-xs font-semibold text-ink mb-2">Recomendación futura</legend>
            <div className="space-y-2">
              {(Object.entries(recommendationLabels) as [DisposalRecommendation, string][]).map(([val, label]) => (
                <label key={val} className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${recommendation === val ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300'}`}>
                  <input
                    type="radio"
                    name="recommendation"
                    value={val}
                    checked={recommendation === val}
                    onChange={() => setRecommendation(val)}
                  />
                  <span className="text-xs text-ink">{label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-700">
            Estas son recomendaciones. No ejecutan devolución, destrucción ni reclamo.
          </div>

          <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={confirmation}
              onChange={(e) => setConfirmation(e.target.checked)}
              className="rounded"
            />
            Confirmo que los datos del rechazo son correctos.
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
            variant="danger"
            onClick={handleSubmit}
            isLoading={createMutation.isPending}
            loadingLabel="Procesando..."
            disabled={!canSubmit || createMutation.isPending}
          >
            Solicitar rechazo
          </Button>
        </div>
      </div>
    </div>
  )
}
