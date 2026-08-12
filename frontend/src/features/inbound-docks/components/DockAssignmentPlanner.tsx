import { useCallback, useEffect, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { CompatibleDocksPanel } from './CompatibleDocksPanel'
import { DockRecommendationPanel } from './DockRecommendationPanel'
import { DockQueueVehicleSummaryPanel } from './DockQueueVehicleSummaryPanel'
import { AssignInboundDockDialog } from './dialogs/AssignInboundDockDialog'
import { OverrideDockCompatibilityDialog } from './dialogs/OverrideDockCompatibilityDialog'
import { useMutation, useQuery } from '../hooks/useQuery'
import { dockAssignmentsApi } from '../api'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows, InlineTabs } from './ui/Primitives'
import {
  compatibilityLabel,
  formatServerTime,
  priorityLabel,
} from '../utils/format'
import type {
  DockAssignmentPlan,
  DockCompatibilityResult,
  GateCheckInSummary,
  InboundDockAssignment,
  InboundDockQueueEntry,
} from '../types/inbound-docks'

const PLANNER_STEPS = [
  'Seleccionar entrada de cola',
  'Revisar vehículo',
  'Revisar carga',
  'Revisar requisitos',
  'Consultar disponibilidad',
  'Consultar compatibilidad',
  'Revisar recomendaciones',
  'Seleccionar muelle',
  'Revisar intervalo',
  'Confirmar asignación',
] as const

type PlannerStep = (typeof PLANNER_STEPS)[number] | 'completado'

export function DockAssignmentPlanner({
  entry,
  onAssigned,
  onCancel,
}: {
  entry: InboundDockQueueEntry | null
  onAssigned?: (assignment: InboundDockAssignment) => void
  onCancel?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canPlan = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.planAssignment)
  const canAssign = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.assign)
  const [step, setStep] = useState<PlannerStep>('Seleccionar entrada de cola')
  const [plan, setPlan] = useState<DockAssignmentPlan | null>(null)
  const [selectedDockId, setSelectedDockId] = useState<string | null>(null)
  const [overrideTarget, setOverrideTarget] = useState<DockCompatibilityResult | null>(null)
  const [assignOpen, setAssignOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const planId = plan?.id ?? null
  const planQuery = useQuery<DockAssignmentPlan>(
    ['dock-assignment-plan-refresh', planId],
    planId ? `/logistics/inbound/dock-assignment-plans/${planId}` : '',
    undefined,
    { enabled: Boolean(planId), refetchIntervalMs: 5_000 },
  )
  useEffect(() => {
    if (planQuery.data) {
      setPlan(planQuery.data)
    }
  }, [planQuery.data])
  const entryQuery = useQuery<InboundDockQueueEntry>(
    ['dock-queue-entry-refresh', entry?.id],
    entry ? `/logistics/inbound-dock-queue/${entry.id}` : '',
    undefined,
    { enabled: Boolean(entry), refetchIntervalMs: 5_000 },
  )
  const createPlan = useMutation<{ queueEntryId: string }, DockAssignmentPlan>(
    async (input) => dockAssignmentsApi.createPlan({ queue_entry_id: input.queueEntryId }),
    {
      onSuccess: (data) => {
        setPlan(data)
        setStep('Consultar disponibilidad')
      },
    },
  )
  const queueEntry: InboundDockQueueEntry | null = entryQuery.data ?? entry
  const planCompatible = plan?.compatible_docks ?? []
  const planIncompatible = plan?.incompatible_docks ?? []
  const planRecommendation = plan?.recommendation ?? null
  const recommendedId = planRecommendation?.recommended_dock_id ?? null
  const compatibleById = new Map(planCompatible.map((c) => [c.dock_id, c]))
  const incompatibleById = new Map(planIncompatible.map((c) => [c.dock_id, c]))
  const handleSelect = useCallback(
    (result: DockCompatibilityResult) => {
      setSelectedDockId(result.dock_id)
      setStep('Seleccionar muelle')
    },
    [],
  )
  const handleStartPlan = useCallback(async () => {
    if (!queueEntry) return
    setErrorMessage(null)
    await createPlan.mutate({ queueEntryId: queueEntry.id })
  }, [queueEntry, createPlan])
  const selectedCompatible: DockCompatibilityResult | null = selectedDockId
    ? compatibleById.get(selectedDockId) ?? null
    : null
  const selectedIncompatible: DockCompatibilityResult | null = selectedDockId
    ? incompatibleById.get(selectedDockId) ?? null
    : null
  const isSelectionIncompatible = Boolean(selectedIncompatible)
  const checkInMock: GateCheckInSummary | null = queueEntry
    ? {
        id: queueEntry.check_in_id,
        cpv_code: queueEntry.cpv_code,
        cit_code: queueEntry.cit_code,
        warehouse_id: queueEntry.warehouse_id,
        warehouse_name: queueEntry.warehouse_name,
        gate_id: null,
        gate_name: null,
        vehicle_plate: queueEntry.vehicle_plate,
        vehicle_id: queueEntry.vehicle_id ?? null,
        driver_name_redacted: queueEntry.driver_name_redacted,
        supplier_name: queueEntry.supplier_name,
        carrier_name: queueEntry.carrier_name,
        arrived_at: null,
        authorized_at: queueEntry.gate_clearance_at,
        decision_type: null,
        seal_number: null,
        pallets: queueEntry.pallets,
        packages: queueEntry.packages,
        weight: queueEntry.weight,
        special_requirements: (queueEntry.special_requirements ?? []).join(', ') || null,
        conditions: null,
        warnings: queueEntry.alerts ?? [],
        status: queueEntry.status,
      }
    : null
  if (!queueEntry) {
    return (
      <SectionPanel
        title="Planificador de asignación"
        description="Selecciona una entrada de cola para iniciar la planificación."
      >
        <EmptyPanel
          title="Sin entrada de cola"
          description="Selecciona un vehículo en la cola para iniciar el plan."
        />
      </SectionPanel>
    )
  }
  const confirm = () => {
    if (!selectedDockId) {
      setStep('Seleccionar muelle')
      return
    }
    if (isSelectionIncompatible) {
      const result = selectedIncompatible
      if (result) {
        setOverrideTarget(result)
      }
    } else {
      setAssignOpen(true)
    }
  }
  const stepIndex = PLANNER_STEPS.indexOf(step as (typeof PLANNER_STEPS)[number])
  return (
    <div className="space-y-4">
      <SectionPanel
        title="Planificador de asignación"
        description={`Entrada #${queueEntry.position} · ${queueEntry.cpv_code ?? '—'} · ${queueEntry.cit_code ?? '—'} · Prioridad ${priorityLabel(queueEntry.priority)}`}
        actions={
          <StatusPill tone={plan ? 'success' : 'info'}>
            {plan ? `Plan ${plan.id.slice(0, 8)}` : 'Sin plan'}
          </StatusPill>
        }
      >
        <ol className="flex flex-wrap items-center gap-1 text-[10px]">
          {PLANNER_STEPS.map((s, idx) => (
            <li
              key={s}
              className={`flex items-center gap-1 rounded-md border px-2 py-1 ${
                step === s
                  ? 'border-[#1F4E6D] bg-[#1F4E6D]/5 text-[#1F4E6D]'
                  : stepIndex > idx || step === 'completado'
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                    : 'border-slate-200 text-slate-500'
              }`}
            >
              <span className="font-bold">{idx + 1}.</span>
              <span>{s}</span>
            </li>
          ))}
        </ol>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            type="button"
            variant="primary"
            onClick={handleStartPlan}
            disabled={!canPlan || createPlan.isPending}
            isLoading={createPlan.isPending}
          >
            {plan ? 'Regenerar plan' : 'Generar plan'}
          </Button>
          {plan && (
            <>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setStep('Revisar recomendaciones')}
              >
                Ver recomendación
              </Button>
              {selectedDockId && (
                <Button
                  type="button"
                  variant={isSelectionIncompatible ? 'danger' : 'primary'}
                  onClick={confirm}
                  disabled={!canAssign}
                >
                  {isSelectionIncompatible ? 'Override y asignar' : 'Confirmar asignación'}
                </Button>
              )}
            </>
          )}
          {onCancel && (
            <Button type="button" variant="ghost" onClick={onCancel}>
              Cancelar
            </Button>
          )}
        </div>
        {errorMessage && <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {createPlan.error && <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{createPlan.error}</p>}
      </SectionPanel>
      <InlineTabs
        tabs={[
          { key: 'vehiculo', label: 'Vehículo y carga' },
          { key: 'compatibilidad', label: 'Compatibilidad' },
          { key: 'recomendacion', label: 'Recomendación' },
          { key: 'muelle', label: 'Selección de muelle' },
        ]}
        value={step === 'Seleccionar muelle' || step === 'completado' ? 'muelle' : step === 'Consultar compatibilidad' || step === 'Revisar recomendaciones' ? 'compatibilidad' : 'vehiculo'}
        onChange={(k) => {
          if (k === 'vehiculo') setStep('Revisar vehículo')
          if (k === 'compatibilidad') setStep('Consultar compatibilidad')
          if (k === 'recomendacion') setStep('Revisar recomendaciones')
          if (k === 'muelle') setStep('Seleccionar muelle')
        }}
      />
      {(step === 'Revisar vehículo' ||
        step === 'Revisar carga' ||
        step === 'Revisar requisitos' ||
        step === 'Seleccionar entrada de cola' ||
        step === 'Consultar disponibilidad') && (
        <div className="space-y-3">
          <DockQueueVehicleSummaryPanel checkIn={checkInMock} queueEntry={queueEntry} />
          <SectionPanel
            title="Requisitos de la entrada"
            description="Información consolidada para la planificación."
          >
            <ul className="list-disc pl-4 text-xs text-slate-700">
              <li>Proveedor: {queueEntry.supplier_name ?? '—'}</li>
              <li>Transportista: {queueEntry.carrier_name ?? '—'}</li>
              <li>Pallets esperados: {queueEntry.pallets ?? '—'}</li>
              <li>Bultos esperados: {queueEntry.packages ?? '—'}</li>
              <li>Peso: {queueEntry.weight ?? '—'}</li>
              <li>Requisitos: {queueEntry.special_requirements?.join(', ') ?? '—'}</li>
              <li>Hora de entrada a cola: {formatServerTime(queueEntry.entered_queue_at)}</li>
              <li>Compatibles previos: {queueEntry.compatible_dock_ids?.length ?? 0} muelle(s)</li>
            </ul>
          </SectionPanel>
        </div>
      )}
      {(step === 'Consultar compatibilidad' || step === 'Revisar recomendaciones' || step === 'Seleccionar muelle' || step === 'Revisar intervalo' || step === 'completado') && (
        <div className="space-y-3">
          {!plan && (
            <SectionPanel
              title="Compatibilidad"
              description="Genera un plan para obtener la compatibilidad calculada por el servidor."
            >
              {createPlan.isPending ? <SkeletonRows /> : <EmptyPanel title="Sin plan" description="Genera el plan para ver los muelles compatibles." />}
            </SectionPanel>
          )}
          {plan && (
            <>
              <CompatibleDocksPanel
                compatible={planCompatible}
                incompatible={planIncompatible}
                recommendedId={recommendedId}
                onSelect={handleSelect}
              />
              <DockRecommendationPanel recommendation={planRecommendation} />
              {selectedCompatible && (
                <SectionPanel
                  title="Muelle seleccionado"
                  description="Confirma para ejecutar la asignación."
                >
                  <p className="text-sm font-bold text-slate-800">
                    {selectedCompatible.dock_code} — {selectedCompatible.dock_name}
                  </p>
                  <p className="text-[11px] text-slate-600">
                    Compatibilidad: {compatibilityLabel(selectedCompatible.compatibility_status)}
                  </p>
                  {selectedCompatible.estimated_availability && (
                    <p className="text-[11px] text-slate-600">
                      Disponibilidad estimada: {formatServerTime(selectedCompatible.estimated_availability)}
                    </p>
                  )}
                </SectionPanel>
              )}
              {selectedIncompatible && (
                <SectionPanel
                  title="Muelle seleccionado (con restricciones)"
                  description="Se requerirá un override para asignarlo."
                >
                  <ErrorPanel
                    message={`Muelle ${selectedIncompatible.dock_code} con restricciones: ${compatibilityLabel(selectedIncompatible.compatibility_status)}`}
                  />
                  <ul className="mt-2 list-disc pl-4 text-[11px] text-rose-700">
                    {selectedIncompatible.restriction_conflicts.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                </SectionPanel>
              )}
            </>
          )}
        </div>
      )}
      <AssignInboundDockDialog
        open={assignOpen}
        entry={queueEntry}
        plan={plan}
        dockId={selectedCompatible ? selectedCompatible.dock_id : null}
        onOpenChange={setAssignOpen}
        onAssigned={(a) => {
          setStep('completado')
          onAssigned?.(a)
        }}
      />
      <OverrideDockCompatibilityDialog
        open={Boolean(overrideTarget)}
        entry={queueEntry}
        plan={plan}
        result={overrideTarget}
        onOpenChange={(open) => {
          if (!open) setOverrideTarget(null)
        }}
        onExecuted={(a) => {
          setStep('completado')
          setOverrideTarget(null)
          onAssigned?.(a)
        }}
      />
    </div>
  )
}
