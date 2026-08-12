import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { formatServerTime } from '../../utils/format'
import type { InboundDockAssignment } from '../../types/inbound-docks'

export function StartMovementToDockDialog({
  open,
  assignment,
  onOpenChange,
  onStarted,
}: {
  open: boolean
  assignment: InboundDockAssignment | null
  onOpenChange: (open: boolean) => void
  onStarted?: (assignment: InboundDockAssignment) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canStart = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.startMovement)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.startMovement,
  })
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) setErrorMessage(null)
  }, [open])
  const mutation = useMutation<{ id: string }, InboundDockAssignment>(
    async ({ id }) => dockAssignmentsApi.startMovement(id),
    { onSuccess: (a) => { onStarted?.(a); onOpenChange(false) } },
  )
  if (!assignment) return null
  const submit = async () => {
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({ id: assignment.id })
      if (r) onStarted?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Iniciar movimiento al muelle"
      description="Esta acción registra que el vehículo comenzó a desplazarse hacia el muelle. No inicia la descarga."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={submit}
            disabled={!canStart}
            isLoading={mutation.isPending || guard.isPending}
          >
            Iniciar movimiento
          </Button>
        </>
      }
    >
      <div className="space-y-2 text-xs">
        <p>Vehículo: <span className="font-mono text-slate-800">{assignment.vehicle?.plate ?? '—'}</span></p>
        <p>Muelle asignado: <span className="font-mono text-slate-800">{assignment.dock_code}</span> — {assignment.dock_name}</p>
        <p>Hora del servidor: <span className="font-mono text-slate-800">{formatServerTime(assignment.server_time)}</span></p>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canStart && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para iniciar movimientos.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function ConfirmDockArrivalDialog({
  open,
  assignment,
  onOpenChange,
  onConfirmed,
}: {
  open: boolean
  assignment: InboundDockAssignment | null
  onOpenChange: (open: boolean) => void
  onConfirmed?: (assignment: InboundDockAssignment) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canConfirm = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.confirmArrival)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.confirmArrival,
  })
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) setErrorMessage(null)
  }, [open])
  const mutation = useMutation<{ id: string }, InboundDockAssignment>(
    async ({ id }) => dockAssignmentsApi.confirmDockArrival(id),
    { onSuccess: (a) => { onConfirmed?.(a); onOpenChange(false) } },
  )
  if (!assignment) return null
  const submit = async () => {
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({ id: assignment.id })
      if (r) onConfirmed?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Confirmar llegada al muelle"
      description="Al confirmar se iniciará la ocupación real del muelle usando la hora del servidor."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={submit}
            disabled={!canConfirm}
            isLoading={mutation.isPending || guard.isPending}
          >
            Confirmar llegada
          </Button>
        </>
      }
    >
      <div className="space-y-2 text-xs">
        <p>Muelle: <span className="font-mono text-slate-800">{assignment.dock_code}</span> — {assignment.dock_name}</p>
        <p>Vehículo: <span className="font-mono text-slate-800">{assignment.vehicle?.plate ?? '—'}</span></p>
        <p>Estado: <span className="font-mono text-slate-800">{assignment.status}</span></p>
        <p>Hora del servidor: <span className="font-mono text-slate-800">{formatServerTime(assignment.server_time)}</span></p>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canConfirm && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para confirmar llegada.
          </p>
        )}
      </div>
    </DockModal>
  )
}
