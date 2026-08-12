import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import {
  ConfirmDockArrivalDialog,
  StartMovementToDockDialog,
} from '../components/dialogs/MovementDialogs'
import { ReassignInboundDockDialog } from '../components/dialogs/ReassignInboundDockDialog'
import { ReleaseWarehouseDockDialog } from '../components/dialogs/UnloadingSupportDialogs'
import { RequestDockOperationalTimeCorrectionDialog } from '../components/dialogs/OperationalDialogs'
import { DockOperationTimeline } from '../components/DockOperationTimeline'
import { DockOperationalTimesPanel } from '../components/DockOperationalTimesPanels'
import { DockOperationsServerClock } from '../components/ui/DockOperationsServerClock'
import {
  ErrorPanel,
  InlineTabs,
  KeyValueGrid,
  SectionPanel,
  SkeletonRows,
  StatusPill,
} from '../components/ui/Primitives'
import {
  assignmentStatusLabel,
  assignmentStatusTone,
  formatServerDateTime,
  formatServerTime,
  priorityLabel,
} from '../utils/format'
import {
  useDockAssignmentHistory,
  useDockAssignmentMetrics,
  useDockOperationalTimes,
  useInboundDockAssignment,
  useUnloadingOperationsList,
} from '../hooks/useInboundDocksQueries'
import { useQuery } from '../hooks/useQuery'
import type { DockCompatibilityResult, InboundDockAssignment } from '../types/inbound-docks'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

type Tab = 'summary' | 'dock' | 'vehicle' | 'unloading' | 'responsibles' | 'seal' | 'events' | 'times' | 'integrity' | 'history'

const TABS: Array<{ key: Tab; label: string }> = [
  { key: 'summary', label: 'Resumen' },
  { key: 'dock', label: 'Muelle' },
  { key: 'vehicle', label: 'Vehículo' },
  { key: 'unloading', label: 'Descarga' },
  { key: 'responsibles', label: 'Responsables' },
  { key: 'seal', label: 'Precinto' },
  { key: 'events', label: 'Eventos' },
  { key: 'times', label: 'Tiempos' },
  { key: 'integrity', label: 'Integridad' },
  { key: 'history', label: 'Historial' },
]

export function InboundDockAssignmentDetailPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>()
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canReassign = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.reassign)
  const canRelease = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.releaseDock)
  const canStartMovement = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.startMovement)
  const canConfirmArrival = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.confirmArrival)
  const canRequestCorrection = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.requestTimeCorrection)
  const canApproveCorrection = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.approveTimeCorrection)
  const [tab, setTab] = useState<Tab>('summary')
  const [startMovementOpen, setStartMovementOpen] = useState(false)
  const [confirmArrivalOpen, setConfirmArrivalOpen] = useState(false)
  const [reassignOpen, setReassignOpen] = useState(false)
  const [releaseOpen, setReleaseOpen] = useState(false)
  const [correctionOpen, setCorrectionOpen] = useState(false)
  const [reassignDockId, setReassignDockId] = useState<string | null>(null)
  const assignment = useInboundDockAssignment(assignmentId ?? null)
  const history = useDockAssignmentHistory(assignmentId ?? null)
  const metrics = useDockAssignmentMetrics(assignmentId ?? null)
  const times = useDockOperationalTimes(assignmentId ?? null)
  const integrity = useQuery<{ assignment_id: string; status: 'VALID' | 'FAILED' | 'PENDING'; failures: string[]; last_checked_at: string | null; partial_hash: string | null }>(
    ['dock-assignment-integrity', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}/integrity` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: 15_000 },
  )
  useQuery<{ items: Array<{ id: string; dock_id: string; queue_entry_id: string; expires_at: string; server_time: string; created_at: string; compatible_docks: DockCompatibilityResult[]; incompatible_docks: DockCompatibilityResult[]; recommendation: { recommended_dock_id: string | null; recommended_dock_code: string | null; recommended_dock_name: string | null; reasons: string[]; is_available: boolean; matched_capabilities: string[]; estimated_wait_seconds: number | null; warnings: string[]; policy_used: string | null; alternatives: DockCompatibilityResult[] } | null }> }>(
    ['dock-assignment-plans-by-assignment', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignment-plans?assignment_id=${assignmentId}` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: 15_000 },
  )
  const operations = useUnloadingOperationsList(
    { assignment_id: assignmentId ?? undefined },
    { refetchIntervalMs: 10_000 },
  )
  if (assignment.isLoading) return <SkeletonRows rows={4} />
  if (assignment.isError) return <ErrorPanel message={assignment.error ?? 'No se pudo cargar la asignación.'} />
  const a: InboundDockAssignment | null = assignment.data ?? null
  if (!a) return <ErrorPanel message="Asignación no encontrada" />
  return (
    <div className="page">
      <PageHeader
        eyebrow={`Asignación ${a.id.slice(0, 8)}`}
        title={`${a.cpv_code ?? a.cit_code ?? '—'} · ${a.vehicle?.plate ?? '—'}`}
        description={`Muelle: ${a.dock_code} — ${a.dock_name} · Estado: ${assignmentStatusLabel(a.status)} · Prioridad: ${priorityLabel(a.priority)}`}
        actions={
          <>
            <DockOperationsServerClock serverTimeIso={a.server_time} timezone={null} />
            {canStartMovement && a.status === 'ASSIGNED' && (
              <Button size="small" variant="primary" onClick={() => setStartMovementOpen(true)}>
                Iniciar movimiento
              </Button>
            )}
            {canConfirmArrival && a.status === 'IN_MOVEMENT' && (
              <Button size="small" variant="primary" onClick={() => setConfirmArrivalOpen(true)}>
                Confirmar llegada
              </Button>
            )}
            {canReassign && (
              <Button
                size="small"
                variant="secondary"
                onClick={() => {
                  setReassignDockId(null)
                  setReassignOpen(true)
                }}
              >
                Reasignar
              </Button>
            )}
            {canRelease && a.status === 'PENDING_RELEASE' && (
              <Button size="small" variant="primary" onClick={() => setReleaseOpen(true)}>
                Liberar muelle
              </Button>
            )}
            {(canRequestCorrection || canApproveCorrection) && (
              <Button size="small" variant="secondary" onClick={() => setCorrectionOpen(true)}>
                Solicitar corrección
              </Button>
            )}
          </>
        }
      />
      <SectionPanel
        title="Encabezado operativo"
        description="Datos principales de la asignación"
        actions={
          <StatusPill tone={assignmentStatusTone(a.status)}>
            {assignmentStatusLabel(a.status)}
          </StatusPill>
        }
      >
        <KeyValueGrid
          items={[
            { label: 'CPV', value: a.cpv_code ?? '—' },
            { label: 'CIT', value: a.cit_code ?? '—' },
            { label: 'Proveedor', value: a.supplier?.name ?? '—' },
            { label: 'Transportista', value: a.carrier?.name ?? '—' },
            { label: 'Placa', value: a.vehicle?.plate ?? '—' },
            { label: 'Muelle', value: `${a.dock_code} — ${a.dock_name}` },
            { label: 'Estado', value: assignmentStatusLabel(a.status) },
            { label: 'Prioridad', value: priorityLabel(a.priority) },
            { label: 'Hora de asignación', value: a.assigned_at ? formatServerTime(a.assigned_at) : '—' },
            { label: 'Inicio de movimiento', value: a.movement_started_at ? formatServerTime(a.movement_started_at) : '—' },
            { label: 'Llegada al muelle', value: a.arrived_at_dock_at ? formatServerTime(a.arrived_at_dock_at) : '—' },
            { label: 'Liberación', value: a.released_at ? formatServerTime(a.released_at) : '—' },
            { label: 'Override', value: a.is_override ? 'Sí' : 'No' },
            { label: 'Reasignado', value: a.was_reassigned ? 'Sí' : 'No' },
            { label: 'Operación activa', value: a.active_unloading_operation_id ?? '—' },
          ]}
        />
        {a.alerts && a.alerts.length > 0 && (
          <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50/40 p-2 text-amber-700">
            <p className="text-[11px] font-semibold">Alertas</p>
            <ul className="list-disc pl-4 text-[11px]">
              {a.alerts.map((al) => (
                <li key={al}>{al}</li>
              ))}
            </ul>
          </div>
        )}
      </SectionPanel>
      <InlineTabs tabs={TABS} value={tab} onChange={setTab} />
      {tab === 'summary' && (
        <div className="space-y-3">
          <SectionPanel title="Capacidades (capabilities)">
            <ul className="grid grid-cols-2 gap-1 text-xs text-slate-700 md:grid-cols-3">
              {Object.entries(a.capabilities).map(([key, value]) => (
                <li key={key} className="rounded border border-slate-200 bg-white px-2 py-1">
                  <span className="font-semibold">{key}:</span> {value ? 'Sí' : 'No'}
                </li>
              ))}
            </ul>
          </SectionPanel>
        </div>
      )}
      {tab === 'dock' && (
        <SectionPanel
          title="Muelle"
          description="Datos de la asignación y compatibilidad calculada por el backend."
        >
          <p className="text-xs text-slate-600">
            Muelle: {a.dock_code} — {a.dock_name}
          </p>
          <p className="text-xs text-slate-600">Estado: {assignmentStatusLabel(a.status)}</p>
          <p className="text-xs text-slate-600">Override aplicado: {a.is_override ? 'Sí' : 'No'}</p>
          {a.override_reason && <p className="text-xs text-slate-600">Motivo override: {a.override_reason}</p>}
          {a.was_reassigned && (
            <p className="text-xs text-slate-600">
              Muelle previo: {a.previous_dock_code ?? '—'} · Motivo: {a.reassignment_reason ?? '—'}
            </p>
          )}
        </SectionPanel>
      )}
      {tab === 'vehicle' && (
        <SectionPanel title="Vehículo" description="Información consolidada del vehículo">
          <KeyValueGrid
            items={[
              { label: 'Placa', value: a.vehicle?.plate ?? '—', mono: true },
              { label: 'Marca', value: a.vehicle?.make ?? '—' },
              { label: 'Modelo', value: a.vehicle?.model ?? '—' },
              { label: 'Tipo', value: a.vehicle?.vehicle_type ?? '—' },
              { label: 'Estado', value: a.vehicle?.status ?? '—' },
              { label: 'Transportista', value: a.vehicle?.carrier_name ?? a.carrier?.name ?? '—' },
            ]}
          />
        </SectionPanel>
      )}
      {tab === 'unloading' && (
        <SectionPanel
          title="Descarga"
          description="Operaciones asociadas a la asignación"
        >
          {operations.isLoading ? (
            <SkeletonRows rows={3} />
          ) : (
            <ul className="space-y-2 text-xs">
              {(operations.data?.items ?? []).map((o) => (
                <li key={o.id} className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono">{o.id.slice(0, 8)}</span>
                    <StatusPill tone="info">{o.status}</StatusPill>
                  </div>
                  <p className="text-[11px] text-slate-500">{formatServerDateTime(o.started_at_server ?? o.started_at ?? o.created_at)}</p>
                  <Button
                    size="small"
                    variant="secondary"
                    className="mt-2"
                    onClick={() => navigate(`/logistics/inbound/unloading/${o.id}`)}
                  >
                    Abrir workspace
                  </Button>
                </li>
              ))}
              {(operations.data?.items ?? []).length === 0 && (
                <li className="rounded-md border border-dashed border-slate-200 bg-white p-3 text-[11px] text-slate-400">
                  Sin operaciones.
                </li>
              )}
            </ul>
          )}
        </SectionPanel>
      )}
      {tab === 'responsibles' && (
        <SectionPanel title="Responsables" description="Solo lectura, gestionados en el workspace de descarga">
          <p className="text-xs text-slate-600">
            Los responsables se asignan desde el workspace de descarga. Esta pantalla es de solo lectura.
          </p>
        </SectionPanel>
      )}
      {tab === 'seal' && (
        <SectionPanel title="Precinto" description="Solo lectura, gestionado en el workspace de descarga">
          <p className="text-xs text-slate-600">
            La apertura de precinto se registra desde el workspace de descarga.
          </p>
        </SectionPanel>
      )}
      {tab === 'events' && (
        <DockOperationTimeline
          events={history.data}
          loading={history.isLoading}
          error={history.error}
        />
      )}
      {tab === 'times' && (
        <div className="space-y-3">
          <DockOperationalTimesPanel times={times.data} loading={times.isLoading} error={times.error} />
          <SectionPanel
            title="Métricas operativas"
            description="Fuente operativa, no KPI corporativo."
          >
            <KeyValueGrid
              items={[
                { label: 'Espera', value: metrics.data?.wait_seconds != null ? `${metrics.data.wait_seconds}s` : '—' },
                { label: 'Movimiento', value: metrics.data?.movement_seconds != null ? `${metrics.data.movement_seconds}s` : '—' },
                { label: 'Espera en muelle', value: metrics.data?.dock_wait_seconds != null ? `${metrics.data.dock_wait_seconds}s` : '—' },
                { label: 'Ocupación', value: metrics.data?.dock_occupancy_seconds != null ? `${metrics.data.dock_occupancy_seconds}s` : '—' },
                { label: 'Ciclo total', value: metrics.data?.total_cycle_seconds != null ? `${metrics.data.total_cycle_seconds}s` : '—' },
              ]}
            />
          </SectionPanel>
        </div>
      )}
      {tab === 'integrity' && (
        <SectionPanel title="Integridad" description="Validación del backend">
          {integrity.isLoading ? (
            <SkeletonRows rows={3} />
          ) : integrity.data ? (
            <div className="space-y-1 text-xs text-slate-700">
              <p>Estado: <span className="font-mono">{integrity.data.status}</span></p>
              <p>Última verificación: {integrity.data.last_checked_at ? formatServerTime(integrity.data.last_checked_at) : '—'}</p>
              {integrity.data.failures.length > 0 && (
                <ul className="list-disc pl-4 text-rose-700">
                  {integrity.data.failures.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500">Sin datos de integridad.</p>
          )}
        </SectionPanel>
      )}
      {tab === 'history' && (
        <DockOperationTimeline
          events={history.data}
          loading={history.isLoading}
          error={history.error}
        />
      )}
      {tab === 'summary' && (
        <>
          <StartMovementToDockDialog
            open={startMovementOpen}
            assignment={a}
            onOpenChange={setStartMovementOpen}
            onStarted={() => { void assignment.refetch() }}
          />
          <ConfirmDockArrivalDialog
            open={confirmArrivalOpen}
            assignment={a}
            onOpenChange={setConfirmArrivalOpen}
            onConfirmed={() => { void assignment.refetch() }}
          />
          <ReassignInboundDockDialog
            open={reassignOpen}
            assignment={a}
            newDockId={reassignDockId}
            onOpenChange={(o) => { if (!o) { setReassignOpen(false); setReassignDockId(null) } }}
            onReassigned={() => { void assignment.refetch() }}
          />
          <ReleaseWarehouseDockDialog
            open={releaseOpen}
            assignment={a}
            onOpenChange={setReleaseOpen}
            onReleased={() => { void assignment.refetch() }}
          />
          <RequestDockOperationalTimeCorrectionDialog
            open={correctionOpen}
            assignment={a}
            onOpenChange={setCorrectionOpen}
            onRequested={() => { void assignment.refetch() }}
          />
        </>
      )}
    </div>
  )
}

