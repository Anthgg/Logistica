import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { DockModal } from '../components/dialogs/DockModal'
import { DockOperationsServerClock } from '../components/ui/DockOperationsServerClock'
import { ErrorPanel, SkeletonRows, SectionPanel, StatusPill, KeyValueGrid } from '../components/ui/Primitives'
import {
  dockDirectionLabel,
  dockOperationalStatusLabel,
  dockOperationalStatusTone,
  dockStatusLabel,
  dockTypeLabel,
  formatServerTime,
} from '../utils/format'
import {
  useInboundDockAssignments,
  useWarehouseDock,
  useWarehouseDockAvailability,
  useWarehouseDockBlackouts,
  useWarehouseDockOperatingWindows,
} from '../hooks/useInboundDocksQueries'
import { WarehouseDocksBoard } from '../components/WarehouseDocksBoard'
import { WarehouseDockBlackoutsPanel, WarehouseDockOperatingWindowsPanel } from '../components/WarehouseDockSchedules'
import { useMutation, useQuery } from '../hooks/useQuery'
import { warehouseDocksApi } from '../api/warehouseDocksApi'
import { InboundDockDailyCalendar } from '../components/WarehouseDockSchedules'
import type { WarehouseDock } from '../types/inbound-docks'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function WarehouseDockDetailPage() {
  const { dockId } = useParams<{ dockId: string }>()
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageDocks)
  const dock = useWarehouseDock(dockId ?? null)
  const availability = useWarehouseDockAvailability(dockId ?? null)
  const blackouts = useWarehouseDockBlackouts(dockId ?? null)
  const windows = useWarehouseDockOperatingWindows(dockId ?? null)
  const assignments = useInboundDockAssignments(
    { dock_id: dockId ?? undefined },
    { refetchIntervalMs: 10_000 },
  )
  const operationsQuery = useQuery<{ items: Array<{ id: string; dock_id: string; cpv_code: string | null; vehicle: { plate: string | null } | null; status: string; started_at_server: string | null; started_at: string | null; created_at: string; server_time: string; warehouse_id: string; check_in_id: string; dock_code: string; supplier: { id: string; name: string; code: string | null } | null; carrier: { id: string; name: string; code: string | null } | null; alerts: string[] }> }>(
    ['dock-detail-operations', dockId],
    dockId ? `/logistics/inbound/unloading?dock_id=${dockId}` : '',
    undefined,
    { enabled: Boolean(dockId), refetchIntervalMs: 10_000 },
  )
  const [maintenanceOpen, setMaintenanceOpen] = useState(false)
  const [maintenanceReason, setMaintenanceReason] = useState('')
  const [maintenanceEnd, setMaintenanceEnd] = useState('')
  const [blockOpen, setBlockOpen] = useState(false)
  const [blockReason, setBlockReason] = useState('')
  const [editOpen, setEditOpen] = useState(false)
  const [confirmText, setConfirmText] = useState('')
  const maintenanceMutation = useMutation<{ id: string; reason: string; end: string }, WarehouseDock>(
    async ({ id, reason, end }) => warehouseDocksApi.setMaintenance(id, { reason, estimated_end: end || null }),
    { onSuccess: () => { setMaintenanceOpen(false); void dock.refetch(); void availability.refetch() } },
  )
  const endMaintenanceMutation = useMutation<{ id: string }, WarehouseDock>(
    async ({ id }) => warehouseDocksApi.endMaintenance(id),
    { onSuccess: () => { void dock.refetch(); void availability.refetch() } },
  )
  const blockMutation = useMutation<{ id: string; reason: string }, WarehouseDock>(
    async ({ id, reason }) => warehouseDocksApi.block(id, { reason }),
    { onSuccess: () => { setBlockOpen(false); void dock.refetch(); void availability.refetch() } },
  )
  const unblockMutation = useMutation<{ id: string }, WarehouseDock>(
    async ({ id }) => warehouseDocksApi.unblock(id),
    { onSuccess: () => { void dock.refetch(); void availability.refetch() } },
  )
  const activateMutation = useMutation<{ id: string }, WarehouseDock>(
    async ({ id }) => warehouseDocksApi.update(id, { name: dock.data?.name ?? '' }),
    { onSuccess: () => { void dock.refetch() } },
  )
  const deactivateMutation = useMutation<{ id: string }, WarehouseDock>(
    async ({ id }) => warehouseDocksApi.update(id, { name: dock.data?.name ?? '' }),
    { onSuccess: () => { void dock.refetch() } },
  )
  if (dock.isLoading) return <SkeletonRows rows={4} />
  if (dock.isError) return <ErrorPanel message={dock.error ?? 'No se pudo cargar el muelle.'} />
  const data = dock.data
  if (!data) {
    return (
      <div className="page">
        <PageHeader title="Detalle de muelle" />
        <ErrorPanel message="Muelle no encontrado" />
      </div>
    )
  }
  return (
    <div className="page">
      <PageHeader
        eyebrow={`Muelle ${data.code}`}
        title={data.name}
        description={`${data.warehouse_name} · ${dockTypeLabel(data.type)} · ${dockDirectionLabel(data.direction)}`}
        actions={
          <>
            <DockOperationsServerClock
              serverTimeIso={availability.data?.server_time ?? null}
              timezone={availability.data?.timezone ?? data.timezone ?? null}
            />
            <Button size="small" variant="secondary" onClick={() => navigate('/logistics/inbound/docks')}>
              Tablero
            </Button>
            {canManage && data.status === 'ACTIVE' && (
              <Button size="small" variant="secondary" onClick={() => setMaintenanceOpen(true)}>
                Mantenimiento
              </Button>
            )}
            {canManage && data.status === 'MAINTENANCE' && (
              <Button size="small" variant="secondary" onClick={() => endMaintenanceMutation.mutate({ id: data.id })}>
                Salir de mantenimiento
              </Button>
            )}
            {canManage && data.status !== 'BLOCKED' && (
              <Button size="small" variant="danger" onClick={() => setBlockOpen(true)}>
                Bloquear
              </Button>
            )}
            {canManage && data.status === 'BLOCKED' && (
              <Button size="small" variant="primary" onClick={() => unblockMutation.mutate({ id: data.id })}>
                Desbloquear
              </Button>
            )}
            {canManage && data.status === 'INACTIVE' && (
              <Button size="small" variant="primary" onClick={() => activateMutation.mutate({ id: data.id })}>
                Activar
              </Button>
            )}
            {canManage && data.status === 'ACTIVE' && (
              <Button size="small" variant="secondary" onClick={() => deactivateMutation.mutate({ id: data.id })}>
                Desactivar
              </Button>
            )}
            <Button size="small" variant="ghost" onClick={() => setEditOpen(true)}>
              Editar
            </Button>
          </>
        }
      />
      <SectionPanel
        title="Estado del muelle"
        description="El estado maestro y operativo lo calcula el backend."
        actions={
          <StatusPill tone={dockOperationalStatusTone(data.operational_status)}>
            {dockOperationalStatusLabel(data.operational_status)}
          </StatusPill>
        }
      >
        <KeyValueGrid
          items={[
            { label: 'Estado maestro', value: dockStatusLabel(data.status) },
            { label: 'Estado operativo', value: dockOperationalStatusLabel(data.operational_status) },
            { label: 'Dirección', value: dockDirectionLabel(data.direction) },
            { label: 'Tipo', value: dockTypeLabel(data.type) },
            { label: 'Zona', value: data.zone ?? '—' },
            { label: 'Dirección física', value: data.address ?? '—' },
            { label: 'Zona horaria', value: data.timezone ?? '—' },
            { label: 'Asignación activa', value: data.active_assignment_id ?? '—' },
            { label: 'Placa activa', value: data.active_assignment_vehicle_plate ?? '—', mono: true },
            { label: 'Ocupado desde', value: data.occupied_since ? formatServerTime(data.occupied_since) : '—' },
            { label: 'Próxima asignación', value: data.next_scheduled_assignment_id ?? '—' },
          ]}
        />
        {data.notes && (
          <p className="mt-2 text-[11px] text-slate-600">Notas: {data.notes}</p>
        )}
      </SectionPanel>
      <SectionPanel
        title="Disponibilidad"
        description="Próxima disponibilidad y blackouts"
      >
        {availability.isLoading ? (
          <SkeletonRows rows={3} />
        ) : availability.data ? (
          <KeyValueGrid
            items={[
              { label: 'Disponible', value: availability.data.is_available ? 'Sí' : 'No' },
              { label: 'Estado operativo', value: dockOperationalStatusLabel(availability.data.operational_status) },
              { label: 'Próxima disponibilidad', value: availability.data.next_available_from ? formatServerTime(availability.data.next_available_from) : '—' },
              { label: 'Asignación activa', value: availability.data.active_assignment_id ?? '—' },
            ]}
          />
        ) : (
          <p className="text-xs text-slate-500">Sin datos de disponibilidad.</p>
        )}
      </SectionPanel>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <WarehouseDockOperatingWindowsPanel windows={windows.data} loading={windows.isLoading} error={windows.error} />
        <WarehouseDockBlackoutsPanel
          dockId={data.id}
          dockCode={data.code}
          blackouts={blackouts.data}
          loading={blackouts.isLoading}
          error={blackouts.error}
          onChanged={() => { void blackouts.refetch() }}
        />
      </div>
      <WarehouseDocksBoard
        docks={[{
          id: data.id,
          code: data.code,
          name: data.name,
          warehouse_id: data.warehouse_id,
          warehouse_name: data.warehouse_name,
          type: data.type,
          direction: data.direction,
          status: data.status,
          operational_status: data.operational_status,
          active_assignment_id: data.active_assignment_id,
          active_assignment_vehicle_plate: data.active_assignment_vehicle_plate,
          occupied_since: data.occupied_since,
        }]}
      />
      <SectionPanel
        title="Asignaciones recientes"
        description="Listado limitado a este muelle."
      >
        {assignments.isLoading ? (
          <SkeletonRows rows={3} />
        ) : (
          <ul className="space-y-2 text-xs">
            {(assignments.data?.items ?? []).map((a) => (
              <li key={a.id} className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono">{a.cpv_code ?? '—'} · {a.vehicle?.plate ?? '—'}</span>
                  <StatusPill tone="info">{a.status}</StatusPill>
                </div>
                <p className="text-[11px] text-slate-500">Asignado: {a.assigned_at ?? '—'}</p>
                <Button
                  size="small"
                  variant="secondary"
                  className="mt-2"
                  onClick={() => navigate(`/logistics/inbound/dock-assignments/${a.id}`)}
                >
                  Ver asignación
                </Button>
              </li>
            ))}
            {(assignments.data?.items ?? []).length === 0 && (
              <li className="rounded-md border border-dashed border-slate-200 bg-white p-3 text-[11px] text-slate-400">
                Sin asignaciones recientes.
              </li>
            )}
          </ul>
        )}
      </SectionPanel>
      <InboundDockDailyCalendar
        assignments={assignments.data?.items}
        operations={operationsQuery.data?.items as never}
        loading={assignments.isLoading || operationsQuery.isLoading}
        error={assignments.error ?? operationsQuery.error}
        onSelectAssignment={(id) => navigate(`/logistics/inbound/dock-assignments/${id}`)}
        onSelectOperation={(id) => navigate(`/logistics/inbound/unloading/${id}`)}
      />
      <DockModal
        open={maintenanceOpen}
        onOpenChange={setMaintenanceOpen}
        title="Programar mantenimiento"
        description="Esta acción puede requerir step-up."
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setMaintenanceOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={() => maintenanceMutation.mutate({ id: data.id, reason: maintenanceReason, end: maintenanceEnd })}
              isLoading={maintenanceMutation.isPending}
              disabled={!maintenanceReason.trim()}
            >
              Programar
            </Button>
          </>
        }
      >
        <div className="space-y-2 text-xs">
          <label className="block text-[11px] font-semibold text-slate-600" htmlFor="mt-reason">Motivo</label>
          <input
            id="mt-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={maintenanceReason}
            onChange={(event) => setMaintenanceReason(event.target.value)}
          />
          <label className="block text-[11px] font-semibold text-slate-600" htmlFor="mt-end">Fin estimado (ISO)</label>
          <input
            id="mt-end"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={maintenanceEnd}
            onChange={(event) => setMaintenanceEnd(event.target.value)}
          />
        </div>
      </DockModal>
      <DockModal
        open={blockOpen}
        onOpenChange={setBlockOpen}
        title="Bloquear muelle"
        description="Bloquear puede requerir step-up. Confirma escribiendo BLOQUEAR."
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setBlockOpen(false)}>
              Cancelar
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={() => blockMutation.mutate({ id: data.id, reason: blockReason })}
              isLoading={blockMutation.isPending}
              disabled={confirmText !== 'BLOQUEAR'}
            >
              Bloquear
            </Button>
          </>
        }
      >
        <div className="space-y-2 text-xs">
          <label className="block text-[11px] font-semibold text-slate-600" htmlFor="block-reason">Motivo</label>
          <input
            id="block-reason"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={blockReason}
            onChange={(event) => setBlockReason(event.target.value)}
          />
          <label className="block text-[11px] font-semibold text-slate-600" htmlFor="block-confirm">Confirmación</label>
          <input
            id="block-confirm"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={confirmText}
            onChange={(event) => setConfirmText(event.target.value)}
            placeholder="Escribe BLOQUEAR"
          />
        </div>
      </DockModal>
      <DockModal
        open={editOpen}
        onOpenChange={setEditOpen}
        title="Editar muelle"
        description="Los cambios se enviarán al backend."
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setEditOpen(false)}>
              Cerrar
            </Button>
          </>
        }
      >
        <p className="text-xs text-slate-600">
          La edición de muelle se realiza en la página de Configuración. Esta pantalla es de solo lectura operativa.
        </p>
        <Button size="small" variant="primary" className="mt-3" onClick={() => { setEditOpen(false); navigate('/logistics/inbound/docks/settings') }}>
          Ir a Configuración
        </Button>
      </DockModal>
    </div>
  )
}
