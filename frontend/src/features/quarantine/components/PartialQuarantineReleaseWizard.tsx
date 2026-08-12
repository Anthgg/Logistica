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
  InventoryDispositionSplit,
} from '../types/quarantine'
import { quarantineReleaseApi } from '../api/quarantineReleaseApi'
import { inboundInventoryDispositionApi } from '../api/inboundInventoryDispositionApi'

type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8

interface Props {
  isOpen: boolean
  quarantineCase: QualityQuarantineCase
  allocationId: string | null
  onClose: () => void
  onCompleted: (auth: QuarantineReleaseAuthorization) => void
}

export function PartialQuarantineReleaseWizard({
  quarantineCase,
  allocationId,
  isOpen,
  onClose,
  onCompleted,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { hasPermission } = useLogisticsPermissions()
  const canRelease = hasPermission(LOGISTICS_PERMISSIONS.quarantine.requestRelease)

  const [step, setStep] = useState<WizardStep>(1)
  const [releaseType] = useState<QuarantineReleaseType>('PARTIAL')
  const [releaseQuantity, setReleaseQuantity] = useState('')
  const [reason, setReason] = useState('')
  const [confirmation, setConfirmation] = useState(false)
  const [splitResult, setSplitResult] = useState<InventoryDispositionSplit | null>(null)

  const splitMutation = useMutation(
    (input: { allocationId: string; data: Record<string, unknown> }) =>
      inboundInventoryDispositionApi.split(input.allocationId, input.data),
    {
      onSuccess: (result) => {
        if (result) {
          setSplitResult(result)
          setStep(8)
        }
      },
    },
  )

  const createReleaseMutation = useMutation(
    (input: { caseId: string; data: Parameters<typeof quarantineReleaseApi.createAuthorization>[1] }) =>
      quarantineReleaseApi.createAuthorization(input.caseId, input.data),
    {
      onSuccess: (result) => {
        if (result) onCompleted(result)
      },
    },
  )

  useEffect(() => {
    if (!isOpen) return
    setStep(1)
    setReleaseQuantity('')
    setReason('')
    setConfirmation(false)
    setSplitResult(null)
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !splitMutation.isPending && !createReleaseMutation.isPending) onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, splitMutation.isPending, createReleaseMutation.isPending, onClose])

  if (!isOpen) return null

  const close = () => {
    if (!splitMutation.isPending && !createReleaseMutation.isPending) onClose()
  }

  const originalQuantity = quarantineCase.quarantined_quantity
  const remainingQuantity = String(
    Math.max(0, Number(originalQuantity) - Number(releaseQuantity || '0')),
  )

  const steps = [
    { num: 1, label: 'Revisar cantidad original' },
    { num: 2, label: 'Ingresar cantidad a liberar' },
    { num: 3, label: 'Revisar cantidad restante' },
    { num: 4, label: 'Revisar unidades' },
    { num: 5, label: 'Revisar inspección' },
    { num: 6, label: 'Revisar autorización' },
    { num: 7, label: 'Confirmar división' },
    { num: 8, label: 'Ejecutar liberación' },
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
              <div className="flex justify-between">
                <span className="text-muted">SKU</span>
                <span className="font-medium text-ink">{quarantineCase.product?.sku ?? 'N/A'}</span>
              </div>
            </div>
            <Button type="button" variant="primary" fullWidth onClick={() => setStep(2)}>Siguiente</Button>
          </div>
        )
      case 2:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 2: Cantidad a liberar</h3>
            <Input
              label="Cantidad a liberar *"
              type="text"
              value={releaseQuantity}
              onChange={(e) => setReleaseQuantity(e.target.value)}
              placeholder="Ingrese la cantidad (cadena)"
            />
            <p className="text-[11px] text-muted">La cantidad debe ser menor a {originalQuantity} {quarantineCase.unit?.symbol ?? ''}</p>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(1)}>Atrás</Button>
              <Button
                type="button"
                variant="primary"
                fullWidth
                onClick={() => setStep(3)}
                disabled={!releaseQuantity || Number(releaseQuantity) <= 0 || Number(releaseQuantity) >= Number(originalQuantity)}
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
                <span className="text-muted">Cantidad a liberar</span>
                <span className="font-medium text-emerald-600">{releaseQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Cantidad restante</span>
                <span className="font-medium text-amber-600">{remainingQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">La parte restante permanecerá en cuarentena</span>
                <span></span>
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
            <h3 className="text-sm font-semibold text-ink">Paso 4: Revisión de unidades</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-muted">Unidad de medida</span>
                <span className="font-medium text-ink">{quarantineCase.unit?.name ?? 'N/A'} ({quarantineCase.unit?.symbol ?? ''})</span>
              </div>
            </div>
            <p className="text-[11px] text-muted">Ambas partes mantienen la misma unidad de medida.</p>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(3)}>Atrás</Button>
              <Button type="button" variant="primary" fullWidth onClick={() => setStep(5)}>Siguiente</Button>
            </div>
          </div>
        )
      case 5:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 5: Revisión de inspección</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-muted">Inspección</span>
                <span className="font-medium text-ink">{quarantineCase.inspection_code ?? 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Decisión de disposición</span>
                <span className="font-medium text-ink">{quarantineCase.disposition_decision_type ?? 'N/A'}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(4)}>Atrás</Button>
              <Button type="button" variant="primary" fullWidth onClick={() => setStep(6)}>Siguiente</Button>
            </div>
          </div>
        )
      case 6:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 6: Revisión de autorización</h3>
            <div className="field">
              <label className="field__label" htmlFor="partial-reason">Motivo *</label>
              <textarea
                id="partial-reason"
                className="field__input min-h-[60px]"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Motivo de la liberación parcial..."
              />
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(5)}>Atrás</Button>
              <Button type="button" variant="primary" fullWidth onClick={() => setStep(7)} disabled={!reason.trim()}>Siguiente</Button>
            </div>
          </div>
        )
      case 7:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 7: Confirmar división</h3>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs space-y-2">
              <p className="font-semibold text-ink text-xs">Resumen de la división</p>
              <div className="flex justify-between">
                <span className="text-muted">Parte liberada</span>
                <span className="font-medium text-emerald-600">{releaseQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Parte restante (cuarentena)</span>
                <span className="font-medium text-amber-600">{remainingQuantity} {quarantineCase.unit?.symbol ?? ''}</span>
              </div>
            </div>
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-[11px] text-blue-700">
              Se creará una nueva asignación para la parte liberada. La asignación original no se sobrescribe.
            </div>
            <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
              <input
                type="checkbox"
                checked={confirmation}
                onChange={(e) => setConfirmation(e.target.checked)}
                className="rounded"
              />
              Confirmo la división correcta de cantidades.
            </label>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" fullWidth onClick={() => setStep(6)}>Atrás</Button>
              <Button
                type="button"
                variant="primary"
                fullWidth
                onClick={() => {
                  if (!allocationId || !confirmation || !canRelease) return
                  void splitMutation.mutate({
                    allocationId,
                    data: {
                      split_type: 'RELEASE',
                      quantity: releaseQuantity,
                      reason,
                    },
                  })
                }}
                isLoading={splitMutation.isPending}
                loadingLabel="Dividiendo..."
                disabled={!confirmation || !canRelease || splitMutation.isPending}
              >
                Confirmar división
              </Button>
            </div>
          </div>
        )
      case 8:
        return (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">Paso 8: Ejecutar liberación</h3>
            {splitResult && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-xs space-y-2">
                <p className="font-semibold text-emerald-700">División completada</p>
                <div className="flex justify-between">
                  <span className="text-muted">Cantidad liberada</span>
                  <span className="font-medium text-ink">{splitResult.released_quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Cantidad restante</span>
                  <span className="font-medium text-ink">{splitResult.remaining_quantity}</span>
                </div>
                <div>
                  <span className="text-muted">Árbol de asignaciones</span>
                  <div className="mt-1 space-y-1">
                    <div className="rounded bg-white p-2 border border-slate-200 text-[11px]">
                      Original: {splitResult.original_quantity} → Restante: {splitResult.remaining_quantity}
                    </div>
                    <div className="rounded bg-emerald-50 p-2 border border-emerald-200 text-[11px]">
                      Liberada: {splitResult.released_quantity}
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] text-amber-700">
              La asignación original no se sobrescribe. Se creó una nueva asignación para la parte liberada.
            </div>
            <Button
              type="button"
              variant="primary"
              fullWidth
              onClick={() => {
                if (!canRelease) return
                void createReleaseMutation.mutate({
                  caseId: quarantineCase.case_id,
                  data: {
                    case_id: quarantineCase.case_id,
                    release_type: releaseType,
                    released_quantity: releaseQuantity,
                    unit_id: quarantineCase.unit?.unit_id,
                    reason,
                    decision_id: quarantineCase.disposition_decision_id ?? undefined,
                  },
                })
              }}
              isLoading={createReleaseMutation.isPending}
              loadingLabel="Creando solicitud..."
              disabled={!canRelease || createReleaseMutation.isPending}
            >
              Crear solicitud de liberación
            </Button>
          </div>
        )
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={close}>
      <div ref={dialogRef} className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="partial-release-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="resource-dialog__header">
          <div>
            <p className="eyebrow">Fase 043 — Liberación parcial</p>
            <h2 id="partial-release-title">Asistente de liberación parcial</h2>
          </div>
          <button type="button" className="icon-button" onClick={close} aria-label="Cerrar" disabled={splitMutation.isPending || createReleaseMutation.isPending}>×</button>
        </div>

        <div className="resource-dialog__body">
          {/* Step indicator */}
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
          {createReleaseMutation.error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-700 mb-3">
              {createReleaseMutation.error}
            </div>
          )}

          {renderStep()}
        </div>

        <div className="resource-dialog__footer">
          <Button type="button" variant="secondary" onClick={close} disabled={splitMutation.isPending || createReleaseMutation.isPending}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  )
}
