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
  InventoryDispositionSplit,
} from '../types/quarantine'
import { quarantineRejectionApi } from '../api/quarantineRejectionApi'
import { inboundInventoryDispositionApi } from '../api/inboundInventoryDispositionApi'

type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 7

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  allocationId: string | null
  onClose: () => void
  onCompleted: (auth: QuarantineRejectionAuthorization) => void
}

export function PartialQualityRejectionWizard({
  quarantineCase,
  allocationId,
  isOpen,
  onClose,
  onCompleted,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canReject = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestRejection)

  const [step, setStep] = useState<WizardStep>(1)
  const [rejectionType] = useState<QuarantineRejectionType>('PARTIAL')
  const [rejectedQuantity, setRejectedQuantity] = useState('')
  const [reason, setReason] = useState('')
  const [evidence, setEvidence] = useState('')
  const [disposalMethod, setDisposalMethod] = useState('')
  const [splitResult, setSplitResult] = useState<InventoryDispositionSplit | null>(null)

  const splitMutation = useMutation(
    (input: { allocationId: string; data: Record<string, unknown> }) =>
      inboundInventoryDispositionApi.split(input.allocationId, input.data),
    {
      onSuccess: (result) => {
        if (result) {
          setSplitResult(result)
          setStep(7)
        }
      },
    },
  )

  const createRejectionMutation = useMutation(
    (input: { caseId: string; data: Parameters<typeof quarantineRejectionApi.createAuthorization>[1] }) =>
      quarantineRejectionApi.createAuthorization(input.caseId, input.data),
    {
      onSuccess: (result) => {
        if (result) onCompleted(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setStep(1)
    setRejectedQuantity('')
    setReason('')
    setEvidence('')
    setDisposalMethod('')
    setSplitResult(null)
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !splitMutation.isPending && !createRejectionMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, splitMutation.isPending, createRejectionMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!splitMutation.isPending && !createRejectionMutation.isPending) onClose()
  }

  const originalQuantity = quarantineCase.quarantined_quantity
  const remainingQuantity = String(
    Math.max(0, Number(originalQuantity) - Number(rejectedQuantity || '0')),
  )

  const steps = [
    { num: 1, label: 'Cantidad original' },
    { num: 2, label: 'Cantidad rechazada' },
    { num: 3, label: 'Cantidad restante' },
    { num: 4, label: 'Unidad y motivo' },
    { num: 5, label: 'Evidencia' },
    { num: 6, label: 'División resultante' },
    { num: 7, label: 'Ejecutar' },
  ]

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 1: Cantidad original</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-muted">Cantidad en cuarentena</span>
                <span className="font-medium text-ink">{originalQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Producto</span>
                <span className="font-medium text-ink">{quarantineCase.product?.name ?? 'N/A'}</span>
              </div>
            </div>
            <Button type="button" variant="primary" fullWidth onClick={() => setStep(2)}>Siguiente</Button>
          </div>
        )
      case 2:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 2: Cantidad rechazada</h3>
            <Input
              label="Cantidad a rechazar *"
              type="text"
              value={rejectedQuantity}
              onChange={(e) => setRejectedQuantity(e.target.value)}
              placeholder="Cantidad (cadena)"
            />
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(1)}>Atrás</Button>
              <Button
                type="button"
                variant="primary"
                fullWidth
                onClick={() => setStep(3)}
                disabled={!rejectedQuantity || Number(rejectedQuantity) <= 0 || Number(rejectedQuantity) > Number(originalQuantity)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )
      case 3:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 3: Cantidad restante</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-muted">Rechazada</span>
                <span className="font-medium text-rose-600">{rejectedQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Restante</span>
                <span className="font-medium text-amber-600">{remainingQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(2)}>Atrás</Button>
              <Button type="button" variant="primary" fullWidth onClick={() => setStep(4)}>Siguiente</Button>
            </div>
          </div>
        )
      case 4:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 4: Unidad y motivo</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
              <div className="flex justify-between">
                <span className="text-muted">Unidad</span>
                <span className="font-medium text-ink">{quarantineCase.unit?.name ?? 'N/A'} ({quarantineCase.unit?.symbol ?? ''})</span>
              </div>
            </div>
            <Input
              label="Motivo del rechazo *"
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Motivo..."
            />
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(3)}>Atrás</Button>
              <Button type="button" variant="primary" fullWidth onClick={() => setStep(5)} disabled={!reason.trim()}>Siguiente</Button>
            </div>
          </div>
        )
      case 5:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 5: Evidencia</h3>
            <div className="field">
              <label className="field__label" htmlFor="partial-evidence">Evidencia del rechazo</label>
              <textarea
                id="partial-evidence"
                className="field__input min-h-[60px]"
                value={evidence}
                onChange={(e) => setEvidence(e.target.value)}
                placeholder="Describa la evidencia..."
              />
            </div>
            <Input
              label="Método de disposición"
              type="text"
              value={disposalMethod}
              onChange={(e) => setDisposalMethod(e.target.value)}
              placeholder="Ej: RETURN, DESTRUCTION, CLAIM..."
            />
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(4)}>Atrás</Button>
              <Button type="button" variant="primary" fullWidth onClick={() => setStep(6)}>Siguiente</Button>
            </div>
          </div>
        )
      case 6:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 6: División resultante</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs space-y-2">
              <p className="font-semibold text-ink">Resumen de la división</p>
              <div className="flex justify-between">
                <span className="text-muted">Original</span>
                <span className="font-medium text-ink">{originalQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Rechazada</span>
                <span className="font-medium text-rose-600">{rejectedQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Restante</span>
                <span className="font-medium text-amber-600">{remainingQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-2 text-[11px] text-blue-700 mt-2">
                El backend valida que la suma exacta de rechazada + restante = original.
              </div>
            </div>
            <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
              <input
                type="checkbox"
                checked={splitResult !== null}
                readOnly
                className="rounded"
              />
              La división se procesará al confirmar.
            </label>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(5)}>Atrás</Button>
              <Button
                type="button"
                variant="danger"
                fullWidth
                onClick={() => {
                  if (!allocationId || !canReject) return
                  void splitMutation.mutate({
                    allocationId,
                    data: {
                      split_type: 'REJECTION',
                      quantity: rejectedQuantity,
                      reason,
                      disposal_method: disposalMethod || undefined,
                    },
                  })
                }}
                isLoading={splitMutation.isPending}
                loadingLabel="Procesando..."
                disabled={!canReject || splitMutation.isPending}
              >
                Confirmar división
              </Button>
            </div>
          </div>
        )
      case 7:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 7: Ejecutar rechazo</h3>
            {splitResult && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-xs space-y-2">
                <p className="font-semibold text-emerald-700">División completada</p>
                <div className="flex justify-between">
                  <span className="text-muted">Rechazada</span>
                  <span className="font-medium text-ink">{splitResult.rejected_quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Restante</span>
                  <span className="font-medium text-ink">{splitResult.remaining_quantity}</span>
                </div>
              </div>
            )}
            <Button
              type="button"
              variant="danger"
              fullWidth
              onClick={() => {
                if (!canReject) return
                void createRejectionMutation.mutate({
                  caseId: quarantineCase.case_id,
                  data: {
                    case_id: quarantineCase.case_id,
                    rejection_type: rejectionType,
                    rejected_quantity: rejectedQuantity,
                    unit_id: quarantineCase.unit?.unit_id,
                    reason,
                    disposal_method: disposalMethod || undefined,
                  },
                })
              }}
              isLoading={createRejectionMutation.isPending}
              loadingLabel="Creando solicitud..."
              disabled={!canReject || createRejectionMutation.isPending}
            >
              Crear solicitud de rechazo
            </Button>
          </div>
        )
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="partial-rejection-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 044 — Rechazo parcial</p>
            <h2 id="partial-rejection-title">Asistente de rechazo parcial</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={splitMutation.isPending || createRejectionMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body">
          <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
            {steps.map((s) => (
              <div
                key={s.num}
                className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium whitespace-nowrap ${
                  step === s.num
                    ? 'bg-primary text-white'
                    : step > s.num
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                {step > s.num ? '✓' : s.num}
                <span className="hidden sm:inline">{s.label}</span>
              </div>
            ))}
          </div>

          {splitMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700 mb-3">
              {splitMutation.error}
            </div>
          )}
          {createRejectionMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700 mb-3">
              {createRejectionMutation.error}
            </div>
          )}

          {renderStep()}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={splitMutation.isPending || createRejectionMutation.isPending}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  )
}
