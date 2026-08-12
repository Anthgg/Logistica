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
  onExecuted: (auth: QuarantineRejectionAuthorization) => void
}

export function ExecuteQualityRejectionDialog({
  quarantineCase,
  authorization,
  isOpen,
  onClose,
  onExecuted,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canExecute = hasPermission(LOGISTICS_PERMISSIONS.quarantine.executeRejection)

  const [confirmation, setConfirmation] = useState(false)

  const executeMutation = useMutation(
    (input: { authId: string }) =>
      quarantineRejectionApi.executeRejection(input.authId),
    {
      onSuccess: (result) => {
        if (result) onExecuted(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setConfirmation(false)
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !executeMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, executeMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!executeMutation.isPending) onClose()
  }

  const handleExecute = () => {
    if (!confirmation || !canExecute) return
    void executeMutation.mutate({ authId: authorization.authorization_id })
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="execute-rejection-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 044 — Ejecución de rechazo</p>
            <h2 id="execute-rejection-title">Ejecutar rechazo de calidad</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={executeMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad autorizada</span>
                <p className="font-medium text-ink">{authorization.rejected_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
              <div>
                <span className="text-muted">Unidad</span>
                <p className="font-medium text-ink">{quarantineCase.unit?.name ?? 'N/A'}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Estado actual</span>
                <p className="font-medium text-ink">{authorization.status}</p>
              </div>
              <div>
                <span className="text-muted">Estado futuro</span>
                <p className="font-medium text-rose-600">REJECTED_NOT_AVAILABLE</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-700 space-y-1">
            <p>• La cantidad será rechazada y no estará disponible.</p>
            <p>• No será removida ni retirada físicamente por esta acción.</p>
          </div>

          <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={confirmation}
              onChange={(e) => setConfirmation(e.target.checked)}
              className="rounded"
            />
            Confirmo que la cantidad y el producto son correctos para rechazar.
          </label>

          {executeMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700">
              {executeMutation.error}
            </div>
          )}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={executeMutation.isPending}>Cancelar</Button>
          <Button
            type="button"
            variant="danger"
            onClick={handleExecute}
            isLoading={executeMutation.isPending}
            loadingLabel="Ejecutando..."
            disabled={!confirmation || !canExecute || executeMutation.isPending}
          >
            Ejecutar rechazo
          </Button>
        </div>
      </div>
    </div>
  )
}
