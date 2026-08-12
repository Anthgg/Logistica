import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { useSensitiveActionGuard } from '../../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { compatibilityLabel } from '../../utils/format'
import type {
  DockAssignmentPlan,
  DockCompatibilityResult,
  InboundDockAssignment,
  InboundDockQueueEntry,
} from '../../types/inbound-docks'

export function OverrideDockCompatibilityDialog({
  open,
  entry,
  plan,
  result,
  onOpenChange,
  onExecuted,
}: {
  open: boolean
  entry: InboundDockQueueEntry | null
  plan: DockAssignmentPlan | null
  result: DockCompatibilityResult | null
  onOpenChange: (open: boolean) => void
  onExecuted?: (assignment: InboundDockAssignment) => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canAssign = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.assign)
  const guard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.inboundDocks.assign,
  })
  const [reason, setReason] = useState('')
  const [evidence, setEvidence] = useState('')
  const [conditions, setConditions] = useState('')
  const [touched, setTouched] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setReason('')
      setEvidence('')
      setConditions('')
      setTouched(false)
      setErrorMessage(null)
    }
  }, [open])
  const mutation = useMutation<{ planId: string; dockId: string; reason: string; evidence: string; conditions: string }, InboundDockAssignment>(
    async (input) =>
      dockAssignmentsApi.executePlan({
        plan_id: input.planId,
        dock_id: input.dockId,
        reason: input.reason,
        override_incompatibility: true,
        override_reason: input.reason,
        override_evidence_file_id: input.evidence || null,
        override_conditions: input.conditions || null,
      }),
    { onSuccess: (a) => { onExecuted?.(a); onOpenChange(false) } },
  )
  if (!entry || !plan || !result) return null
  const valid = reason.trim().length >= 8
  const submit = async () => {
    setTouched(true)
    if (!valid) return
    setErrorMessage(null)
    const ok = await guard.run(async () => {
      const r = await mutation.mutate({
        planId: plan.id,
        dockId: result.dock_id,
        reason: reason.trim(),
        evidence: evidence.trim(),
        conditions: conditions.trim(),
      })
      if (r) onExecuted?.(r)
    })
    if (!ok && guard.errorMessage) setErrorMessage(guard.errorMessage)
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Asignación incompatible — override"
      description="La asignación quedará registrada como excepción. Requiere capability y step-up CRITICAL."
      size="lg"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="button" variant="danger" onClick={submit} disabled={!canAssign || !valid} isLoading={mutation.isPending || guard.isPending}>
            Confirmar override
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <div className="rounded-lg border border-rose-200 bg-rose-50/40 p-3 text-rose-700">
          <p className="font-semibold">Muelle: {result.dock_code} — {result.dock_name}</p>
          <p>Regla incumplida: {compatibilityLabel(result.compatibility_status)}</p>
          {result.restriction_conflicts.length > 0 && (
            <ul className="mt-1 list-disc pl-4">
              {result.restriction_conflicts.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          {result.missing_capabilities.length > 0 && (
            <ul className="mt-1 list-disc pl-4">
              {result.missing_capabilities.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          {result.missing_information.length > 0 && (
            <ul className="mt-1 list-disc pl-4">
              {result.missing_information.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </div>
        <p>
          Alternativas compatibles disponibles:{' '}
          <span className="font-mono text-slate-800">
            {plan.compatible_docks.map((c) => c.dock_code).join(', ') || '—'}
          </span>
        </p>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="override-motive">Motivo</label>
          <textarea
            id="override-motive"
            className="w-full rounded-lg border border-rose-300 bg-white px-3 py-2 text-xs focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-300"
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            onBlur={() => setTouched(true)}
            aria-invalid={touched && !valid}
            placeholder="Detalla por qué se requiere el override (mínimo 8 caracteres)"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="override-cond">Condiciones</label>
          <textarea
            id="override-cond"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            rows={2}
            value={conditions}
            onChange={(event) => setConditions(event.target.value)}
            placeholder="Condiciones que aplican (opcional)"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="override-evid">Evidencia (ID archivo)</label>
          <input
            id="override-evid"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
          El muelle no se visualizará como compatible; quedará marcado como excepción.
        </p>
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canAssign && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para asignar.
          </p>
        )}
      </div>
    </DockModal>
  )
}
