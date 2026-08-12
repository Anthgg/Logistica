import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows, StatusPill } from './ui/Primitives'
import { CreateWarehouseDockBlackoutDialog } from './dialogs/OperationalDialogs'
import { formatServerDateTime, formatServerTime } from '../utils/format'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  WarehouseDockBlackout,
  WarehouseDockOperatingWindow,
  InboundDockAssignment,
  UnloadingOperation,
} from '../types/inbound-docks'

export function WarehouseDockOperatingWindowsPanel({
  windows,
  loading,
  error,
}: {
  windows: WarehouseDockOperatingWindow[] | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel title="Horarios operativos" description="Ventanas de atención del muelle">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Horarios operativos" description="Ventanas de atención del muelle">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!windows?.length) {
    return (
      <SectionPanel title="Horarios operativos" description="Ventanas de atención del muelle">
        <EmptyPanel title="Sin horarios" description="No hay horarios configurados para este muelle." />
      </SectionPanel>
    )
  }
  const DAY_LABEL = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
  return (
    <SectionPanel title="Horarios operativos" description="Ventanas de atención del muelle">
      <ul className="space-y-2 text-xs">
        {windows.map((w) => (
          <li key={w.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">
                {DAY_LABEL[w.day_of_week] ?? `Día ${w.day_of_week}`}
              </p>
              <StatusPill tone={w.is_active ? 'success' : 'muted'}>
                {w.is_active ? 'Activo' : 'Inactivo'}
              </StatusPill>
            </div>
            <p className="text-[11px] text-slate-600">Apertura: {w.opens_at}</p>
            <p className="text-[11px] text-slate-600">Cierre: {w.closes_at}</p>
            {w.effective_from && <p className="text-[10px] text-slate-500">Vigente desde: {w.effective_from}</p>}
            {w.effective_to && <p className="text-[10px] text-slate-500">Vigente hasta: {w.effective_to}</p>}
          </li>
        ))}
      </ul>
    </SectionPanel>
  )
}

export function WarehouseDockBlackoutsPanel({
  dockId,
  dockCode,
  blackouts,
  loading,
  error,
  onChanged,
}: {
  dockId: string | null
  dockCode: string
  blackouts: WarehouseDockBlackout[] | undefined
  loading: boolean
  error: string | null
  onChanged?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageBlackouts)
  const [open, setOpen] = useState(false)
  if (loading) {
    return (
      <SectionPanel title="Blackouts" description="Bloqueos programados del muelle">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Blackouts" description="Bloqueos programados del muelle">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!blackouts?.length) {
    return (
      <SectionPanel
        title="Blackouts"
        description="Bloqueos programados del muelle"
        actions={
          canCreate && dockId ? (
            <Button size="small" variant="primary" onClick={() => setOpen(true)}>
              Crear blackout
            </Button>
          ) : undefined
        }
      >
        <EmptyPanel title="Sin blackouts" description="No hay bloqueos programados para este muelle." />
        {dockId && (
          <CreateWarehouseDockBlackoutDialog
            open={open}
            dockId={dockId}
            dockCode={dockCode}
            onOpenChange={setOpen}
            onCreated={() => { onChanged?.() }}
          />
        )}
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Blackouts"
      description="Bloqueos programados del muelle"
      actions={
        canCreate && dockId ? (
          <Button size="small" variant="primary" onClick={() => setOpen(true)}>
            Crear blackout
          </Button>
        ) : undefined
      }
    >
      <ul className="space-y-2 text-xs">
        {blackouts.map((b) => (
          <li key={b.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">
                {formatServerTime(b.starts_at)} → {formatServerTime(b.ends_at)}
              </p>
              {b.affects_active_assignments ? (
                <StatusPill tone="warning">Afecta operación activa</StatusPill>
              ) : (
                <StatusPill tone="info">Sin afectación</StatusPill>
              )}
            </div>
            <p className="text-[11px] text-slate-600">Motivo: {b.reason}</p>
            <p className="text-[10px] text-slate-500">Creado por: {b.created_by_display}</p>
            <p className="text-[10px] text-slate-500">{formatServerDateTime(b.created_at)}</p>
          </li>
        ))}
      </ul>
      {dockId && (
        <CreateWarehouseDockBlackoutDialog
          open={open}
          dockId={dockId}
          dockCode={dockCode}
          onOpenChange={setOpen}
          onCreated={() => { onChanged?.() }}
        />
      )}
    </SectionPanel>
  )
}

export function InboundDockDailyCalendar({
  assignments,
  operations,
  loading,
  error,
  onSelectAssignment,
  onSelectOperation,
}: {
  assignments: InboundDockAssignment[] | undefined
  operations: UnloadingOperation[] | undefined
  loading: boolean
  error: string | null
  onSelectAssignment?: (id: string) => void
  onSelectOperation?: (id: string) => void
}) {
  if (loading) {
    return (
      <SectionPanel title="Calendario diario" description="Datos del backend, no se generan intervalos ficticios.">
        <SkeletonRows rows={4} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Calendario diario" description="Datos del backend, no se generan intervalos ficticios.">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  const items: Array<{
    key: string
    label: string
    detail: string
    at: string
    onClick?: () => void
    status?: string
  }> = []
  for (const a of assignments ?? []) {
    const at = a.assigned_at
    items.push({
      key: `assignment-${a.id}`,
      label: `Asignación ${a.dock_code}`,
      detail: `${a.cpv_code ?? '—'} · ${a.vehicle?.plate ?? '—'}`,
      at,
      onClick: onSelectAssignment ? () => onSelectAssignment(a.id) : undefined,
      status: a.status,
    })
  }
  for (const o of operations ?? []) {
    const at = o.started_at_server ?? o.started_at ?? o.created_at
    items.push({
      key: `operation-${o.id}`,
      label: `Operación ${o.dock_code}`,
      detail: `${o.cpv_code ?? '—'} · ${o.vehicle?.plate ?? '—'}`,
      at,
      onClick: onSelectOperation ? () => onSelectOperation(o.id) : undefined,
      status: o.status,
    })
  }
  if (!items.length) {
    return (
      <SectionPanel title="Calendario diario" description="Datos del backend, no se generan intervalos ficticios.">
        <EmptyPanel title="Sin eventos" description="No hay eventos registrados para el día seleccionado." />
      </SectionPanel>
    )
  }
  items.sort((a, b) => (a.at < b.at ? 1 : -1))
  return (
    <SectionPanel title="Calendario diario" description="Datos del backend, no se generan intervalos ficticios.">
      <ol className="space-y-2 text-xs">
        {items.map((item) => (
          <li
            key={item.key}
            className="flex flex-col gap-1 rounded-lg border border-slate-200 bg-white p-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">{item.label}</p>
              <p className="font-mono text-[11px] text-slate-500">{formatServerTime(item.at)}</p>
            </div>
            <p className="text-[11px] text-slate-600">{item.detail}</p>
            {item.status && <StatusPill tone="muted">{item.status}</StatusPill>}
            {item.onClick && (
              <Button size="small" variant="secondary" onClick={item.onClick} className="self-start">
                Ver detalle
              </Button>
            )}
          </li>
        ))}
      </ol>
    </SectionPanel>
  )
}
