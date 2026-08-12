import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import {
  compatibilityLabel,
  formatServerTime,
  priorityLabel,
} from '../../utils/format'
import type {
  DockAssignmentPlan,
  InboundDockAssignment,
  InboundDockQueueEntry,
} from '../../types/inbound-docks'

export function AssignInboundDockDialog({
  open,
  entry,
  plan,
  dockId,
  onOpenChange,
  onAssigned,
}: {
  open: boolean
  entry: InboundDockQueueEntry | null
  plan: DockAssignmentPlan | null
  dockId: string | null
  onOpenChange: (open: boolean) => void
  onAssigned?: (assignment: InboundDockAssignment) => void
}) {
  const { hasPermission, requiresStepUp } = useLogisticsPermissions()
  const canAssign = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.assign)
  const stepUpRequiredByCapability = requiresStepUp(LOGISTICS_PERMISSIONS.inboundDocks.assign)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.assign,
  })
  const [reason, setReason] = useState('')
  const [overrideIncompatibility, setOverrideIncompatibility] = useState(false)
  const [overrideReason, setOverrideReason] = useState('')
  const [overrideEvidence, setOverrideEvidence] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setReason('')
      setOverrideIncompatibility(false)
      setOverrideReason('')
      setOverrideEvidence('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{
    planId: string
    dockId: string
    reason: string
    overrideIncompatibility: boolean
    overrideReason: string
    overrideEvidence: string
  }, InboundDockAssignment>(
    async (input) =>
      dockAssignmentsApi.executePlan({
        plan_id: input.planId,
        dock_id: input.dockId,
        reason: input.reason || null,
        override_incompatibility: input.overrideIncompatibility,
        override_reason: input.overrideReason || null,
        override_evidence_file_id: input.overrideEvidence || null,
        override_conditions: null,
      }),
    { onSuccess: (a) => { onAssigned?.(a); onOpenChange(false) } },
  )
  if (!entry || !plan || !dockId) return null
  const result =
    plan.compatible_docks.find((c) => c.dock_id === dockId) ??
    plan.incompatible_docks.find((c) => c.dock_id === dockId)
  const incompatible = result ? plan.incompatible_docks.some((c) => c.dock_id === dockId) : false
  const isOverride = overrideIncompatibility
  const trimmedReason = reason.trim()
  const trimmedOverride = overrideReason.trim()
  const overrideValid = !isOverride || trimmedOverride.length >= 8
  const reasonValid = trimmedReason.length >= 4
  const valid = reasonValid && overrideValid
  const submit = async () => {
    if (!plan || !dockId) return
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const resultAssignment = await mutation.mutate({
        planId: plan.id,
        dockId,
        reason: trimmedReason,
        overrideIncompatibility: isOverride,
        overrideReason: trimmedOverride,
        overrideEvidence: overrideEvidence.trim(),
      })
      if (resultAssignment) onAssigned?.(resultAssignment)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Asignar muelle"
      description="La asignación se ejecuta con la hora del servidor. No se enviarán responsables ni timestamps autoritativos."
      size="lg"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant={isOverride ? 'danger' : 'primary'}
            onClick={submit}
            disabled={!canAssign || !valid}
            isLoading={mutation.isPending || guard.isPending}
          >
            {isOverride ? 'Asignar con override' : 'Asignar muelle'}
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <dl className="grid grid-cols-2 gap-1 sm:grid-cols-3">
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">CPV</dt>
            <dd className="font-mono text-slate-800">{entry.cpv_code ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">CIT</dt>
            <dd className="font-mono text-slate-800">{entry.cit_code ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Proveedor</dt>
            <dd className="text-slate-800">{entry.supplier_name ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Placa</dt>
            <dd className="font-mono text-slate-800">{entry.vehicle_plate ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Prioridad</dt>
            <dd className="text-slate-800">{priorityLabel(entry.priority)}</dd>
          </div>
          <div>
            <dt className="text-[10px] font-semibold uppercase text-slate-500">Hora del servidor</dt>
            <dd className="font-mono text-slate-800">{formatServerTime(entry.server_time)}</dd>
          </div>
        </dl>
        <div className="rounded-lg border border-slate-200 bg-slate-50/40 p-3">
          <h3 className="text-[11px] font-bold uppercase text-slate-500">Muelle seleccionado</h3>
          <p className="mt-1 text-sm font-semibold text-slate-800">
            {result?.dock_code} — {result?.dock_name}
          </p>
          {result && (
            <p className="mt-1 text-[11px] text-slate-600">
              Compatibilidad: {compatibilityLabel(result.compatibility_status)}
            </p>
          )}
          {result && result.warnings.length > 0 && (
            <ul className="mt-1 list-disc pl-4 text-[11px] text-amber-700">
              {result.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
          {result && result.conflicts.length > 0 && (
            <ul className="mt-1 list-disc pl-4 text-[11px] text-rose-700">
              {result.conflicts.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
        </div>
        <div className="space-y-2">
          <label className="block text-[11px] font-semibold text-slate-600" htmlFor="assign-reason">
            Motivo de asignación
          </label>
          <textarea
            id="assign-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            placeholder="Describe el motivo (mínimo 4 caracteres)"
            aria-invalid={touched && !reasonValid}
          />
          {touched && !reasonValid && (
            <p className="text-[11px] text-rose-600" role="alert">Motivo requerido.</p>
          )}
        </div>
        {incompatible && (
          <div className="space-y-2 rounded-lg border border-rose-200 bg-rose-50/40 p-3">
            <label className="flex items-center gap-2 text-[11px] font-semibold text-rose-700">
              <input
                type="checkbox"
                checked={overrideIncompatibility}
                onChange={(event) => setOverrideIncompatibility(event.target.checked)}
                className="h-3.5 w-3.5"
              />
              Asignar como excepción (override de incompatibilidad)
            </label>
            {overrideIncompatibility && (
              <>
                <p className="text-[11px] text-rose-700">
                  Esta acción requiere capability, motivo obligatorio y queda registrada como override
                  en el historial.
                </p>
                <textarea
                  className="w-full rounded-lg border border-rose-300 bg-white px-3 py-2 text-xs focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-300"
                  rows={2}
                  value={overrideReason}
                  onChange={(event) => setOverrideReason(event.target.value)}
                  placeholder="Motivo del override (mínimo 8 caracteres)"
                  aria-invalid={touched && !overrideValid}
                />
                <input
                  className="w-full rounded-lg border border-rose-300 bg-white px-3 py-2 text-xs focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-300"
                  placeholder="Evidencia (ID de archivo, opcional)"
                  value={overrideEvidence}
                  onChange={(event) => setOverrideEvidence(event.target.value)}
                />
              </>
            )}
          </div>
        )}
        {stepUpRequiredByCapability && (
          <p className="rounded-lg border border-indigo-200 bg-indigo-50/40 p-2 text-[11px] text-indigo-700">
            Esta capability puede requerir step-up al confirmar.
          </p>
        )}
        {guard.stepUpRequired && (
          <p className="rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-[11px] text-amber-700">
            Step-up requerido por el servidor. Completa el flujo reforzado.
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
        {!canAssign && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-[11px] text-rose-700">
            No tienes capability para asignar muelles.
          </p>
        )}
      </div>
    </DockModal>
  )
}
