import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows } from './ui/Primitives'
import { checkResultLabel, readinessStatusLabel } from '../utils/format'
import { UpdateUnloadingReadinessCheckDialog } from './dialogs/OperationalDialogs'
import { RequestUnloadingReadinessOverrideDialog, ReviewUnloadingReadinessOverrideDialog } from './dialogs/UnloadingSupportDialogs'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  UnloadingOperation,
  UnloadingReadinessCheck,
} from '../types/inbound-docks'

export function UnloadingReadinessChecklist({
  operation,
  checks,
  loading,
  error,
  onChanged,
}: {
  operation: UnloadingOperation | null
  checks: UnloadingReadinessCheck[] | undefined
  loading: boolean
  error: string | null
  onChanged?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageReadiness)
  const [editing, setEditing] = useState<UnloadingReadinessCheck | null>(null)
  const [overrideRequest, setOverrideRequest] = useState<UnloadingReadinessCheck | null>(null)
  const [overrideReview, setOverrideReview] = useState<UnloadingReadinessCheck | null>(null)
  const [reviewApproved, setReviewApproved] = useState(true)
  if (loading) {
    return (
      <SectionPanel
        title="Readiness previo"
        description="Cada check proviene del backend. El resultado final lo calcula el servidor."
      >
        <SkeletonRows rows={4} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Readiness previo" description="Sin datos del servidor.">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!operation) {
    return (
      <SectionPanel title="Readiness previo" description="Operación no cargada.">
        <EmptyPanel title="Sin operación" />
      </SectionPanel>
    )
  }
  if (!checks?.length) {
    return (
      <SectionPanel
        title="Readiness previo"
        description="No hay checks configurados para esta operación."
      >
        <EmptyPanel title="Sin checks" description="El backend aún no configuró los checks de readiness." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Readiness previo"
      description={`Estado final: ${readinessStatusLabel(operation.readiness_status)}`}
    >
      <ul className="space-y-2">
        {checks.map((check) => {
          const isPending = !check.result
          const isFail = check.result === 'FAIL'
          const isOverride = check.override_requested
          return (
            <li
              key={check.id}
              className="flex flex-col gap-1 rounded-lg border border-slate-200 bg-white p-3 text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    {check.name}
                    {check.is_required && <span className="ml-1 text-[10px] text-rose-700">requerido</span>}
                  </p>
                  <p className="text-[11px] text-slate-500">{check.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusPill
                    tone={
                      check.result === 'PASS' || check.result === 'NOT_APPLICABLE'
                        ? 'success'
                        : check.result === 'PASS_WITH_OBSERVATION'
                          ? 'info'
                          : isFail
                            ? 'danger'
                            : isPending
                              ? 'muted'
                              : 'warning'
                    }
                  >
                    {checkResultLabel(check.result)}
                  </StatusPill>
                  {isOverride && (
                    <StatusPill tone={check.override_approved ? 'success' : 'warning'}>
                      {check.override_approved ? 'Override aprobado' : 'Override pendiente'}
                    </StatusPill>
                  )}
                </div>
              </div>
              {check.observation && (
                <p className="text-[11px] text-slate-600">Observación: {check.observation}</p>
              )}
              {check.performed_by && (
                <p className="text-[10px] text-slate-500">
                  Por: {check.performed_by.display_name} · {check.performed_at ?? '—'}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                {canManage && !check.override_approved && (
                  <Button
                    size="small"
                    variant="secondary"
                    onClick={() => setEditing(check)}
                  >
                    Actualizar
                  </Button>
                )}
                {canManage && isFail && !check.override_requested && (
                  <Button
                    size="small"
                    variant="danger"
                    onClick={() => setOverrideRequest(check)}
                  >
                    Solicitar override
                  </Button>
                )}
                {canManage && check.override_requested && check.override_approved == null && (
                  <>
                    <Button
                      size="small"
                      variant="primary"
                      onClick={() => {
                        setOverrideReview(check)
                        setReviewApproved(true)
                      }}
                    >
                      Aprobar override
                    </Button>
                    <Button
                      size="small"
                      variant="secondary"
                      onClick={() => {
                        setOverrideReview(check)
                        setReviewApproved(false)
                      }}
                    >
                      Rechazar
                    </Button>
                  </>
                )}
              </div>
            </li>
          )
        })}
      </ul>
      <UpdateUnloadingReadinessCheckDialog
        open={Boolean(editing)}
        operation={operation}
        check={editing}
        onOpenChange={(o) => { if (!o) setEditing(null) }}
        onUpdated={() => { onChanged?.() }}
      />
      <RequestUnloadingReadinessOverrideDialog
        open={Boolean(overrideRequest)}
        operation={operation}
        check={overrideRequest}
        onOpenChange={(o) => { if (!o) setOverrideRequest(null) }}
        onRequested={() => { onChanged?.() }}
      />
      <ReviewUnloadingReadinessOverrideDialog
        open={Boolean(overrideReview)}
        operation={operation}
        check={overrideReview}
        approve={reviewApproved}
        onOpenChange={(o) => { if (!o) setOverrideReview(null) }}
        onReviewed={() => { onChanged?.() }}
      />
    </SectionPanel>
  )
}
