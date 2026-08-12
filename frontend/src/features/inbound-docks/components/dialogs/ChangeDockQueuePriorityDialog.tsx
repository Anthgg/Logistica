import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { Input } from '../../../../components/common/Input'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { inboundDockQueueApi } from '../../api/inboundDockQueueApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { priorityLabel } from '../../utils/format'
import type {
  InboundDockPriority,
  InboundDockQueueEntry,
} from '../../types/inbound-docks'

const PRIORITIES: InboundDockPriority[] = ['LOW', 'NORMAL', 'HIGH', 'URGENT']

export function ChangeDockQueuePriorityDialog({
  open,
  entry,
  onOpenChange,
  onChanged,
}: {
  open: boolean
  entry: InboundDockQueueEntry | null
  onOpenChange: (open: boolean) => void
  onChanged?: (entry: InboundDockQueueEntry) => void
}) {
  const { hasPermission, requiresStepUp } = useLogisticsPermissions()
  const canChange = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.changePriority)
  const requiresStrong = requiresStepUp(LOGISTICS_PERMISSIONS.inboundDocks.changePriority)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.changePriority,
  })
  const [priority, setPriority] = useState<InboundDockPriority>('NORMAL')
  const [reason, setReason] = useState('')
  const [evidence, setEvidence] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const isUrgent = priority === 'URGENT'
  useEffect(() => {
    if (open && entry) {
      setPriority(entry.priority)
      setReason('')
      setEvidence('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open, entry])
  const mutation = useMutation<{
    entryId: string
    priority: InboundDockPriority
    reason: string
    evidence: string
  }, InboundDockQueueEntry>(
    async ({ entryId, priority: p, reason: r, evidence: ev }) => {
      return inboundDockQueueApi.changePriority(entryId, {
        priority: p,
        reason: r,
        evidence_file_id: ev || null,
      })
    },
    {
      onSuccess: (result) => {
        onOpenChange(false)
        onChanged?.(result)
      },
    },
  )
  if (!entry) return null
  const trimmedReason = reason.trim()
  const valid = trimmedReason.length >= 8
  const showError = touched && !valid
  const disabled = !canChange || !valid || mutation.isPending
  const submit = async () => {
    if (!entry) return
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const run = async (overrideReason: string) => {
      const result = await mutation.mutate({
        entryId: entry.id,
        priority,
        reason: overrideReason,
        evidence,
      })
      if (result) onChanged?.(result)
    }
    const ok = await guard.run(async () => {
      await run(trimmedReason)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Cambiar prioridad de cola"
      description={`Posición actual: #${entry.position}. Tiempo esperando: ${
        entry.waiting_seconds != null ? `${entry.waiting_seconds}s` : '—'
      }. Proveedor: ${entry.supplier_name ?? '—'}.`}
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant={isUrgent ? 'danger' : 'primary'}
            onClick={submit}
            disabled={disabled}
            isLoading={mutation.isPending || guard.isPending}
          >
            Confirmar cambio
          </Button>
        </>
      }
    >
      {!canChange && (
        <p className="mb-2 rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
          No tienes permiso para cambiar prioridades.
        </p>
      )}
      <div className="space-y-3">
        <fieldset>
          <legend className="mb-1 text-[11px] font-semibold uppercase text-slate-500">
            Prioridad nueva
          </legend>
          <div className="flex flex-wrap gap-2">
            {PRIORITIES.map((p) => (
              <label
                key={p}
                className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold ${
                  priority === p
                    ? 'border-[#1F4E6D] bg-[#1F4E6D]/5 text-[#1F4E6D]'
                    : 'border-slate-200 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="priority"
                  value={p}
                  checked={priority === p}
                  onChange={() => setPriority(p)}
                  className="sr-only"
                />
                {priorityLabel(p)}
              </label>
            ))}
          </div>
        </fieldset>
        <Input
          id="change-priority-reason"
          label="Motivo"
          required
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          onBlur={() => setTouched(true)}
          placeholder="Detalla por qué se cambia la prioridad"
          {...(showError ? { error: 'Indica un motivo de al menos 8 caracteres.' } : {})}
        />
        <Input
          id="change-priority-evidence"
          label="Evidencia (opcional)"
          value={evidence}
          onChange={(event) => setEvidence(event.target.value)}
          placeholder="ID de archivo"
        />
        {isUrgent && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
            Prioridad URGENTE. Se exigirá motivo y, si la capability lo requiere, step-up reforzado.
          </p>
        )}
        {requiresStrong && (
          <p className="rounded-lg border border-indigo-200 bg-indigo-50/40 p-2 text-[11px] text-indigo-700">
            Esta capability requiere step-up. El sistema abrirá el flujo reforzado al confirmar.
          </p>
        )}
        {guard.stepUpRequired && (
          <p className="rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-[11px] text-amber-700">
            Step-up requerido por el servidor. Completa el flujo reforzado para continuar.
          </p>
        )}
        {errorMessage && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700" role="alert">
            {errorMessage}
          </p>
        )}
        {mutation.error && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700" role="alert">
            {mutation.error}
          </p>
        )}
      </div>
    </DockModal>
  )
}
