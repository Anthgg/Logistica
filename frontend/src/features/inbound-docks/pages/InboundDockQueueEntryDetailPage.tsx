import { useParams } from 'react-router-dom'
import { useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { ChangeDockQueuePriorityDialog } from '../components/dialogs/ChangeDockQueuePriorityDialog'
import { DockAssignmentPlanner } from '../components/DockAssignmentPlanner'
import { DockQueueVehicleSummaryPanel } from '../components/DockQueueVehicleSummaryPanel'
import { ErrorPanel, KeyValueGrid, SectionPanel, SkeletonRows, StatusPill } from '../components/ui/Primitives'
import { formatServerTime, priorityLabel, queueStatusLabel } from '../utils/format'
import { useInboundDockQueueEntry } from '../hooks/useInboundDocksQueries'
import type { GateCheckInSummary } from '../types/inbound-docks'
import { useQuery } from '../hooks/useQuery'
import type { DockAssignmentPlan } from '../types/inbound-docks'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function InboundDockQueueEntryDetailPage() {
  const { entryId } = useParams<{ entryId: string }>()
  const { hasPermission } = useLogisticsPermissions()
  const canChange = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.changePriority)
  const [priorityOpen, setPriorityOpen] = useState(false)
  const entry = useInboundDockQueueEntry(entryId ?? null)
  useQuery<DockAssignmentPlan>(
    ['dock-queue-entry-plan', entryId],
    entryId ? `/logistics/inbound/dock-assignment-plans?queue_entry_id=${entryId}` : '',
    undefined,
    { enabled: Boolean(entryId), refetchIntervalMs: 10_000 },
  )
  if (entry.isLoading) return <SkeletonRows rows={4} />
  if (entry.isError) return <ErrorPanel message={entry.error ?? 'No se pudo cargar la entrada.'} />
  const data = entry.data
  if (!data) return <ErrorPanel message="Entrada no encontrada" />
  const checkIn: GateCheckInSummary = {
    id: data.check_in_id,
    cpv_code: data.cpv_code,
    cit_code: data.cit_code,
    warehouse_id: data.warehouse_id,
    warehouse_name: data.warehouse_name,
    gate_id: null,
    gate_name: null,
    vehicle_plate: data.vehicle_plate,
    vehicle_id: data.vehicle_id ?? null,
    driver_name_redacted: data.driver_name_redacted,
    supplier_name: data.supplier_name,
    carrier_name: data.carrier_name,
    arrived_at: null,
    authorized_at: data.gate_clearance_at,
    decision_type: null,
    seal_number: null,
    pallets: data.pallets,
    packages: data.packages,
    weight: data.weight,
    special_requirements: (data.special_requirements ?? []).join(', ') || null,
    conditions: null,
    warnings: data.alerts ?? [],
    status: data.status,
  }
  return (
    <div className="page">
      <PageHeader
        eyebrow={`Cola #${data.position}`}
        title={`${data.cpv_code ?? '—'} · ${data.vehicle_plate ?? '—'}`}
        description={`Proveedor: ${data.supplier_name ?? '—'} · Transportista: ${data.carrier_name ?? '—'}`}
        actions={
          canChange && (
            <Button type="button" variant="secondary" onClick={() => setPriorityOpen(true)}>
              Cambiar prioridad
            </Button>
          )
        }
      />
      <SectionPanel
        title="Estado"
        description="Información de cola y compatibilidad"
        actions={
          <StatusPill tone="info">{queueStatusLabel(data.status)}</StatusPill>
        }
      >
        <KeyValueGrid
          items={[
            { label: 'Posición', value: data.position },
            { label: 'Prioridad', value: priorityLabel(data.priority) },
            { label: 'Vehículo', value: data.vehicle_type ?? '—' },
            { label: 'Muelles compatibles', value: data.compatible_dock_ids?.length ? `${data.compatible_dock_ids.length} muelle(s)` : '—' },
            { label: 'Muelle asignado', value: data.assigned_dock_code ?? '—' },
            { label: 'Hora de entrada a cola', value: formatServerTime(data.entered_queue_at) },
            { label: 'Tiempo en espera', value: data.waiting_seconds != null ? `${data.waiting_seconds}s` : '—' },
            { label: 'Ventana CIT', value: data.cit_window_start && data.cit_window_end ? `${formatServerTime(data.cit_window_start)} – ${formatServerTime(data.cit_window_end)}` : '—' },
          ]}
        />
        {data.alerts && data.alerts.length > 0 && (
          <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-amber-700">
            <ul className="list-disc pl-4 text-[11px]">
              {data.alerts.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
        )}
      </SectionPanel>
      <DockQueueVehicleSummaryPanel checkIn={checkIn} queueEntry={data} />
      <DockAssignmentPlanner
        entry={data}
        onAssigned={() => { void entry.refetch() }}
      />
      <ChangeDockQueuePriorityDialog
        open={priorityOpen}
        entry={data}
        onOpenChange={setPriorityOpen}
        onChanged={() => { void entry.refetch() }}
      />
    </div>
  )
}
