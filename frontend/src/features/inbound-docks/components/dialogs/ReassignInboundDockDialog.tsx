import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { compatibilityLabel } from '../../utils/format'
import type { DockCompatibilityResult, InboundDockAssignment } from '../../types/inbound-docks'

export function ReassignInboundDockDialog({
  open,
  assignment,
  newDockId,
  onOpenChange,
  onReassigned,
}: {
  open: boolean
  assignment: InboundDockAssignment | null
  newDockId: string | null
  onOpenChange: (open: boolean) => void
  onReassigned?: (assignment: InboundDockAssignment) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canReassign = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.reassign)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.reassign,
  })
  const [reason, setReason] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setReason('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ assignmentId: string; newDockId: string; reason: string }, InboundDockAssignment>(
    async (input) =>
      dockAssignmentsApi.reassign(input.assignmentId, {
        new_dock_id: input.newDockId,
        reason: input.reason,
      }),
    { onSuccess: (a) => { onReassigned?.(a); onOpenChange(false) } },
  )
  if (!assignment || !newDockId) return null
  const trimmed = reason.trim()
  const valid = trimmed.length >= 8
  const submit = async () => {
    if (!assignment) return
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const result = await mutation.mutate({
        assignmentId: assignment.id,
        newDockId,
        reason: trimmed,
      })
      if (result) onReassigned?.(result)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Reasignar muelle"
      description="La reasignación quedará registrada en el historial. Si la descarga ya inició, requerirá capabilities reforzadas."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={submit}
            disabled={!canReassign || !valid}
            isLoading={mutation.isPending || guard.isPending}
          >
            Reasignar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>
          Muelle anterior:{' '}
          <span className="font-mono font-bold text-slate-800">
            {assignment.previous_dock_code ?? assignment.dock_code}
          </span>{' '}
          — {assignment.dock_name}
        </p>
        <p>
          Muelle nuevo: <span className="font-mono font-bold text-slate-800">{newDockId}</span>
        </p>
        <p>
          Vehículo: <span className="font-mono text-slate-800">{assignment.vehicle?.plate ?? '—'}</span> (
          {assignment.cpv_code ?? '—'})
        </p>
        <p>
          Estado actual: <span className="font-mono text-slate-800">{assignment.status}</span>
        </p>
        {assignment.was_reassigned && (
          <p className="rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-[11px] text-amber-700">
            Esta asignación ya fue reasignada anteriormente.
          </p>
        )}
        <div className="space-y-1">
          <label className="block text-[11px] font-semibold text-slate-600" htmlFor="reassign-reason">
            Motivo de reasignación
          </label>
          <textarea
            id="reassign-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={3}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder="Detalla por qué se reasigna (mínimo 8 caracteres)"
          />
          {touched && !valid && (
            <p className="text-[11px] text-rose-600" role="alert">Motivo requerido.</p>
          )}
        </div>
        {guard.stepUpRequired && (
          <p className="rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-[11px] text-amber-700">
            Step-up requerido por el servidor.
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
        {!canReassign && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
            No tienes capability para reasignar.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function compatibleSummary(items: DockCompatibilityResult[]): string {
  return items
    .map((c) => `${c.dock_code} (${compatibilityLabel(c.compatibility_status)})`)
    .join(', ')
}
