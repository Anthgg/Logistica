import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { QualityQuarantineCase, QualityDispositionDecision } from '../types/quarantine'
import { qualityDispositionDecisionsApi } from '../api/qualityDispositionDecisionsApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  onClose: () => void
  onCreated: (decision: QualityDispositionDecision) => void
}

export function KeepInQuarantineDialog({
  quarantineCase,
  isOpen,
  onClose,
  onCreated,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canKeep = hasPermission(LOGISTICS_PERMISSIONS.quarantine.keepQuarantined)

  const [reason, setReason] = useState('')
  const [reviewDate, setReviewDate] = useState('')
  const [additionalEvidence, setAdditionalEvidence] = useState('')
  const [responsible, setResponsible] = useState('')
  const [comment, setComment] = useState('')

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
    setReason('')
    setReviewDate('')
    setAdditionalEvidence('')
    setResponsible('')
    setComment('')
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !createMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, createMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!createMutation.isPending) onClose()
  }

  const canSubmit = reason.trim().length > 0 && responsible.trim().length > 0 && canKeep

  const handleSubmit = () => {
    if (!canSubmit) return
    const rationale = [
      `Mantener en cuarentena: ${reason}`,
      reviewDate ? `Fecha de revisión sugerida: ${reviewDate}` : '',
      additionalEvidence ? `Evidencia adicional requerida: ${additionalEvidence}` : '',
      `Responsable: ${responsible}`,
      comment ? `Comentario: ${comment}` : '',
    ]
      .filter(Boolean)
      .join('. ')

    void createMutation.mutate({
      caseId: quarantineCase.case_id,
      data: {
        case_id: quarantineCase.case_id,
        decision_type: 'KEEP_IN_QUARANTINE',
        proposed_quantity: quarantineCase.quarantined_quantity,
        rationale,
      },
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="keep-quarantine-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 042 — Cuarentena</p>
            <h2 id="keep-quarantine-title">Mantener en cuarentena</h2>
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

          <Input
            label="Motivo de retención *"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describa el motivo..."
          />

          <Input
            label="Fecha de revisión sugerida"
            type="date"
            value={reviewDate}
            onChange={(e) => setReviewDate(e.target.value)}
          />

          <div className="field">
            <label className="field__label" htmlFor="keep-evidence">Evidencia adicional requerida</label>
            <textarea
              id="keep-evidence"
              className="field__input min-h-[60px]"
              value={additionalEvidence}
              onChange={(e) => setAdditionalEvidence(e.target.value)}
              placeholder="Documentos, fotos, certificados adicionales..."
            />
          </div>

          <Input
            label="Responsable *"
            type="text"
            value={responsible}
            onChange={(e) => setResponsible(e.target.value)}
            placeholder="Nombre del responsable..."
          />

          <div className="field">
            <label className="field__label" htmlFor="keep-comment">Comentario</label>
            <textarea
              id="keep-comment"
              className="field__input min-h-[60px]"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Comentarios adicionales..."
            />
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-700 space-y-1">
            <p>• La cantidad permanecerá bloqueada.</p>
            <p>• No estará disponible para putaway.</p>
            <p>• Puede requerir reinspección.</p>
            <p>• No se modifica la availability_class local.</p>
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
            variant="danger"
            onClick={handleSubmit}
            isLoading={createMutation.isPending}
            loadingLabel="Procesando..."
            disabled={!canSubmit || createMutation.isPending}
          >
            Mantener en cuarentena
          </Button>
        </div>
      </div>
    </div>
  )
}
