import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { inboundInventoryDispositionApi } from '../api/inboundInventoryDispositionApi'
import type {
  InventoryDispositionSplit,
  InventoryDispositionSplitRecord,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface SplitInventoryDispositionDialogProps {
  isOpen: boolean
  allocationId: string
  onClose: () => void
  onSplitComplete: (result: InventoryDispositionSplit) => void
}

const SPLIT_TYPES = ['RELEASE', 'REJECTION', 'REINSPECTION'] as const
type SplitType = typeof SPLIT_TYPES[number]

export function SplitInventoryDispositionDialog({
  isOpen,
  allocationId,
  onClose,
  onSplitComplete,
}: SplitInventoryDispositionDialogProps) {
  const splitGuard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.quarantine.splitAllocation,
    requiresReason: true,
  })

  const { data: splitData, isLoading: isLoadingSplit } = useQuery<InventoryDispositionSplit>(
    ['split', allocationId],
    `/logistics/inbound-inventory-disposition/allocations/${allocationId}/split`,
    undefined,
    { enabled: isOpen && Boolean(allocationId) },
  )

  const [splitQuantity, setSplitQuantity] = useState<string>('')
  const [splitType, setSplitType] = useState<SplitType>('RELEASE')
  const [reason, setReason] = useState<string>('')
  const [destinationState, setDestinationState] = useState<string>('')
  const [evidenceFileId, setEvidenceFileId] = useState<string>('')
  const [confirmed, setConfirmed] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const splitMutation = useMutation(
    (input: Record<string, unknown>) =>
      inboundInventoryDispositionApi.split(allocationId, input),
    {
      onSuccess: (result) => {
        onSplitComplete(result)
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

    setSplitQuantity('')
    setSplitType('RELEASE')
    setReason('')
    setDestinationState('')
    setEvidenceFileId('')
    setConfirmed(false)
    setError(null)

    const previousFocus = document.activeElement as HTMLElement | null
    cancelButtonRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !splitMutation.isPending) handleClose()
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"])',
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
  }, [isOpen, splitMutation.isPending])

  if (!isOpen) return null

  const remainingQuantity = splitData?.remaining_quantity ?? '0'
  const originalQuantity = splitData?.original_quantity ?? '0'
  const trimmedQuantity = splitQuantity.trim()
  const trimmedReason = reason.trim()
  const isValidQuantity = trimmedQuantity.length > 0 && Number(trimmedQuantity) > 0
  const isValidQuantityRange = isValidQuantity && Number(trimmedQuantity) <= Number(remainingQuantity)
  const canSubmit = isValidQuantityRange && trimmedReason.length > 0 && confirmed && !splitGuard.stepUpRequired

  function handleClose() {
    if (!splitMutation.isPending) {
      onClose()
    }
  }

  async function handleConfirm() {
    if (!canSubmit) return
    setError(null)

    const payload: Record<string, unknown> = {
      split_type: splitType,
      quantity: trimmedQuantity,
      reason: trimmedReason,
      destination_state: destinationState || undefined,
      evidence_file_id: evidenceFileId || undefined,
    }

    const guardResult = await splitGuard.run(async (guardReason) => {
      if (guardReason) {
        payload.reason = guardReason
      }
    })

    if (!guardResult) return

    await splitMutation.mutate(payload)
  }

  const backendConversionEstimate = trimmedQuantity.length > 0
    ? `${trimmedQuantity} ${splitData?.unit?.symbol ?? ''}`
    : null

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={() => { if (!splitMutation.isPending) handleClose() }}
    >
      <div
        ref={dialogRef}
        className="dialog w-full max-w-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="split-disposition-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id="split-disposition-title" className="text-base font-bold">
          Dividir disposición de inventario
        </h2>

        {isLoadingSplit ? (
          <div className="py-8 text-center text-sm text-slate-500">Cargando datos…</div>
        ) : (
          <>
            <div className="mt-4 space-y-3">
              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Cantidad original:</span>
                  <span className="font-medium">{originalQuantity} {splitData?.unit?.symbol ?? ''}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Liberada:</span>
                  <span className="font-medium">{splitData?.released_quantity ?? '0'} {splitData?.unit?.symbol ?? ''}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Rechazada:</span>
                  <span className="font-medium">{splitData?.rejected_quantity ?? '0'} {splitData?.unit?.symbol ?? ''}</span>
                </div>
                <div className="flex justify-between font-semibold border-t border-slate-200 pt-1 mt-1">
                  <span>Restante:</span>
                  <span>{remainingQuantity} {splitData?.unit?.symbol ?? ''}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">Unidad:</span>
                <StatusBadge value={splitData?.unit?.code ?? 'N/A'} />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="field__label text-xs" htmlFor="split-type">Tipo de división</label>
                  <select
                    id="split-type"
                    className="field__input text-xs"
                    value={splitType}
                    onChange={(e) => setSplitType(e.target.value as SplitType)}
                    disabled={splitMutation.isPending}
                  >
                    {SPLIT_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <Input
                  id="split-quantity"
                  label="Cantidad a dividir"
                  type="text"
                  inputMode="decimal"
                  value={splitQuantity}
                  onChange={(e) => setSplitQuantity(e.target.value)}
                  disabled={splitMutation.isPending}
                  placeholder="0"
                  required
                />
              </div>

              {trimmedQuantity.length > 0 && (
                <div className="rounded-lg bg-blue-50 border border-blue-200 p-2 text-xs text-blue-700">
                  <span className="font-medium">Conversión backend estimada: </span>
                  {backendConversionEstimate}
                </div>
              )}

              {isValidQuantity && !isValidQuantityRange && (
                <Alert variant="warning">
                  La cantidad excede el saldo restante de {remainingQuantity}.
                </Alert>
              )}

              <Input
                id="split-reason"
                label="Motivo"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={splitMutation.isPending}
                required
                placeholder="Describe el motivo de la división"
              />

              <Input
                id="split-destination"
                label="Estado destino (opcional)"
                value={destinationState}
                onChange={(e) => setDestinationState(e.target.value)}
                disabled={splitMutation.isPending}
                placeholder="Ej: RELEASED, REJECTED"
              />

              <Input
                id="split-evidence"
                label="ID de evidencia (opcional)"
                value={evidenceFileId}
                onChange={(e) => setEvidenceFileId(e.target.value)}
                disabled={splitMutation.isPending}
                placeholder="File ID de evidencia adjunta"
              />

              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  disabled={splitMutation.isPending}
                  className="rounded border-slate-300"
                />
                Confirmo que los datos de la división son correctos
              </label>

              {splitData?.split_history && splitData.split_history.length > 0 && (
                <div className="mt-2">
                  <h3 className="text-xs font-semibold text-slate-600 mb-1">Historial de divisiones</h3>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {splitData.split_history.map((record: InventoryDispositionSplitRecord) => (
                      <div key={record.split_id} className="flex items-center justify-between text-[11px] bg-slate-50 rounded px-2 py-1">
                        <div className="flex items-center gap-2">
                          <StatusBadge value={record.split_type.toLowerCase()} />
                          <span>{record.quantity} {splitData.unit?.symbol ?? ''}</span>
                        </div>
                        <span className="text-slate-400">{record.destination ?? '—'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {(error || splitGuard.errorMessage) && (
              <Alert variant="error" title="Error">
                {error ?? splitGuard.errorMessage}
              </Alert>
            )}

            {splitGuard.stepUpRequired && (
              <Alert variant="warning" title="Autenticación requerida">
                Se requiere re-autenticación para esta operación sensible.
              </Alert>
            )}

            <div className="dialog__actions mt-4">
              <Button
                ref={cancelButtonRef}
                type="button"
                variant="secondary"
                onClick={handleClose}
                disabled={splitMutation.isPending}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={handleConfirm}
                isLoading={splitMutation.isPending}
                disabled={!canSubmit || splitMutation.isPending}
              >
                Confirmar división
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
