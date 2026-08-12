import { useNavigate, useParams } from 'react-router-dom'
import { useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { DockAssignmentPlanner } from '../components/DockAssignmentPlanner'
import { ErrorPanel, SectionPanel, SkeletonRows } from '../components/ui/Primitives'
import { useQuery } from '../hooks/useQuery'
import type { DockAssignmentPlan, InboundDockQueueEntry } from '../types/inbound-docks'
import { AssignInboundDockDialog } from '../components/dialogs/AssignInboundDockDialog'
import { OverrideDockCompatibilityDialog } from '../components/dialogs/OverrideDockCompatibilityDialog'

export function DockAssignmentPlanDetailPage() {
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()
  const [assignOpen, setAssignOpen] = useState(false)
  const [overrideOpen, setOverrideOpen] = useState(false)
  const plan = useQuery<DockAssignmentPlan>(
    ['dock-assignment-plan-detail', planId],
    planId ? `/logistics/inbound/dock-assignment-plans/${planId}` : '',
    undefined,
    { enabled: Boolean(planId), refetchIntervalMs: 5_000 },
  )
  const queueEntries = useQuery<{ items: InboundDockQueueEntry[] }>(
    ['dock-queue-by-plan', plan.data?.queue_entry_id],
    plan.data?.queue_entry_id ? `/logistics/inbound-dock-queue?page_size=1&search=${plan.data.queue_entry_id}` : '',
    undefined,
    { enabled: Boolean(plan.data?.queue_entry_id), refetchIntervalMs: 10_000 },
  )
  if (plan.isLoading) return <SkeletonRows rows={4} />
  if (plan.isError) return <ErrorPanel message={plan.error ?? 'No se pudo cargar el plan.'} />
  const planData = plan.data
  if (!planData) return <ErrorPanel message="Plan no encontrado" />
  const entry = (queueEntries.data?.items ?? [])[0] ?? null
  const selectedDockId = planData.recommendation?.recommended_dock_id ?? planData.compatible_docks[0]?.dock_id ?? null
  const compatible = planData.compatible_docks.find((c) => c.dock_id === selectedDockId) ?? null
  const incompatible = planData.incompatible_docks.find((c) => c.dock_id === selectedDockId) ?? null
  return (
    <div className="page">
      <PageHeader
        eyebrow={`Plan ${planData.id.slice(0, 8)}`}
        title="Plan de asignación"
        description="Compatibilidad calculada por el servidor. La asignación no se ejecuta hasta confirmar."
        actions={
          <>
            <Button size="small" variant="secondary" onClick={() => navigate('/logistics/inbound/docks')}>
              Tablero
            </Button>
            {compatible && (
              <Button
                size="small"
                variant="primary"
                onClick={() => setAssignOpen(true)}
              >
                Asignar muelle compatible
              </Button>
            )}
            {incompatible && (
              <Button
                size="small"
                variant="danger"
                onClick={() => setOverrideOpen(true)}
              >
                Override incompatibilidad
              </Button>
            )}
          </>
        }
      />
      <SectionPanel title="Resumen" description="Datos clave del plan">
        <p className="text-xs text-slate-600">Plan expira: {planData.expires_at}</p>
        <p className="text-xs text-slate-600">Compatibles: {planData.compatible_docks.length}</p>
        <p className="text-xs text-slate-600">No compatibles: {planData.incompatible_docks.length}</p>
        <p className="text-xs text-slate-600">Servidor: {planData.server_time}</p>
      </SectionPanel>
      <DockAssignmentPlanner
        entry={entry}
        onAssigned={() => {
          setAssignOpen(false)
          setOverrideOpen(false)
        }}
      />
      <AssignInboundDockDialog
        open={assignOpen}
        entry={entry}
        plan={planData}
        dockId={selectedDockId}
        onOpenChange={setAssignOpen}
        onAssigned={() => { void plan.refetch() }}
      />
      <OverrideDockCompatibilityDialog
        open={overrideOpen}
        entry={entry}
        plan={planData}
        result={incompatible}
        onOpenChange={setOverrideOpen}
        onExecuted={() => { void plan.refetch() }}
      />
    </div>
  )
}
