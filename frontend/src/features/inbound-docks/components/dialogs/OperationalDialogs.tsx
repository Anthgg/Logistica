import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { warehouseDocksApi } from '../../api/warehouseDocksApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { formatServerTime } from '../../utils/format'
import type {
  DockEventType,
  DockOperationalTimeCorrection,
  InboundDockAssignment,
  UnloadingOperation,
  UnloadingCheckResult,
  UnloadingReadinessCheck,
} from '../../types/inbound-docks'

export function StartUnloadingDialog({
  open,
  operation,
  readinessSummary,
  onOpenChange,
  onStarted,
}: {
  open: boolean
  operation: UnloadingOperation | null
  readinessSummary?: { total: number; pending: number; failed: number; passed: number }
  onOpenChange: (open: boolean) => void
  onStarted?: (operation: UnloadingOperation) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canStart = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.startUnloading)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.startUnloading,
  })
  const [confirm, setConfirm] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setConfirm(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ id: string }, UnloadingOperation>(
    async ({ id }) => {
      const { unloadingOperationsApi } = await import('../../api/unloadingOperationsApi')
      return unloadingOperationsApi.start(id)
    },
    { onSuccess: (o) => { onStarted?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const readinessBlocks = readinessSummary ? readinessSummary.failed > 0 : false
  const submit = async () => {
    setErrorMessage(null)
    if (!confirm) return
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({ id: operation.id })
      if (r) onStarted?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Iniciar descarga"
      description="Esta acción registra el inicio físico de la descarga. No registra cantidades recibidas ni modifica inventario."
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
            disabled={!canStart || !confirm || readinessBlocks}
            isLoading={mutation.isPending || guard.isPending}
          >
            Iniciar descarga
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Esta acción registra el inicio físico de la descarga. No registra cantidades recibidas, lotes, series ni modifica inventario.</p>
        <dl className="grid grid-cols-2 gap-1">
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Muelle</dt>
            <dd className="font-mono text-slate-800">{operation.dock_code}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Vehículo</dt>
            <dd className="font-mono text-slate-800">{operation.vehicle?.plate ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Estado</dt>
            <dd className="font-mono text-slate-800">{operation.status}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Hora del servidor</dt>
            <dd className="font-mono text-slate-800">{formatServerTime(operation.server_time)}</dd>
          </div>
        </dl>
        {readinessSummary && (
          <div className="rounded-lg border border-slate-200 bg-slate-50/40 p-2 text-[11px]">
            Readiness: {readinessSummary.passed}/{readinessSummary.total} completados.{' '}
            {readinessSummary.pending > 0 && (
              <span className="text-amber-700">{readinessSummary.pending} pendientes</span>
            )}
            {readinessSummary.failed > 0 && (
              <span className="ml-2 text-rose-700">{readinessSummary.failed} con falla</span>
            )}
          </div>
        )}
        {readinessBlocks && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            Hay checks con FAIL. Resuelve o solicita override antes de iniciar.
          </p>
        )}
        <label className="flex items-center gap-2 text-[12px] font-semibold text-slate-700">
          <input
            type="checkbox"
            checked={confirm}
            onChange={(event) => setConfirm(event.target.checked)}
            className="h-3.5 w-3.5"
          />
          Confirmo el inicio físico de la descarga.
        </label>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canStart && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para iniciar descargas.
          </p>
        )}
      </div>
    </DockModal>
  )
}

const READINESS_RESULTS: Array<{ value: UnloadingCheckResult; label: string }> = [
  { value: 'PASS', label: 'Cumple' },
  { value: 'PASS_WITH_OBSERVATION', label: 'Cumple con observación' },
  { value: 'FAIL', label: 'No cumple' },
  { value: 'NOT_APPLICABLE', label: 'No aplica' },
]

export function UpdateUnloadingReadinessCheckDialog({
  open,
  operation,
  check,
  onOpenChange,
  onUpdated,
}: {
  open: boolean
  operation: UnloadingOperation | null
  check: UnloadingReadinessCheck | null
  onOpenChange: (open: boolean) => void
  onUpdated?: (check: UnloadingReadinessCheck) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageReadiness)
  const [result, setResult] = useState<UnloadingCheckResult>('PASS')
  const [observation, setObservation] = useState('')
  const [evidence, setEvidence] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open && check) {
      setResult(check.result ?? 'PASS')
      setObservation(check.observation ?? '')
      setEvidence(check.evidence_file_id ?? '')
      setErrorMessage(null)
    }
  }, [open, check])
  const mutation = useMutation<{ checkId: string; result: UnloadingCheckResult; observation: string; evidence: string }, UnloadingReadinessCheck>(
    async (input) => {
      const { unloadingOperationsApi } = await import('../../api/unloadingOperationsApi')
      return unloadingOperationsApi.updateReadinessCheck(
        operation!.id,
        input.checkId,
        input.result as 'PASS' | 'FAIL' | 'PASS_WITH_OBSERVATION' | 'NOT_APPLICABLE',
        input.observation || null,
        input.evidence || null,
      )
    },
    { onSuccess: (c) => { onUpdated?.(c); onOpenChange(false) } },
  )
  if (!operation || !check) return null
  const isFail = result === 'FAIL'
  const requiresObservation = result === 'PASS_WITH_OBSERVATION' || result === 'FAIL'
  const observationValid = !requiresObservation || observation.trim().length >= 4
  const submit = async () => {
    setErrorMessage(null)
    if (!observationValid) return
    const r = await mutation.mutate({
      checkId: check.id,
      result,
      observation: observation.trim(),
      evidence: evidence.trim(),
    })
    if (r) onUpdated?.(r)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Actualizar check de readiness"
      description="El estado final del readiness lo calcula el servidor."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant={isFail ? 'danger' : 'primary'} onClick={submit} disabled={!canManage || !observationValid} isLoading={mutation.isPending}>
            Guardar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Check: <span className="font-mono text-slate-800">{check.code}</span> — {check.name}</p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600">Resultado</label>
          <select
            value={result}
            onChange={(event) => setResult(event.target.value as UnloadingCheckResult)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
          >
            {READINESS_RESULTS.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="check-observation">Observación</label>
          <textarea
            id="check-observation"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={observation}
            onChange={(event) => setObservation(event.target.value)}
            placeholder={requiresObservation ? 'Detalla la observación' : 'Opcional'}
            aria-invalid={requiresObservation && observation.trim().length < 4}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="check-evidence">Evidencia (ID archivo)</label>
          <input
            id="check-evidence"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        {isFail && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            Si el check es bloqueante, el inicio quedará impedido hasta aprobar un override.
          </p>
        )}
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canManage && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para gestionar readiness.
          </p>
        )}
      </div>
    </DockModal>
  )
}

const DOCK_EVENT_TYPES: Array<{ value: DockEventType; label: string }> = [
  { value: 'GATE_CLEARANCE', label: 'Autorización de garita' },
  { value: 'QUEUE_ENTRY', label: 'Entrada a cola' },
  { value: 'PRIORITY_CHANGED', label: 'Cambio de prioridad' },
  { value: 'PLAN_GENERATED', label: 'Plan generado' },
  { value: 'DOCK_ASSIGNED', label: 'Muelle asignado' },
  { value: 'MOVEMENT_STARTED', label: 'Movimiento iniciado' },
  { value: 'DOCK_ARRIVAL', label: 'Llegada al muelle' },
  { value: 'READINESS_UPDATED', label: 'Readiness actualizado' },
  { value: 'RESPONSIBLE_ASSIGNED', label: 'Responsable asignado' },
  { value: 'SEAL_OPENING_RECORDED', label: 'Apertura de precinto' },
  { value: 'UNLOADING_STARTED', label: 'Descarga iniciada' },
  { value: 'UNLOADING_PAUSED', label: 'Pausa' },
  { value: 'UNLOADING_RESUMED', label: 'Reanudación' },
  { value: 'UNLOADING_ABORTED', label: 'Aborto' },
  { value: 'UNLOADING_COMPLETED', label: 'Finalización' },
  { value: 'DOCK_RELEASED', label: 'Liberación' },
  { value: 'DOCK_REASSIGNED', label: 'Reasignación' },
  { value: 'TIME_CORRECTION_REQUESTED', label: 'Corrección solicitada' },
  { value: 'TIME_CORRECTION_APPROVED', label: 'Corrección aprobada' },
  { value: 'TIME_CORRECTION_REJECTED', label: 'Corrección rechazada' },
  { value: 'INTEGRITY_FAILED', label: 'Integridad fallida' },
]

export function RequestDockOperationalTimeCorrectionDialog({
  open,
  assignment,
  onOpenChange,
  onRequested,
}: {
  open: boolean
  assignment: InboundDockAssignment | null
  onOpenChange: (open: boolean) => void
  onRequested?: (correction: DockOperationalTimeCorrection) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.requestTimeCorrection)
  const [eventType, setEventType] = useState<DockEventType>('GATE_CLEARANCE')
  const [original, setOriginal] = useState('')
  const [proposed, setProposed] = useState('')
  const [timezone, setTimezone] = useState('America/Lima')
  const [reason, setReason] = useState('')
  const [evidence, setEvidence] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setEventType('GATE_CLEARANCE')
      setOriginal('')
      setProposed('')
      setTimezone('America/Lima')
      setReason('')
      setEvidence('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<Parameters<typeof dockAssignmentsApi.requestTimeCorrection>[1], DockOperationalTimeCorrection>(
    async (data) => dockAssignmentsApi.requestTimeCorrection(assignment!.id, data),
    { onSuccess: (c) => { onRequested?.(c); onOpenChange(false) } },
  )
  if (!assignment) return null
  const valid = reason.trim().length >= 8
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const r = await mutation.mutate({
      event_type: eventType,
      proposed_time: proposed.trim(),
      timezone: timezone.trim() || 'UTC',
      reason: reason.trim(),
      evidence_file_id: evidence.trim() || null,
    })
    if (r) onRequested?.(r)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Solicitar corrección de tiempo"
      description="No se edita la hora original. La corrección requiere aprobación."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="primary" onClick={submit} disabled={!canRequest || !valid} isLoading={mutation.isPending}>
            Solicitar corrección
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600">Evento</label>
          <select
            value={eventType}
            onChange={(event) => setEventType(event.target.value as DockEventType)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
          >
            {DOCK_EVENT_TYPES.map((e) => (
              <option key={e.value} value={e.value}>{e.label}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="correction-original">Hora original (solo lectura)</label>
            <input
              id="correction-original"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600"
              value={original}
              onChange={(event) => setOriginal(event.target.value)}
              readOnly
              placeholder="(el backend la calcula)"
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="correction-proposed">Hora propuesta</label>
            <input
              id="correction-proposed"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={proposed}
              onChange={(event) => setProposed(event.target.value)}
              placeholder="ISO 8601"
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="correction-tz">Zona horaria</label>
          <input
            id="correction-tz"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
            placeholder="America/Lima"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="correction-reason">Motivo</label>
          <textarea
            id="correction-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder="Detalla el motivo de la corrección (mínimo 8 caracteres)"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="correction-evidence">Evidencia (ID archivo)</label>
          <input
            id="correction-evidence"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
          La hora original no se edita. El impacto se estimará al aprobar la corrección.
        </p>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canRequest && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para solicitar correcciones.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function CreateWarehouseDockBlackoutDialog({
  open,
  dockId,
  dockCode,
  onOpenChange,
  onCreated,
}: {
  open: boolean
  dockId: string | null
  dockCode: string
  onOpenChange: (open: boolean) => void
  onCreated?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageBlackouts)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.manageBlackouts,
  })
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [reason, setReason] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setStartsAt('')
      setEndsAt('')
      setReason('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<Parameters<typeof warehouseDocksApi.createBlackout>[0], unknown>(
    async (data) => warehouseDocksApi.createBlackout(data),
    { onSuccess: () => { onCreated?.(); onOpenChange(false) } },
  )
  if (!dockId) return null
  const valid = startsAt && endsAt && reason.trim().length >= 4
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      await mutation.mutate({
        dock_id: dockId,
        starts_at: startsAt,
        ends_at: endsAt,
        reason: reason.trim(),
      })
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title={`Crear blackout (${dockCode})`}
      description="Un blackout con operación activa puede requerir step-up."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="danger" onClick={submit} disabled={!canCreate || !valid} isLoading={mutation.isPending || guard.isPending}>
            Crear blackout
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="blackout-start">Inicio (ISO)</label>
            <input
              id="blackout-start"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={startsAt}
              onChange={(event) => setStartsAt(event.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="blackout-end">Fin (ISO)</label>
            <input
              id="blackout-end"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={endsAt}
              onChange={(event) => setEndsAt(event.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="blackout-reason">Motivo</label>
          <textarea
            id="blackout-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && reason.trim().length < 4}
            placeholder="Detalla el motivo (mínimo 4 caracteres)"
          />
        </div>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canCreate && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para crear blackouts.
          </p>
        )}
      </div>
    </DockModal>
  )
}
