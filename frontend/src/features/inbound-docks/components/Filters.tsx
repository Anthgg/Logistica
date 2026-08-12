import { useEffect, useMemo, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { SectionPanel } from './ui/Primitives'
import type {
  InboundDockPriority,
  InboundDockQueueStatus,
  WarehouseDockOperationalStatus,
  WarehouseDockStatus,
} from '../types/inbound-docks'

export interface QueueFilter {
  warehouse_id?: string
  dock_id?: string
  status?: InboundDockQueueStatus
  priority?: InboundDockPriority
  supplier_id?: string
  carrier_id?: string
  search?: string
  date_from?: string
  date_to?: string
  with_anomalies?: boolean
  with_reassignment?: boolean
}

export interface AssignmentFilter {
  warehouse_id?: string
  dock_id?: string
  status?: string
  supplier_id?: string
  carrier_id?: string
  date_from?: string
  date_to?: string
}

export interface DockFilter {
  warehouse_id?: string
  status?: WarehouseDockStatus
  operational_status?: WarehouseDockOperationalStatus
  search?: string
}

const DEBOUNCE_MS = 350

function useDebouncedValue<T>(value: T): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), DEBOUNCE_MS)
    return () => window.clearTimeout(id)
  }, [value])
  return debounced
}

export function DockQueueFilters({
  value,
  onChange,
  warehouses,
  docks,
  showMine = false,
  onMineChange,
  myAssignmentsOnly = false,
}: {
  value: QueueFilter
  onChange: (next: QueueFilter) => void
  warehouses: Array<{ id: string; label: string }>
  docks?: Array<{ id: string; label: string }>
  showMine?: boolean
  onMineChange?: (next: boolean) => void
  myAssignmentsOnly?: boolean
}) {
  const [local, setLocal] = useState<QueueFilter>(value)
  const debounced = useDebouncedValue(local)
  useEffect(() => {
    onChange(debounced)
  }, [debounced, onChange])
  useEffect(() => {
    setLocal(value)
  }, [value])
  return (
    <SectionPanel
      title="Filtros"
      description="Los filtros afectan la consulta al backend. No se buscan archivos locales."
    >
      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-warehouse">Almacén</label>
          <select
            id="filter-warehouse"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.warehouse_id ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, warehouse_id: event.target.value || undefined }))}
          >
            <option value="">Todos</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.label}</option>
            ))}
          </select>
        </div>
        {docks && (
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-dock">Muelle</label>
            <select
              id="filter-dock"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={local.dock_id ?? ''}
              onChange={(event) => setLocal((prev) => ({ ...prev, dock_id: event.target.value || undefined }))}
            >
              <option value="">Todos</option>
              {docks.map((d) => (
                <option key={d.id} value={d.id}>{d.label}</option>
              ))}
            </select>
          </div>
        )}
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-status">Estado</label>
          <select
            id="filter-status"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.status ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, status: (event.target.value || undefined) as InboundDockQueueStatus | undefined }))}
          >
            <option value="">Todos</option>
            <option value="WAITING">Esperando</option>
            <option value="ASSIGNED">Asignado</option>
            <option value="IN_MOVEMENT">En movimiento</option>
            <option value="AT_DOCK">En muelle</option>
            <option value="READY">Listo</option>
            <option value="UNLOADING">Descargando</option>
            <option value="PAUSED">Pausada</option>
            <option value="COMPLETED">Completada</option>
            <option value="PENDING_RELEASE">Pendiente de liberar</option>
            <option value="RELEASED">Liberada</option>
            <option value="HELD">Retenida</option>
            <option value="CANCELLED">Cancelada</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-priority">Prioridad</label>
          <select
            id="filter-priority"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.priority ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, priority: (event.target.value || undefined) as InboundDockPriority | undefined }))}
          >
            <option value="">Todas</option>
            <option value="LOW">Baja</option>
            <option value="NORMAL">Normal</option>
            <option value="HIGH">Alta</option>
            <option value="URGENT">Urgente</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-search">Búsqueda</label>
          <input
            id="filter-search"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.search ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, search: event.target.value || undefined }))}
            placeholder="CPV, CIT, OC, proveedor, transportista, placa, vehículo, muelle, responsable"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-from">Desde</label>
          <input
            id="filter-from"
            type="date"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.date_from ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, date_from: event.target.value || undefined }))}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="filter-to">Hasta</label>
          <input
            id="filter-to"
            type="date"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.date_to ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, date_to: event.target.value || undefined }))}
          />
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={Boolean(local.with_anomalies)}
              onChange={(event) => setLocal((prev) => ({ ...prev, with_anomalies: event.target.checked || undefined }))}
            />
            Con anomalías
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={Boolean(local.with_reassignment)}
              onChange={(event) => setLocal((prev) => ({ ...prev, with_reassignment: event.target.checked || undefined }))}
            />
            Con reasignación
          </label>
        </div>
        {showMine && (
          <div className="flex items-center">
            <label className="flex items-center gap-2 text-xs text-slate-700">
              <input
                type="checkbox"
                className="h-3.5 w-3.5"
                checked={myAssignmentsOnly}
                onChange={(event) => onMineChange?.(event.target.checked)}
              />
              Mis operaciones
            </label>
          </div>
        )}
      </div>
      <div className="mt-3 flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={() => setLocal({})}>
          Limpiar
        </Button>
      </div>
    </SectionPanel>
  )
}

export function DockFiltersPanel({
  value,
  onChange,
  warehouses,
}: {
  value: DockFilter
  onChange: (next: DockFilter) => void
  warehouses: Array<{ id: string; label: string }>
}) {
  const [local, setLocal] = useState<DockFilter>(value)
  const debounced = useDebouncedValue(local)
  useEffect(() => {
    onChange(debounced)
  }, [debounced, onChange])
  useEffect(() => {
    setLocal(value)
  }, [value])
  const statusOptions = useMemo<Array<{ value: WarehouseDockStatus; label: string }>>(
    () => [
      { value: 'ACTIVE', label: 'Activo' },
      { value: 'INACTIVE', label: 'Inactivo' },
      { value: 'BLOCKED', label: 'Bloqueado' },
      { value: 'MAINTENANCE', label: 'Mantenimiento' },
      { value: 'ARCHIVED', label: 'Archivado' },
    ],
    [],
  )
  const opOptions = useMemo<Array<{ value: WarehouseDockOperationalStatus; label: string }>>(
    () => [
      { value: 'AVAILABLE', label: 'Disponible' },
      { value: 'RESERVED', label: 'Reservado' },
      { value: 'OCCUPIED', label: 'Ocupado' },
      { value: 'UNLOADING', label: 'Descargando' },
      { value: 'PENDING_RELEASE', label: 'Pendiente de liberar' },
      { value: 'BLOCKED', label: 'Bloqueado' },
      { value: 'MAINTENANCE', label: 'Mantenimiento' },
      { value: 'INACTIVE', label: 'Inactivo' },
    ],
    [],
  )
  return (
    <SectionPanel
      title="Filtros de muelles"
      description="Los filtros consultan al backend. No se calculan compatibilidades locales."
    >
      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-filter-warehouse">Almacén</label>
          <select
            id="dock-filter-warehouse"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.warehouse_id ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, warehouse_id: event.target.value || undefined }))}
          >
            <option value="">Todos</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-filter-status">Estado</label>
          <select
            id="dock-filter-status"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.status ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, status: (event.target.value || undefined) as WarehouseDockStatus | undefined }))}
          >
            <option value="">Todos</option>
            {statusOptions.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-filter-op">Estado operativo</label>
          <select
            id="dock-filter-op"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.operational_status ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, operational_status: (event.target.value || undefined) as WarehouseDockOperationalStatus | undefined }))}
          >
            <option value="">Todos</option>
            {opOptions.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-filter-search">Búsqueda</label>
          <input
            id="dock-filter-search"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={local.search ?? ''}
            onChange={(event) => setLocal((prev) => ({ ...prev, search: event.target.value || undefined }))}
            placeholder="Código, nombre, dirección"
          />
        </div>
      </div>
    </SectionPanel>
  )
}
