import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows } from './ui/Primitives'
import { checkResultLabel } from '../utils/format'
import { UpdateUnloadingReadinessCheckDialog } from './dialogs/OperationalDialogs'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  UnloadingCompletionCheck,
  UnloadingOperation,
} from '../types/inbound-docks'

export function UnloadingCompletionChecklist({
  operation,
  checks,
  loading,
  error,
  onChanged,
}: {
  operation: UnloadingOperation | null
  checks: UnloadingCompletionCheck[] | undefined
  loading: boolean
  error: string | null
  onChanged?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.complete)
  const [editing, setEditing] = useState<UnloadingCompletionCheck | null>(null)
  if (loading) {
    return (
      <SectionPanel title="Checklist de cierre" description="Cierre operativo de la descarga">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Checklist de cierre" description="Cierre operativo de la descarga">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!operation) {
    return (
      <SectionPanel title="Checklist de cierre" description="Cierre operativo de la descarga">
        <EmptyPanel title="Sin operación" />
      </SectionPanel>
    )
  }
  if (!checks?.length) {
    return (
      <SectionPanel title="Checklist de cierre" description="Cierre operativo de la descarga">
        <EmptyPanel
          title="Sin checks de cierre"
          description="El backend aún no ha configurado el checklist de cierre."
        />
      </SectionPanel>
    )
  }
  const totals = {
    total: checks.length,
    passed: checks.filter((c) => c.result === 'PASS' || c.result === 'NOT_APPLICABLE').length,
    failed: checks.filter((c) => c.result === 'FAIL').length,
    pending: checks.filter((c) => !c.result).length,
  }
  return (
    <SectionPanel
      title="Checklist de cierre"
      description={`${totals.passed}/${totals.total} completados · ${totals.pending} pendientes · ${totals.failed} con falla`}
    >
      <ul className="space-y-2">
        {checks.map((c) => (
          <li key={c.id} className="rounded-lg border border-slate-200 bg-white p-3 text-xs">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-slate-800">{c.name}</p>
              </div>
              <StatusPill
                tone={
                  c.result === 'PASS' || c.result === 'NOT_APPLICABLE'
                    ? 'success'
                    : c.result === 'PASS_WITH_OBSERVATION'
                      ? 'info'
                      : c.result === 'FAIL'
                        ? 'danger'
                        : 'muted'
                }
              >
                {checkResultLabel(c.result)}
              </StatusPill>
            </div>
            {c.observation && <p className="text-[11px] text-slate-600">Observación: {c.observation}</p>}
            {c.performed_by && (
              <p className="text-[10px] text-slate-500">
                Por: {c.performed_by.display_name} · {c.performed_at ?? '—'}
              </p>
            )}
      {canManage && (
        <Button
          size="small"
          variant="secondary"
          onClick={() => {
            setEditing(c)
          }}
          className="mt-2"
        >
          Actualizar
        </Button>
      )}
          </li>
        ))}
      </ul>
      <UpdateUnloadingReadinessCheckDialog
        open={Boolean(editing)}
        operation={operation}
        check={editing as unknown as import('../types/inbound-docks').UnloadingReadinessCheck | null}
        onOpenChange={(o) => { if (!o) setEditing(null) }}
        onUpdated={() => { onChanged?.() }}
      />
    </SectionPanel>
  )
}
