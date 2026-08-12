import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QualityInspection,
  QualityDispositionDecision,
  QuarantineReleaseAuthorization,
} from '../types/quarantine'
import { quarantineReleaseApi } from '../api/quarantineReleaseApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  inspection: QualityInspection | null
  decision: QualityDispositionDecision | null
  authorization: QuarantineReleaseAuthorization
  onClose: () => void
  onApproved: (auth: QuarantineReleaseAuthorization) => void
}

export function ApproveQuarantineReleaseDialog({
  quarantineCase,
  inspection,
  decision,
  authorization,
  isOpen,
  onClose,
  onApproved,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canApprove = hasPermission(LOGISTICS_PERMISSIONS.quarantine.approveRelease)

  const [comments, setComments] = useState('')

  const approveMutation = useMutation(
    (input: { authId: string; data: Parameters<typeof quarantineReleaseApi.approveAuthorization>[1] }) =>
      quarantineReleaseApi.approveAuthorization(input.authId, input.data),
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
      authId: authorization.authorization_id,
      data: { decision: 'APPROVE', comments: comments.trim() || undefined },
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="approve-release-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 043 — Aprobación de liberación</p>
            <h2 id="approve-release-title">Aprobar liberación de cuarentena</h2>
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
                <span className="text-muted">Tipo de liberación</span>
                <p className="font-medium text-ink">{authorization.release_type}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad</span>
                <p className="font-medium text-ink">{authorization.released_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
              <div>
                <span className="text-muted">Estado actual</span>
                <p className="font-medium text-ink">{authorization.status}</p>
              </div>
            </div>
            {inspection && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-muted">Inspección</span>
                  <p className="font-medium text-ink">{inspection.inspection_code ?? inspection.inspection_id}</p>
                </div>
                <div>
                  <span className="text-muted">Resultado</span>
                  <p className="font-medium text-ink">{inspection.overall_result}</p>
                </div>
              </div>
            )}
            {decision && (
              <div>
                <span className="text-muted">Decisión de disposición</span>
                <p className="font-medium text-ink">{decision.decision_type} — {decision.status}</p>
              </div>
            )}
            <div>
              <span className="text-muted">Motivo</span>
              <p className="font-medium text-ink">{authorization.reason}</p>
            </div>
            <div>
              <span className="text-muted">Solicitado por</span>
              <p className="font-medium text-ink">{authorization.created_by.display_name}</p>
            </div>
            {authorization.conditions.length > 0 && (
              <div>
                <span className="text-muted">Condiciones</span>
                <ul className="list-disc list-inside space-y-0.5">
                  {authorization.conditions.map((c, i) => (
                    <li key={i} className="font-medium text-ink">{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-[11px] text-blue-700 space-y-1">
            <p className="font-medium">Requiere step-up de aprobación</p>
            <p>El aprobador no puede ser el mismo usuario que solicitó la liberación.</p>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="approve-release-comments">Comentarios</label>
            <textarea
              id="approve-release-comments"
              className="field__input min-h-[60px]"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Comentarios de aprobación..."
            />
          </div>

          {approveMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700">
              {approveMutation.error}
            </div>
          )}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={approveMutation.isPending}>Rechazar</Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleApprove}
            isLoading={approveMutation.isPending}
            loadingLabel="Aprobando..."
            disabled={!canApprove || approveMutation.isPending}
          >
            Aprobar liberación
          </Button>
        </div>
      </div>
    </div>
  )
}
