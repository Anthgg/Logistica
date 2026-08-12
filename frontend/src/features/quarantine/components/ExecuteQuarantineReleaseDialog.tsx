import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QuarantineReleaseAuthorization,
} from '../types/quarantine'
import { quarantineReleaseApi } from '../api/quarantineReleaseApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  authorization: QuarantineReleaseAuthorization
  onClose: () => void
  onExecuted: (auth: QuarantineReleaseAuthorization) => void
}

export function ExecuteQuarantineReleaseDialog({
  quarantineCase,
  authorization,
  isOpen,
  onClose,
  onExecuted,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canExecute = hasPermission(LOGISTICS_PERMISSIONS.quarantine.executeRelease)

  const [confirmation, setConfirmation] = useState(false)

  const executeMutation = useMutation(
    (input: { authId: string }) =>
      quarantineReleaseApi.executeRelease(input.authId),
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
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="execute-release-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 043 — Ejecución</p>
            <h2 id="execute-release-title">Ejecutar liberación de cuarentena</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={executeMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad autorizada</span>
                <p className="font-medium text-ink">{authorization.released_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
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
                <p className="font-medium text-emerald-600">RELEASED_FOR_PUTAWAY</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Zona de cuarentena</span>
                <p className="font-medium text-ink">{quarantineCase.quarantine_zone_name ?? 'N/A'}</p>
              </div>
              <div>
                <span className="text-muted">Producto</span>
                <p className="font-medium text-ink">{quarantineCase.product?.name ?? 'N/A'}</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-[11px] text-blue-700 space-y-1">
            <p className="font-medium">Preparación Fase 043</p>
            <p>La mercancía quedará disponible para generar una tarea de putaway en la Fase 043.</p>
            <p>Esta acción no crea un PUT task ni un MOV movement.</p>
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-700">
            Confirmación física: verifique que la cantidad y el producto corresponden antes de ejecutar.
          </div>

          <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={confirmation}
              onChange={(e) => setConfirmation(e.target.checked)}
              className="rounded"
            />
            Confirmo que la cantidad y el producto son correctos para liberar.
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
            variant="primary"
            onClick={handleExecute}
            isLoading={executeMutation.isPending}
            loadingLabel="Ejecutando..."
            disabled={!confirmation || !canExecute || executeMutation.isPending}
          >
            Ejecutar liberación
          </Button>
        </div>
      </div>
    </div>
  )
}
