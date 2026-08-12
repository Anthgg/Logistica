import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QuarantineRejectionAuthorization,
} from '../types/quarantine'
import { quarantineRejectionApi } from '../api/quarantineRejectionApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  authorization: QuarantineRejectionAuthorization
  onClose: () => void
  onApproved: (auth: QuarantineRejectionAuthorization) => void
}

export function ApproveQualityRejectionDialog({
  quarantineCase,
  authorization,
  isOpen,
  onClose,
  onApproved,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canApprove = hasPermission(LOGISTICS_PERMISSIONS.quarantine.approveRejection)

  const [comments, setComments] = useState('')

  const approveMutation = useMutation(
    (input: { authId: string; data: Parameters<typeof quarantineRejectionApi.approveAuthorization>[1] }) =>
      quarantineRejectionApi.approveAuthorization(input.authId, input.data),
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
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="approve-rejection-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 044 — Aprobación de rechazo</p>
            <h2 id="approve-rejection-title">Aprobar rechazo de calidad</h2>
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
                <span className="text-muted">Resultado</span>
                <p className="font-medium text-rose-600">FAIL</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad a rechazar</span>
                <p className="font-medium text-ink">{authorization.rejected_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
              <div>
                <span className="text-muted">Tipo de rechazo</span>
                <p className="font-medium text-ink">{authorization.rejection_type}</p>
              </div>
            </div>
            <div>
              <span className="text-muted">Motivo</span>
              <p className="font-medium text-ink">{authorization.reason}</p>
            </div>
            <div>
              <span className="text-muted">Método de disposición</span>
              <p className="font-medium text-ink">{authorization.disposal_method ?? 'No especificado'}</p>
            </div>
            <div>
              <span className="text-muted">Solicitado por</span>
              <p className="font-medium text-ink">{authorization.created_by.display_name}</p>
            </div>
            {authorization.non_conformity_id && (
              <div>
                <span className="text-muted">No conformidad</span>
                <p className="font-medium text-ink">{authorization.non_conformity_code ?? authorization.non_conformity_id}</p>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-[11px] text-blue-700 space-y-1">
            <p className="font-medium">Separación de funciones</p>
            <p>El aprobador no puede ser el mismo usuario que solicitó el rechazo.</p>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="approve-rejection-comments">Comentarios</label>
            <textarea
              id="approve-rejection-comments"
              className="field__input min-h-[60px]"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Comentarios de aprobación..."
            />
          </div>

          <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={comments.trim().length > 0}
              readOnly
              className="rounded"
            />
            Confirmo la aprobación del rechazo.
          </label>

          {approveMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700">
              {approveMutation.error}
            </div>
          )}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={approveMutation.isPending}>Rechazar solicitud</Button>
          <Button
            type="button"
            variant="danger"
            onClick={handleApprove}
            isLoading={approveMutation.isPending}
            loadingLabel="Aprobando..."
            disabled={!canApprove || approveMutation.isPending}
          >
            Aprobar rechazo
          </Button>
        </div>
      </div>
    </div>
  )
}
