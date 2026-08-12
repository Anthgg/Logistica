import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QualityInspection,
  QualityDispositionDecision,
} from '../types/quarantine'
import { qualityDispositionDecisionsApi } from '../api/qualityDispositionDecisionsApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  inspection: QualityInspection | null
  decision: QualityDispositionDecision
  onClose: () => void
  onApproved: (decision: QualityDispositionDecision) => void
}

export function ApproveQualityDecisionDialog({
  quarantineCase,
  inspection,
  decision,
  isOpen,
  onClose,
  onApproved,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canApprove = hasPermission(LOGISTICS_PERMISSIONS.quarantine.approveQuality)

  const [comments, setComments] = useState('')

  const approveMutation = useMutation(
    (input: { decisionId: string; data: Parameters<typeof qualityDispositionDecisionsApi.approve>[1] }) =>
      qualityDispositionDecisionsApi.approve(input.decisionId, input.data),
    {
      onSuccess: (result) => {
        if (result) onApproved(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setComments('')
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !approveMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, approveMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!approveMutation.isPending) onClose()
  }

  const handleApprove = () => {
    void approveMutation.mutate({
      decisionId: decision.decision_id,
      data: { decision: 'APPROVE', comments: comments.trim() || undefined },
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="approve-quality-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 042 — Aprobación de calidad</p>
            <h2 id="approve-quality-title">Aprobar decisión de calidad</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={approveMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Caso</span>
                <p className="font-medium text-ink">{quarantineCase.case_code ?? quarantineCase.case_id}</p>
              </div>
              <div>
                <span className="text-muted">Inspección</span>
                <p className="font-medium text-ink">{inspection?.inspection_code ?? inspection?.inspection_id ?? 'N/A'}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Resultado inspección</span>
                <p className="font-medium text-ink">{inspection?.overall_result ?? 'Sin resultado'}</p>
              </div>
              <div>
                <span className="text-muted">Tipo de decisión</span>
                <p className="font-medium text-ink">{decision.decision_type}</p>
              </div>
            </div>
            <div>
              <span className="text-muted">Justificación</span>
              <p className="font-medium text-ink">{decision.rationale}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad propuesta</span>
                <p className="font-medium text-ink">{decision.proposed_quantity ?? quarantineCase.total_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
              <div>
                <span className="text-muted">Proponente</span>
                <p className="font-medium text-ink">{decision.proposed_by.display_name}</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-[11px] text-muted space-y-1">
            <p className="font-medium text-ink">Separación de funciones</p>
            <p>El aprobador no puede ser el mismo usuario que propuso la decisión.</p>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="approve-quality-comments">Comentarios</label>
            <textarea
              id="approve-quality-comments"
              className="field__input min-h-[60px]"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Comentarios opcionales..."
            />
          </div>

          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-[11px] text-emerald-700">
            Aprobar la calidad habilita la solicitud de liberación, pero no pone la mercancía a disposición por sí solo.
          </div>

          {approveMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700">
              {approveMutation.error}
            </div>
          )}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={approveMutation.isPending}>Cancelar</Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleApprove}
            isLoading={approveMutation.isPending}
            loadingLabel="Aprobando..."
            disabled={!canApprove || approveMutation.isPending}
          >
            Aprobar calidad
          </Button>
        </div>
      </div>
    </div>
  )
}
