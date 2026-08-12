import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityQuarantineApi } from '../api/qualityQuarantineApi'
import type {
  QuarantinePlacement,
  QualityQuarantineCase,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface ConfirmQuarantinePlacementDialogProps {
  isOpen: boolean
  placementId: string
  caseId: string
  onClose: () => void
  onConfirmed: (placement: QuarantinePlacement) => void
}

export function ConfirmQuarantinePlacementDialog({
  isOpen,
  placementId,
  caseId,
  onClose,
  onConfirmed,
}: ConfirmQuarantinePlacementDialogProps) {
  const auth = useLogisticsPermissions()
  const canConfirm = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.confirmPlacement)

  const { data: caseData, isLoading: isLoadingCase } = useQuery<QualityQuarantineCase>(
    ['quarantine-case', caseId],
    `/logistics/quality-quarantine/cases/${caseId}`,
    undefined,
    { enabled: isOpen && Boolean(caseId) },
  )

  const { data: placements, isLoading: isLoadingPlacements } = useQuery<QuarantinePlacement[]>(
    ['quarantine-placements', caseId],
    `/logistics/quality-quarantine/cases/${caseId}/placements`,
    undefined,
    { enabled: isOpen && Boolean(caseId) },
  )

  const [scanCode, setScanCode] = useState<string>('')
  const [evidenceFileId, setEvidenceFileId] = useState<string>('')
  const [confirmed, setConfirmed] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const placement = placements?.find((p) => p.placement_id === placementId)

  const confirmMutation = useMutation(
    () => qualityQuarantineApi.confirmPlacement(placementId),
    {
      onSuccess: (result) => {
        onConfirmed(result)
        handleClose()
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const dialogRef = useRef<HTMLDivElement>(null)
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!isOpen) return undefined

    setScanCode('')
    setEvidenceFileId('')
    setConfirmed(false)
    setError(null)

    const previousFocus = document.activeElement as HTMLElement | null
    cancelButtonRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !confirmMutation.isPending) handleClose()
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      )
      const first = focusable[0]
      const last = focusable.at(-1)
      if (!first || !last) return

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previousFocus?.focus()
    }
  }, [isOpen, confirmMutation.isPending])

  if (!isOpen) return null

  const isLoading = isLoadingCase || isLoadingPlacements
  const canSubmit = confirmed && !confirmMutation.isPending && canConfirm

  function handleClose() {
    if (!confirmMutation.isPending) onClose()
  }

  async function handleConfirm() {
    if (!canSubmit) return
    setError(null)
    await confirmMutation.mutate(undefined as never)
  }

  const restrictions: string[] = []
  if (caseData?.quarantine_zone_name) {
    restrictions.push(`Zona: ${caseData.quarantine_zone_name}`)
  }
  if (placement?.lot_number) {
    restrictions.push(`Lote: ${placement.lot_number}`)
  }
  if (placement?.serial_number) {
    restrictions.push(`Serie: ${placement.serial_number}`)
  }

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={() => { if (!confirmMutation.isPending) handleClose() }}
    >
      <div
        ref={dialogRef}
        className="dialog w-full max-w-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-placement-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id="confirm-placement-title" className="text-base font-bold">
          Confirmar ubicación física
        </h2>

        {isLoading ? (
          <div className="py-8 text-center text-sm text-slate-500">Cargando datos…</div>
        ) : !placement ? (
          <Alert variant="error">No se encontró la ubicación especificada.</Alert>
        ) : (
          <>
            <div className="mt-4 space-y-3">
              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Caso:</span>
                  <span className="font-medium">{caseData?.case_code ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Producto:</span>
                  <span className="font-medium">{caseData?.product?.name ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Cantidad:</span>
                  <span className="font-medium">{placement.quantity} {placement.unit?.symbol ?? ''}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Unidad:</span>
                  <span className="font-medium">{placement.unit?.name ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Zona:</span>
                  <span className="font-medium">{placement.zone?.name ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Ubicación:</span>
                  <span className="font-medium">{placement.location?.code ?? '—'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Estado:</span>
                  <StatusBadge value={placement.status.toLowerCase()} />
                </div>
              </div>

              {restrictions.length > 0 && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-2 text-xs">
                  <span className="font-semibold text-amber-700">Restricciones: </span>
                  <span className="text-amber-600">{restrictions.join(' | ')}</span>
                </div>
              )}

              <Input
                id="placement-scan-code"
                label="Código de escaneo"
                value={scanCode}
                onChange={(e) => setScanCode(e.target.value)}
                disabled={confirmMutation.isPending}
                placeholder="Escanea el código de la ubicación"
              />

              <Input
                id="placement-evidence"
                label="ID de evidencia (opcional)"
                value={evidenceFileId}
                onChange={(e) => setEvidenceFileId(e.target.value)}
                disabled={confirmMutation.isPending}
                placeholder="File ID de foto de evidencia"
              />

              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  disabled={confirmMutation.isPending}
                  className="rounded border-slate-300"
                />
                Confirmo que la ubicación física coincide con el registro
              </label>

              {!canConfirm && (
                <Alert variant="warning">
                  No tienes permiso para confirmar esta ubicación.
                </Alert>
              )}
            </div>

            {error && (
              <Alert variant="error" title="Error">{error}</Alert>
            )}

            <div className="dialog__actions mt-4">
              <Button
                ref={cancelButtonRef}
                type="button"
                variant="secondary"
                onClick={handleClose}
                disabled={confirmMutation.isPending}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={handleConfirm}
                isLoading={confirmMutation.isPending}
                disabled={!canSubmit}
              >
                Confirmar ubicación
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
