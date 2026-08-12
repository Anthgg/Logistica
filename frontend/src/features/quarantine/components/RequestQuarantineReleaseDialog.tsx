import { useEffect, useRef, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineCase,
  QuarantineReleaseType,
  QuarantineReleaseAuthorization,
} from '../types/quarantine'
import { quarantineReleaseApi } from '../api/quarantineReleaseApi'

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  onClose: () => void
  onCreated: (auth: QuarantineReleaseAuthorization) => void
}

export function RequestQuarantineReleaseDialog({
  quarantineCase,
  isOpen,
  onClose,
  onCreated,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestRelease)

  const [releaseType, setReleaseType] = useState<QuarantineReleaseType>('TOTAL')
  const [quantity, setQuantity] = useState(quarantineCase.quarantined_quantity)
  const [reason, setReason] = useState('')
  const [conditions, setConditions] = useState('')
  const [confirmation, setConfirmation] = useState(false)

  const createMutation = useMutation(
    (input: { caseId: string; data: Parameters<typeof quarantineReleaseApi.createAuthorization>[1] }) =>
      quarantineReleaseApi.createAuthorization(input.caseId, input.data),
    {
      onSuccess: (result) => {
        if (result) onCreated(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setReleaseType('TOTAL')
    setQuantity(quarantineCase.quarantined_quantity)
    setReason('')
    setConditions('')
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
    const conditionsList = conditions
      .split('\n')
      .map((c) => c.trim())
      .filter(Boolean)

    void createMutation.mutate({
      caseId: quarantineCase.case_id,
      data: {
        case_id: quarantineCase.case_id,
        release_type: releaseType,
        released_quantity: releaseType === 'PARTIAL' ? quantity : undefined,
        unit_id: quarantineCase.unit?.unit_id,
        reason,
        conditions: conditionsList.length > 0 ? conditionsList : undefined,
        decision_id: quarantineCase.disposition_decision_id ?? undefined,
      },
    })
  }

  const availableQuantity = quarantineCase.released_quantity ?? '0'
  const remainingAfterRelease =
    releaseType === 'TOTAL'
      ? '0'
      : String(
          Math.max(
            0,
            Number(quarantineCase.quarantined_quantity) - Number(quantity || '0'),
          ),
        )

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="release-request-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 043 — Liberación</p>
            <h2 id="release-request-title">Solicitar liberación de cuarentena</h2>
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
                <span className="text-muted">Calidad aprobada</span>
                <p className="font-medium text-ink">{quarantineCase.has_disposition_decision ? 'Sí' : 'No'}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-muted">Cantidad disponible</span>
                <p className="font-medium text-ink">{availableQuantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
              <div>
                <span className="text-muted">Cantidad en cuarentena</span>
                <p className="font-medium text-ink">{quarantineCase.quarantined_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
              </div>
            </div>
          </div>

          <fieldset>
            <legend className="text-xs font-semibold text-ink mb-2">Tipo de liberación</legend>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="radio" name="release-type" value="TOTAL" checked={releaseType === 'TOTAL'} onChange={() => setReleaseType('TOTAL')} />
                Total
              </label>
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="radio" name="release-type" value="PARTIAL" checked={releaseType === 'PARTIAL'} onChange={() => setReleaseType('PARTIAL')} />
                Parcial
              </label>
            </div>
          </fieldset>

          {releaseType === 'PARTIAL' && (
            <Input
              label="Cantidad a liberar"
              type="text"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="Cantidad (cadena)"
            />
          )}

          <Input
            label="Motivo de liberación *"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Motivo de la solicitud..."
          />

          <div className="field">
            <label className="field__label" htmlFor="release-conditions">Condiciones (una por línea)</label>
            <textarea
              id="release-conditions"
              className="field__input min-h-[60px]"
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              placeholder="Condición 1&#10;Condición 2"
            />
          </div>

          <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={confirmation}
              onChange={(e) => setConfirmation(e.target.checked)}
              className="rounded"
            />
            Confirmo que la cantidad a liberar es correcta.
          </label>

          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-[11px] text-emerald-700 space-y-1">
            <p>• Calidad aprobada: {quarantineCase.has_disposition_decision ? 'Sí' : 'No'}</p>
            <p>• Cantidad restante después de liberación: {remainingAfterRelease} {quarantineCase.unit?.symbol ?? ''}</p>
            <p>• El siguiente estado será AVAILABLE_FOR_PUTAWAY.</p>
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
            loadingLabel="Solicitando..."
            disabled={!canSubmit || createMutation.isPending}
          >
            Solicitar liberación
          </Button>
        </div>
      </div>
    </div>
  )
}
