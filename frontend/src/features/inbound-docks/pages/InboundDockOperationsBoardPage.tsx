import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsContextSelector } from '../../logistics-permissions/hooks/useLogisticsContextSelector'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { DailySummary } from '../components/DailySummary'
import { DockQueueFilters, type QueueFilter } from '../components/Filters'
import { InboundBoard, type BoardCardEntry } from '../components/InboundBoard'
import { ChangeDockQueuePriorityDialog } from '../components/dialogs/ChangeDockQueuePriorityDialog'
import { DockOperationsServerClock } from '../components/ui/DockOperationsServerClock'
import { ErrorPanel, SkeletonRows, StatusPill, SectionPanel, EmptyPanel } from '../components/ui/Primitives'
import { useInboundDockAssignments, useInboundDockQueue, useInboundDockQueueSummary, useUnloadingOperationsList } from '../hooks/useInboundDocksQueries'
import type { InboundDockQueueEntry } from '../types/inbound-docks'

type ViewMode = 'board' | 'table' | 'calendar'

export function InboundDockOperationsBoardPage() {
  const navigate = useNavigate()
  const { context, options } = useLogisticsContextSelector()
  const { hasPermission, userId } = useLogisticsPermissions()
  const canViewQueue = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.viewQueue)
  const [filter, setFilter] = useState<QueueFilter>({})
  const [view, setView] = useState<ViewMode>('board')
  const [priorityEntry, setPriorityEntry] = useState<InboundDockQueueEntry | null>(null)
  const warehouseId = filter.warehouse_id ?? context.warehouse_id ?? options.warehouses[0]?.id ?? ''
  useEffect(() => {
    if (!filter.warehouse_id && warehouseId) {
      setFilter((prev) => ({ ...prev, warehouse_id: warehouseId }))
    }
  }, [filter.warehouse_id, warehouseId])
  const summary = useInboundDockQueueSummary(warehouseId)
  const queue = useInboundDockQueue({ ...filter, page_size: 100 })
  const assignments = useInboundDockAssignments(
    { warehouse_id: warehouseId, date_from: filter.date_from, date_to: filter.date_to },
    { refetchIntervalMs: 10_000 },
  )
  const operations = useUnloadingOperationsList(
    { warehouse_id: warehouseId },
    { refetchIntervalMs: 10_000 },
  )
  const boardEntries = useMemo<BoardCardEntry[]>(() => {
    const queueEntries: BoardCardEntry[] = (queue.data?.items ?? []).map((entry) => ({
      entry,
      waitingSeconds: entry.waiting_seconds ?? null,
      priority: entry.priority,
      status: entry.status,
      dockCode: entry.assigned_dock_code,
      alerts: entry.alerts,
    }))
    for (const a of assignments.data?.items ?? []) {
      queueEntries.push({
        assignmentId: a.id,
        assignmentStatus: a.status,
        dockCode: a.dock_code,
        // Interpolación visual basada en server_time del backend.
        // No se usa Date.now() como autoridad. El backend entrega server_time en cada respuesta.
        waitingSeconds: (() => {
          if (!a.assigned_at || !a.server_time) return null
          const serverMs = Date.parse(a.server_time)
          const assignedMs = Date.parse(a.assigned_at)
          if (Number.isNaN(serverMs) || Number.isNaN(assignedMs)) return null
          return Math.max(0, Math.floor((serverMs - assignedMs) / 1000))
        })(),
        priority: a.priority,
        alerts: a.alerts,
        message: `${a.cpv_code ?? '—'} · ${a.vehicle?.plate ?? '—'}`,
        entry: {
          id: a.id,
          position: 0,
          priority: a.priority,
          status: 'WAITING',
          check_in_id: a.check_in_id,
          cpv_code: a.cpv_code,
          cit_code: a.cit_code,
          warehouse_id: a.warehouse_id,
          warehouse_name: a.warehouse_name,
          supplier_id: a.supplier?.id ?? null,
          supplier_name: a.supplier?.name ?? null,
          carrier_id: a.carrier?.id ?? null,
          carrier_name: a.carrier?.name ?? null,
          vehicle_id: a.vehicle?.id ?? null,
          vehicle_plate: a.vehicle?.plate ?? null,
          vehicle_type: a.vehicle?.vehicle_type ?? null,
          driver_name_redacted: null,
          gate_clearance_at: null,
          entered_queue_at: a.assigned_at,
          assigned_dock_id: a.dock_id,
          assigned_dock_code: a.dock_code,
          assigned_dock_name: a.dock_name,
          cit_window_start: null,
          cit_window_end: null,
          pallets: null,
          packages: null,
          weight: null,
          special_requirements: [],
          compatible_dock_ids: [],
          alerts: a.alerts,
          waiting_seconds: null,
          server_time: a.server_time,
        },
      })
    }
    for (const o of operations.data?.items ?? []) {
      queueEntries.push({
        assignmentId: o.assignment_id,
        assignmentStatus:
          o.status === 'ACTIVE'
            ? 'UNLOADING_ACTIVE'
            : o.status === 'PAUSED'
              ? 'UNLOADING_PAUSED'
              : o.status === 'COMPLETED'
                ? 'UNLOADING_COMPLETED'
                : 'AT_DOCK',
        unloadingStatus: o.status,
        dockCode: o.dock_code,
        waitingSeconds: null,
        priority: 'NORMAL',
        alerts: o.alerts,
        responsible: o.responsibles?.[0]?.user?.display_name ?? null,
        message: `${o.cpv_code ?? '—'} · ${o.vehicle?.plate ?? '—'}`,
        entry: {
          id: o.id,
          position: 0,
          priority: 'NORMAL',
          status: 'WAITING',
          check_in_id: o.check_in_id,
          cpv_code: o.cpv_code,
          cit_code: o.cit_code,
          warehouse_id: o.warehouse_id,
          warehouse_name: '',
          supplier_id: o.supplier?.id ?? null,
          supplier_name: o.supplier?.name ?? null,
          carrier_id: o.carrier?.id ?? null,
          carrier_name: o.carrier?.name ?? null,
          vehicle_id: o.vehicle?.id ?? null,
          vehicle_plate: o.vehicle?.plate ?? null,
          vehicle_type: o.vehicle?.vehicle_type ?? null,
          driver_name_redacted: null,
          gate_clearance_at: null,
          entered_queue_at: o.created_at,
          assigned_dock_id: o.dock_id,
          assigned_dock_code: o.dock_code,
          assigned_dock_name: '',
          cit_window_start: null,
          cit_window_end: null,
          pallets: null,
          packages: null,
          weight: null,
          special_requirements: [],
          compatible_dock_ids: [],
          alerts: o.alerts,
          waiting_seconds: null,
          server_time: o.server_time,
        },
      })
    }
    return queueEntries
  }, [queue.data, assignments.data, operations.data])
  const onSelectEntry = (entry: InboundDockQueueEntry) => {
    navigate(`/logistics/inbound/docks/queue/${entry.id}`)
  }
  const onSelectAssignment = (assignmentId: string) => {
    navigate(`/logistics/inbound/dock-assignments/${assignmentId}`)
  }
  const serverTime = summary.data?.server_time ?? null
  const timezone = summary.data?.timezone ?? null
  const myUser = userId
  return (
    <div className="page">
      <PageHeader
        eyebrow="Fase 038"
        title="Muelles de entrada"
        description="Tablero operativo. Los estados provienen del backend."
        actions={
          <>
            <DockOperationsServerClock serverTimeIso={serverTime} timezone={timezone} />
            <Button
              size="small"
              variant="secondary"
              onClick={() => navigate('/logistics/inbound/docks/queue')}
            >
              Cola
            </Button>
            <Button
              size="small"
              variant="secondary"
              onClick={() => navigate('/logistics/inbound/docks')}
            >
              Vista de muelles
            </Button>
          </>
        }
      />
      <DailySummary summary={summary.data ?? null} />
      <SectionPanel title="Vistas" description="Alterna entre tablero, tabla y calendario operativo.">
        <div className="flex flex-wrap gap-1">
          {(['board', 'table', 'calendar'] as const).map((v) => (
            <button
              key={v}
              type="button"
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                view === v
                  ? 'bg-[#1F4E6D] text-white'
                  : 'border border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
              onClick={() => setView(v)}
            >
              {v === 'board' ? 'Tablero' : v === 'table' ? 'Tabla' : 'Calendario'}
            </button>
          ))}
        </div>
      </SectionPanel>
      <DockQueueFilters
        value={filter}
        onChange={setFilter}
        warehouses={options.warehouses.length ? options.warehouses : (warehouseId ? [{ id: warehouseId, label: warehouseId }] : [])}
        showMine
        onMineChange={() => undefined}
      />
      {!canViewQueue && (
        <ErrorPanel message="No tienes capability para visualizar la cola de muelles." />
      )}
      {view === 'board' && (
        <>
          {queue.isLoading && <SkeletonRows rows={4} />}
          {queue.isError && <ErrorPanel message={queue.error ?? 'No se pudo cargar la cola.'} />}
          {!queue.isLoading && !queue.isError && boardEntries.length === 0 && (
            <EmptyPanel title="Sin operaciones" description="No hay entradas de cola ni asignaciones activas." />
          )}
          {boardEntries.length > 0 && (
            <InboundBoard
              entries={boardEntries}
              onSelectEntry={onSelectEntry}
              onSelectAssignment={onSelectAssignment}
              actionsFor={(e) => {
                if (!e.entry?.id) return []
                return [
                  {
                    label: 'Prioridad',
                    onClick: () => {
                      if (e.entry) setPriorityEntry(e.entry)
                    },
                  },
                ]
              }}
            />
          )}
        </>
      )}
      {view === 'table' && (
        <SectionPanel title="Tabla de operaciones" description="Datos directos del backend">
          {queue.isLoading ? (
            <SkeletonRows rows={4} />
          ) : (
            <ul className="divide-y divide-slate-100 text-xs">
              {(queue.data?.items ?? []).map((entry) => (
                <li key={entry.id} className="grid grid-cols-2 gap-1 py-2 sm:grid-cols-5">
                  <span className="font-mono">{entry.position}</span>
                  <span className="font-mono">{entry.cpv_code ?? '—'}</span>
                  <span className="font-mono">{entry.vehicle_plate ?? '—'}</span>
                  <span>
                    <StatusPill tone="info">{entry.status}</StatusPill>
                  </span>
                  <span className="text-right">
                    <Button size="small" variant="secondary" onClick={() => onSelectEntry(entry)}>
                      Ver
                    </Button>
                  </span>
                </li>
              ))}
              {(queue.data?.items ?? []).length === 0 && <p className="py-4 text-center text-slate-500">Sin entradas.</p>}
            </ul>
          )}
        </SectionPanel>
      )}
      {view === 'calendar' && (
        <SectionPanel title="Calendario operativo" description="Eventos del backend">
          {(assignments.data?.items ?? []).length === 0 && (operations.data?.items ?? []).length === 0 ? (
            <EmptyPanel title="Sin eventos" description="No hay eventos para el día seleccionado." />
          ) : (
            <ul className="space-y-2 text-xs">
              {(assignments.data?.items ?? []).map((a) => (
                <li key={a.id} className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono">{a.cpv_code ?? '—'} · {a.vehicle?.plate ?? '—'}</span>
                    <StatusPill tone="info">{a.status}</StatusPill>
                  </div>
                  <p className="text-[11px] text-slate-500">Muelle: {a.dock_code}</p>
                  <p className="text-[10px] text-slate-500">{a.assigned_at}</p>
                </li>
              ))}
              {(operations.data?.items ?? []).map((o) => (
                <li key={o.id} className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono">{o.cpv_code ?? '—'} · {o.vehicle?.plate ?? '—'}</span>
                    <StatusPill tone="muted">{o.status}</StatusPill>
                  </div>
                  <p className="text-[11px] text-slate-500">Operación: {o.id}</p>
                </li>
              ))}
            </ul>
          )}
        </SectionPanel>
      )}
      <ChangeDockQueuePriorityDialog
        open={Boolean(priorityEntry)}
        entry={priorityEntry}
        onOpenChange={(o) => { if (!o) setPriorityEntry(null) }}
        onChanged={() => { void queue.refetch() }}
      />
      {myUser && (
        <p className="text-[10px] text-slate-500">Sesión actual: {myUser}</p>
      )}
    </div>
  )
}
