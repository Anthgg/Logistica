import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { unloadingOperationsApi } from '../../api/unloadingOperationsApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { formatServerTime, severityLabel } from '../../utils/format'
import type { UnloadingOperation } from '../../types/inbound-docks'

const PAUSE_REASONS: Array<{ value: string; label: string }> = [
  { value: 'SAFETY', label: 'Seguridad' },
  { value: 'DOCUMENTATION', label: 'Documentación' },
  { value: 'EQUIPMENT', label: 'Equipo' },
  { value: 'PERSONNEL', label: 'Personal' },
  { value: 'DOCK_CONDITION', label: 'Condición del muelle' },
  { value: 'WEATHER', label: 'Clima' },
  { value: 'LOAD_CONDITION', label: 'Condición de carga' },
  { value: 'SEAL', label: 'Precinto' },
  { value: 'RECEIVING_SYSTEM', label: 'Sistema de recepción' },
  { value: 'BREAK', label: 'Descanso' },
  { value: 'OTHER', label: 'Otro' },
]

const SEVERITIES: Array<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'> = [
  'LOW',
  'MEDIUM',
  'HIGH',
  'CRITICAL',
]

export function PauseUnloadingDialog({
  open,
  operation,
  onOpenChange,
  onPaused,
}: {
  open: boolean
  operation: UnloadingOperation | null
  onOpenChange: (open: boolean) => void
  onPaused?: (operation: UnloadingOperation) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canPause = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.pause)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.pause,
  })
  const [reason, setReason] = useState('OTHER')
  const [severity, setSeverity] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('MEDIUM')
  const [comment, setComment] = useState('')
  const [evidence, setEvidence] = useState('')
  const [responsibleInformed, setResponsibleInformed] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setReason('OTHER')
      setSeverity('MEDIUM')
      setComment('')
      setEvidence('')
      setResponsibleInformed('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<Parameters<typeof unloadingOperationsApi.pause>[1], UnloadingOperation>(
    async (data) => unloadingOperationsApi.pause(operation!.id, data),
    { onSuccess: (o) => { onPaused?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const commentValid = comment.trim().length >= 4
  const valid = commentValid
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({
        reason,
        severity,
        comment: comment.trim(),
        evidence_file_id: evidence.trim() || null,
        responsible_informed_user_id: responsibleInformed.trim() || null,
      })
      if (r) onPaused?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Pausar descarga"
      description="No se enviarán started_at ni duración calculada."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="danger" onClick={submit} disabled={!canPause || !valid} isLoading={mutation.isPending || guard.isPending}>
            Pausar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Muelle: <span className="font-mono text-slate-800">{operation.dock_code}</span></p>
        <p>Estado: <span className="font-mono text-slate-800">{operation.status}</span></p>
        <p>Hora del servidor: <span className="font-mono text-slate-800">{formatServerTime(operation.server_time)}</span></p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600">Motivo</label>
          <select
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
          >
            {PAUSE_REASONS.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        <fieldset>
          <legend className="mb-1 text-[11px] font-semibold text-slate-600">Severidad</legend>
          <div className="flex flex-wrap gap-2">
            {SEVERITIES.map((s) => (
              <label
                key={s}
                className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold ${
                  severity === s
                    ? 'border-[#1F4E6D] bg-[#1F4E6D]/5 text-[#1F4E6D]'
                    : 'border-slate-200 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="severity"
                  value={s}
                  checked={severity === s}
                  onChange={() => setSeverity(s)}
                  className="sr-only"
                />
                {severityLabel(s)}
              </label>
            ))}
          </div>
        </fieldset>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="pause-comment">Comentario</label>
          <textarea
            id="pause-comment"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !commentValid}
            placeholder="Describe brevemente el motivo de la pausa"
          />
          {touched && !commentValid && <p className="mt-1 text-[11px] text-rose-600" role="alert">Comentario requerido.</p>}
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="pause-evidence">Evidencia (ID archivo)</label>
          <input
            id="pause-evidence"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="pause-responsible">Responsable informado (ID usuario)</label>
          <input
            id="pause-responsible"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={responsibleInformed}
            onChange={(event) => setResponsibleInformed(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canPause && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para pausar.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function ResumeUnloadingDialog({
  open,
  operation,
  onOpenChange,
  onResumed,
}: {
  open: boolean
  operation: UnloadingOperation | null
  onOpenChange: (open: boolean) => void
  onResumed?: (operation: UnloadingOperation) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canResume = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.resume)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.resume,
  })
  const [condition, setCondition] = useState('')
  const [evidence, setEvidence] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setCondition('')
      setEvidence('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ condition: string; evidence: string }, UnloadingOperation>(
    async (input) => unloadingOperationsApi.resume(operation!.id, { condition_resolved: input.condition, evidence_file_id: input.evidence || null }),
    { onSuccess: (o) => { onResumed?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const valid = condition.trim().length >= 4
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({ condition: condition.trim(), evidence: evidence.trim() })
      if (r) onResumed?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Reanudar descarga"
      description="No se enviarán ended_at ni duración calculada."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="primary" onClick={submit} disabled={!canResume || !valid} isLoading={mutation.isPending || guard.isPending}>
            Reanudar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Motivo previo: <span className="font-mono text-slate-800">{operation.active_pause?.reason_label ?? '—'}</span></p>
        <p>Severidad: <span className="font-mono text-slate-800">{operation.active_pause ? severityLabel(operation.active_pause.severity) : '—'}</span></p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resume-condition">Condición resuelta</label>
          <textarea
            id="resume-condition"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={condition}
            onChange={(event) => setCondition(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder="Describe cómo se resolvió"
          />
          {touched && !valid && <p className="mt-1 text-[11px] text-rose-600" role="alert">Detalla la condición resuelta.</p>}
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resume-evidence">Evidencia (ID archivo)</label>
          <input
            id="resume-evidence"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canResume && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para reanudar.
          </p>
        )}
      </div>
    </DockModal>
  )
}

const ABORT_CATEGORIES: Array<{ value: string; label: string }> = [
  { value: 'SAFETY', label: 'Seguridad' },
  { value: 'SEAL', label: 'Precinto' },
  { value: 'LOAD', label: 'Carga' },
  { value: 'AUTHORITY', label: 'Autoridad' },
  { value: 'OTHER', label: 'Otro' },
]
const ABORT_RISKS: Array<{ value: string; label: string }> = [
  { value: 'LOW', label: 'Bajo' },
  { value: 'MEDIUM', label: 'Medio' },
  { value: 'HIGH', label: 'Alto' },
  { value: 'CRITICAL', label: 'Crítico' },
]

export function AbortUnloadingDialog({
  open,
  operation,
  onOpenChange,
  onAborted,
}: {
  open: boolean
  operation: UnloadingOperation | null
  onOpenChange: (open: boolean) => void
  onAborted?: (operation: UnloadingOperation) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canAbort = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.abort)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.abort,
  })
  const [reason, setReason] = useState('')
  const [category, setCategory] = useState('OTHER')
  const [riskLevel, setRiskLevel] = useState('MEDIUM')
  const [evidence, setEvidence] = useState('')
  const [supervisor, setSupervisor] = useState('')
  const [nextAction, setNextAction] = useState('HOLD')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setReason('')
      setCategory('OTHER')
      setRiskLevel('MEDIUM')
      setEvidence('')
      setSupervisor('')
      setNextAction('HOLD')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<Parameters<typeof unloadingOperationsApi.abort>[1], UnloadingOperation>(
    async (data) => unloadingOperationsApi.abort(operation!.id, data),
    { onSuccess: (o) => { onAborted?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const valid = reason.trim().length >= 8 && nextAction.trim().length >= 2
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({
        reason: reason.trim(),
        category,
        risk_level: riskLevel,
        evidence_file_id: evidence.trim() || null,
        supervisor_user_id: supervisor.trim() || null,
        next_action: nextAction.trim(),
      })
      if (r) onAborted?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Abortar descarga"
      description="La operación no se marcará como completada. El muelle seguirá ocupado hasta liberación. No se registrarán cantidades. Puede requerirse incidencia o diferencia posteriormente."
      size="lg"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="danger" onClick={submit} disabled={!canAbort || !valid} isLoading={mutation.isPending || guard.isPending}>
            Abortar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>La operación no se marcará como completada. El muelle seguirá ocupado hasta liberación.</p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="abort-reason">Motivo</label>
          <textarea
            id="abort-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && reason.trim().length < 8}
            placeholder="Detalla el motivo (mínimo 8 caracteres)"
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600">Categoría</label>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            >
              {ABORT_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600">Nivel de riesgo</label>
            <select
              value={riskLevel}
              onChange={(event) => setRiskLevel(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            >
              {ABORT_RISKS.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="abort-evidence">Evidencia (ID archivo)</label>
          <input
            id="abort-evidence"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="abort-supervisor">Supervisor (ID usuario)</label>
          <input
            id="abort-supervisor"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={supervisor}
            onChange={(event) => setSupervisor(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="abort-next">Próxima acción</label>
          <input
            id="abort-next"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={nextAction}
            onChange={(event) => setNextAction(event.target.value)}
            placeholder="HOLD, ESCALATE, RELEASE, ..."
          />
        </div>
        <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
          Esta acción requiere step-up y queda registrada en el historial.
        </p>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canAbort && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para abortar.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function CompleteUnloadingDialog({
  open,
  operation,
  completionCheckSummary,
  onOpenChange,
  onCompleted,
}: {
  open: boolean
  operation: UnloadingOperation | null
  completionCheckSummary?: { total: number; pending: number; failed: number; passed: number }
  onOpenChange: (open: boolean) => void
  onCompleted?: (operation: UnloadingOperation) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canComplete = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.complete)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.complete,
  })
  const [confirm, setConfirm] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setConfirm(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<unknown, UnloadingOperation>(
    async () => unloadingOperationsApi.complete(operation!.id),
    { onSuccess: (o) => { onCompleted?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const submit = async () => {
    setErrorMessage(null)
    if (!confirm) return
    const ok = await guard.run(async () => {
      const r = await mutation.mutate(undefined)
      if (r) onCompleted?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Finalizar descarga"
      description="Finalizar indica que terminó la actividad física de descarga. La recepción y validación de cantidades se realizará en la Fase 039."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="primary" onClick={submit} disabled={!canComplete || !confirm} isLoading={mutation.isPending || guard.isPending}>
            Finalizar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Esta acción registra el fin de la actividad física de descarga. No incluye cantidades recibidas, lotes, series ni vencimientos.</p>
        <dl className="grid grid-cols-2 gap-1">
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Muelle</dt>
            <dd className="font-mono text-slate-800">{operation.dock_code}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Estado</dt>
            <dd className="font-mono text-slate-800">{operation.status}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Inicio</dt>
            <dd className="font-mono text-slate-800">{formatServerTime(operation.started_at_server ?? operation.started_at)}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Hora del servidor</dt>
            <dd className="font-mono text-slate-800">{formatServerTime(operation.server_time)}</dd>
          </div>
        </dl>
        {completionCheckSummary && (
          <div className="rounded-lg border border-slate-200 bg-slate-50/40 p-2 text-[11px]">
            Checklist de cierre: {completionCheckSummary.passed}/{completionCheckSummary.total} completados.
            {completionCheckSummary.pending > 0 && (
              <span className="ml-1 text-amber-700">
                {completionCheckSummary.pending} pendientes
              </span>
            )}
            {completionCheckSummary.failed > 0 && (
              <span className="ml-1 text-rose-700">
                {completionCheckSummary.failed} con falla
              </span>
            )}
          </div>
        )}
        <label className="flex items-center gap-2 text-[12px] font-semibold text-slate-700">
          <input
            type="checkbox"
            checked={confirm}
            onChange={(event) => setConfirm(event.target.checked)}
            className="h-3.5 w-3.5"
          />
          Confirmo que la actividad física de descarga ha terminado.
        </label>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canComplete && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para finalizar.
          </p>
        )}
      </div>
    </DockModal>
  )
}
