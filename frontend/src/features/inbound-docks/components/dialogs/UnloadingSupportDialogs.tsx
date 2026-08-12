import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { unloadingOperationsApi } from '../../api/unloadingOperationsApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { formatServerTime, formatSecondsApprox, sealOpeningResultLabel } from '../../utils/format'
import type {
  InboundDockAssignment,
  UnloadingOperation,
  UnloadingSealOpening,
  UnloadingResponsibleAssignment,
  SealOpeningResult,
  UnloadingReadinessCheck,
} from '../../types/inbound-docks'

const SEAL_RESULTS: Array<{ value: SealOpeningResult; label: string }> = [
  { value: 'OPENED_NORMALLY', label: 'Abierto normalmente' },
  { value: 'OPENED_WITH_OBSERVATION', label: 'Abierto con observación' },
  { value: 'ABSENT', label: 'Ausente' },
  { value: 'DOES_NOT_MATCH', label: 'No coincide' },
  { value: 'PREVIOUSLY_BROKEN', label: 'Previamente roto' },
  { value: 'POSSIBLE_TAMPERING', label: 'Posible manipulación' },
  { value: 'NOT_APPLICABLE', label: 'No aplica' },
]

export function ReleaseWarehouseDockDialog({
  open,
  assignment,
  onOpenChange,
  onReleased,
}: {
  open: boolean
  assignment: InboundDockAssignment | null
  onOpenChange: (open: boolean) => void
  onReleased?: (assignment: InboundDockAssignment) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canRelease = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.releaseDock)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.releaseDock,
  })
  const [confirm, setConfirm] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setConfirm(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ id: string }, InboundDockAssignment>(
    async ({ id }) => dockAssignmentsApi.releaseDock(id),
    { onSuccess: (a) => { onReleased?.(a); onOpenChange(false) } },
  )
  if (!assignment) return null
  const submit = async () => {
    setErrorMessage(null)
    if (!confirm) return
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({ id: assignment.id })
      if (r) onReleased?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Liberar muelle"
      description="Esta acción registra la liberación del muelle. No registra la salida del vehículo del recinto."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="primary" onClick={submit} disabled={!canRelease || !confirm} isLoading={mutation.isPending || guard.isPending}>
            Liberar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <dl className="grid grid-cols-2 gap-1">
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Muelle</dt>
            <dd className="font-mono text-slate-800">{assignment.dock_code}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Vehículo</dt>
            <dd className="font-mono text-slate-800">{assignment.vehicle?.plate ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Hora de finalización</dt>
            <dd className="font-mono text-slate-800">{formatServerTime(assignment.released_at ?? assignment.server_time)}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Estado</dt>
            <dd className="font-mono text-slate-800">{assignment.status}</dd>
          </div>
        </dl>
        <label className="flex items-center gap-2 text-[12px] font-semibold text-slate-700">
          <input
            type="checkbox"
            checked={confirm}
            onChange={(event) => setConfirm(event.target.checked)}
            className="h-3.5 w-3.5"
          />
          Confirmo la liberación del muelle.
        </label>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canRelease && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para liberar muelles.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function RecordUnloadingSealOpeningDialog({
  open,
  operation,
  existing,
  onOpenChange,
  onRecorded,
}: {
  open: boolean
  operation: UnloadingOperation | null
  existing: UnloadingSealOpening | null
  onOpenChange: (open: boolean) => void
  onRecorded?: (opening: UnloadingSealOpening) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canRecord = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.recordSealOpening)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.recordSealOpening,
  })
  const [observed, setObserved] = useState('')
  const [result, setResult] = useState<SealOpeningResult>('OPENED_NORMALLY')
  const [observation, setObservation] = useState('')
  const [witness, setWitness] = useState('')
  const [photoBefore, setPhotoBefore] = useState('')
  const [photoAfter, setPhotoAfter] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open && operation) {
      setObserved('')
      setResult('OPENED_NORMALLY')
      setObservation('')
      setWitness('')
      setPhotoBefore('')
      setPhotoAfter('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open, operation])
  const mutation = useMutation<Parameters<typeof unloadingOperationsApi.recordSealOpening>[1], UnloadingSealOpening>(
    async (data) => unloadingOperationsApi.recordSealOpening(operation!.id, data),
    { onSuccess: (o) => { onRecorded?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const anomaly = result !== 'OPENED_NORMALLY' && result !== 'NOT_APPLICABLE'
  const valid = observation.trim().length >= 4 || result === 'OPENED_NORMALLY' || result === 'NOT_APPLICABLE'
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({
        observed_seal_number: observed.trim() || null,
        result,
        observation: observation.trim() || null,
        witness_user_id: witness.trim() || null,
        photo_before_file_id: photoBefore.trim() || null,
        photo_after_file_id: photoAfter.trim() || null,
      })
      if (r) onRecorded?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Registrar apertura de precinto"
      description="No se envía opened_at. La hora la asigna el servidor."
      size="lg"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant={anomaly ? 'danger' : 'primary'} onClick={submit} disabled={!canRecord} isLoading={mutation.isPending || guard.isPending}>
            Registrar
          </Button>
        </>
      }
    >
      {existing && (
        <p className="mb-2 rounded-lg border border-slate-200 bg-slate-50/40 p-2 text-[11px] text-slate-600">
          Apertura existente: {sealOpeningResultLabel(existing.result)} · Observado: {existing.observed_seal_number ?? '—'}
        </p>
      )}
      <div className="space-y-3 text-xs">
        <p>Precinto esperado: <span className="font-mono text-slate-800">—</span></p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="seal-observed">Precinto observado</label>
          <input
            id="seal-observed"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={observed}
            onChange={(event) => setObserved(event.target.value)}
            placeholder="Número observado en garita"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600">Resultado</label>
          <select
            value={result}
            onChange={(event) => setResult(event.target.value as SealOpeningResult)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
          >
            {SEAL_RESULTS.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        {anomaly && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
            Resultado con anomalía. Se exigirá evidencia, comentario y puede bloquear el inicio.
          </p>
        )}
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="seal-observation">Observación</label>
          <textarea
            id="seal-observation"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={observation}
            onChange={(event) => setObservation(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder="Detalle de la apertura"
          />
          {touched && !valid && <p className="mt-1 text-[11px] text-rose-600" role="alert">Detalla la observación para registrar el precinto.</p>}
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="seal-witness">Testigo (ID usuario)</label>
            <input
              id="seal-witness"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={witness}
              onChange={(event) => setWitness(event.target.value)}
              placeholder="Opcional"
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="seal-photo-before">Foto previa (ID archivo)</label>
            <input
              id="seal-photo-before"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={photoBefore}
              onChange={(event) => setPhotoBefore(event.target.value)}
              placeholder="Opcional"
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="seal-photo-after">Foto posterior (ID archivo)</label>
          <input
            id="seal-photo-after"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={photoAfter}
            onChange={(event) => setPhotoAfter(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canRecord && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para registrar apertura de precinto.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function AssignUnloadingResponsibleDialog({
  open,
  operation,
  responsibilityType,
  onOpenChange,
  onAssigned,
}: {
  open: boolean
  operation: UnloadingOperation | null
  responsibilityType: string
  onOpenChange: (open: boolean) => void
  onAssigned?: (responsible: UnloadingResponsibleAssignment) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageResponsibles)
  const [responsibility, setResponsibility] = useState(responsibilityType)
  const [userId, setUserId] = useState('')
  const [teamId, setTeamId] = useState('')
  const [contractorId, setContractorId] = useState('')
  const [validUntil, setValidUntil] = useState('')
  const [comment, setComment] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setResponsibility(responsibilityType)
      setUserId('')
      setTeamId('')
      setContractorId('')
      setValidUntil('')
      setComment('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open, responsibilityType])
  const mutation = useMutation<Parameters<typeof unloadingOperationsApi.assignResponsible>[1], UnloadingResponsibleAssignment>(
    async (data) => unloadingOperationsApi.assignResponsible(operation!.id, data),
    { onSuccess: (o) => { onAssigned?.(o); onOpenChange(false) } },
  )
  if (!operation) return null
  const valid = (userId.trim() || teamId.trim() || contractorId.trim()) && responsibility.trim().length >= 2
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const r = await mutation.mutate({
      responsibility_type: responsibility.trim(),
      user_id: userId.trim() || null,
      team_id: teamId.trim() || null,
      contractor_id: contractorId.trim() || null,
      valid_until: validUntil.trim() || null,
      comment: comment.trim() || null,
    })
    if (r) onAssigned?.(r)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Asignar responsable"
      description="Solo se permiten IDs de usuarios, equipos o contratistas registrados en el backend."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="primary" onClick={submit} disabled={!canManage || !valid} isLoading={mutation.isPending}>
            Asignar
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Operación: <span className="font-mono text-slate-800">{operation.id}</span></p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resp-type">Tipo de responsabilidad</label>
          <input
            id="resp-type"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={responsibility}
            onChange={(event) => setResponsibility(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resp-user">ID de usuario</label>
          <input
            id="resp-user"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resp-team">ID de equipo</label>
          <input
            id="resp-team"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={teamId}
            onChange={(event) => setTeamId(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resp-contractor">ID de contratista</label>
          <input
            id="resp-contractor"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={contractorId}
            onChange={(event) => setContractorId(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resp-valid">Vigencia (ISO opcional)</label>
          <input
            id="resp-valid"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={validUntil}
            onChange={(event) => setValidUntil(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="resp-comment">Comentario</label>
          <textarea
            id="resp-comment"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
          />
        </div>
        {touched && !valid && <p className="text-[11px] text-rose-600" role="alert">Selecciona un usuario, equipo o contratista y define el tipo de responsabilidad.</p>}
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canManage && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para asignar responsables.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function RequestUnloadingReadinessOverrideDialog({
  open,
  operation,
  check,
  onOpenChange,
  onRequested,
}: {
  open: boolean
  operation: UnloadingOperation | null
  check: UnloadingReadinessCheck | null
  onOpenChange: (open: boolean) => void
  onRequested?: (check: UnloadingReadinessCheck) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageReadiness)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.manageReadiness,
  })
  const [reason, setReason] = useState('')
  const [conditions, setConditions] = useState('')
  const [evidence, setEvidence] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setReason('')
      setConditions('')
      setEvidence('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ checkId: string; reason: string; conditions: string; evidence: string }, UnloadingReadinessCheck>(
    async (input) => unloadingOperationsApi.requestReadinessOverride(operation!.id, {
      check_id: input.checkId,
      reason: input.reason,
      conditions: input.conditions || null,
      evidence_file_id: input.evidence || null,
    }),
    { onSuccess: (c) => { onRequested?.(c); onOpenChange(false) } },
  )
  if (!operation || !check) return null
  const valid = reason.trim().length >= 8
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({
        checkId: check.id,
        reason: reason.trim(),
        conditions: conditions.trim(),
        evidence: evidence.trim(),
      })
      if (r) onRequested?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Solicitar override de readiness"
      description="El resultado FAIL del check no se modifica. La aprobación requiere capability y step-up."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="danger" onClick={submit} disabled={!canManage || !valid} isLoading={mutation.isPending || guard.isPending}>
            Solicitar override
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Check: <span className="font-mono text-slate-800">{check.code}</span> — {check.name}</p>
        <p>Resultado actual: <span className="font-mono text-slate-800">{check.result ?? '—'}</span></p>
        <p>Override previo: <span className="font-mono text-slate-800">{check.override_requested ? 'Solicitado' : 'No solicitado'}</span></p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="override-reason">Motivo</label>
          <textarea
            id="override-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder="Detalla por qué se solicita el override (mínimo 8 caracteres)"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="override-conditions">Condiciones</label>
          <textarea
            id="override-conditions"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={conditions}
            onChange={(event) => setConditions(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="override-evidence">Evidencia (ID archivo)</label>
          <input
            id="override-evidence"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
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

export function ReviewUnloadingReadinessOverrideDialog({
  open,
  operation,
  check,
  approve,
  onOpenChange,
  onReviewed,
}: {
  open: boolean
  operation: UnloadingOperation | null
  check: UnloadingReadinessCheck | null
  approve: boolean
  onOpenChange: (open: boolean) => void
  onReviewed?: (check: UnloadingReadinessCheck) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageReadiness)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.manageReadiness,
  })
  const [comment, setComment] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setComment('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ checkId: string; approved: boolean; comment: string }, UnloadingReadinessCheck>(
    async (input) => unloadingOperationsApi.reviewReadinessOverride(operation!.id, input.checkId, input.approved, input.comment || null),
    { onSuccess: (c) => { onReviewed?.(c); onOpenChange(false) } },
  )
  if (!operation || !check) return null
  const valid = approve ? comment.trim().length >= 4 : true
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({ checkId: check.id, approved: approve, comment: comment.trim() })
      if (r) onReviewed?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title={approve ? 'Aprobar override de readiness' : 'Rechazar override de readiness'}
      description="El resultado FAIL del check no se modifica."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant={approve ? 'primary' : 'danger'} onClick={submit} disabled={!canManage || !valid} isLoading={mutation.isPending || guard.isPending}>
            {approve ? 'Aprobar' : 'Rechazar'}
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <p>Check: <span className="font-mono text-slate-800">{check.code}</span> — {check.name}</p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="review-comment">Comentario</label>
          <textarea
            id="review-comment"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder={approve ? 'Detalla la aprobación' : 'Motivo del rechazo'}
          />
          {touched && !valid && <p className="mt-1 text-[11px] text-rose-600" role="alert">Detalla la decisión.</p>}
        </div>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canManage && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para revisar overrides.
          </p>
        )}
      </div>
    </DockModal>
  )
}

export function UnloadingPauseBanner({
  pause,
  canResume,
  canAbort,
  onResume,
  onAbort,
}: {
  pause: NonNullable<UnloadingOperation['active_pause']>
  canResume: boolean
  canAbort: boolean
  onResume: () => void
  onAbort: () => void
}) {
  const waitingSeconds = Math.max(
    0,
    pause.duration_seconds ??
      (pause.started_at ? Math.floor((Date.now() - new Date(pause.started_at).getTime()) / 1000) : 0),
  )
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/40 p-3 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-bold text-amber-700">Descarga en pausa</p>
          <p className="text-[11px] text-amber-700">
            Motivo: {pause.reason_label} · Severidad: {pause.severity} · Inicio oficial:{' '}
            {formatServerTime(pause.started_at)}
          </p>
          <p className="text-[11px] text-amber-700">
            Tiempo transcurrido aproximado: {formatSecondsApprox(waitingSeconds)}
          </p>
          {pause.evidence_file_id && (
            <p className="text-[11px] text-amber-700">Evidencia: {pause.evidence_file_id}</p>
          )}
          {pause.responsible_informed && (
            <p className="text-[11px] text-amber-700">Informado: {pause.responsible_informed.display_name}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {canResume && (
            <button
              type="button"
              onClick={onResume}
              className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-[#173a55]"
            >
              Reanudar
            </button>
          )}
          {canAbort && (
            <button
              type="button"
              onClick={onAbort}
              className="rounded-lg bg-rose-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-rose-700"
            >
              Abortar
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
