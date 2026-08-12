import { useMemo, useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { PutawayPhaseNav } from '../components/PutawayPhaseNav'
import { PutawayContextEmptyState } from '../components/PutawayContextEmptyState'
import type { PutawayCapacityProjectionApi } from '../types/putaway-api'

function decimal(value: string | number): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function PutawayCapacityPage() {
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.putaway.viewCapacity)
  const organizationId = currentContext.organization_id
  const [draftWarehouseId, setDraftWarehouseId] = useState(currentContext.warehouse_id ?? '')
  const [draftLocationId, setDraftLocationId] = useState('')
  const [scope, setScope] = useState({ warehouseId: '', locationId: '' })

  const capacity = useQuery<PutawayCapacityProjectionApi[]>(
    ['putaway', 'capacity', organizationId, scope.warehouseId, scope.locationId],
    '/logistics/putaway/capacity/projections',
    scope.warehouseId && scope.locationId ? { warehouse_id: scope.warehouseId, location_id: scope.locationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(scope.warehouseId) && Boolean(scope.locationId) },
  )

  const totals = useMemo(() => (capacity.data ?? []).reduce((result, row) => ({
    maximum: result.maximum + decimal(row.maximum_value),
    occupied: result.occupied + decimal(row.operational_occupied_value),
    reserved: result.reserved + decimal(row.active_reserved_value),
    free: result.free + decimal(row.projected_free_value),
  }), { maximum: 0, occupied: 0, reserved: 0, free: 0 }), [capacity.data])

  if (!canView) return <div className="space-y-4"><PageHeader title="Capacidad de ubicación" /><Alert variant="error">No tienes permisos para ver las proyecciones de capacidad.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Planeamiento" title="Capacidad de ubicación" description="Consulta la ocupación, reservas y capacidad libre proyectada por posición." />
      <PutawayPhaseNav />
      {!organizationId && <PutawayContextEmptyState title="Selecciona la organización de capacidad" description="Las proyecciones dependen del almacén y la ubicación dentro del contexto operativo." />}

      {organizationId && (
        <>
          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="layers" size={21} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Alcance exacto</p><h2 className="mt-1 text-xl font-bold text-slate-950">Selecciona una posición</h2></div></div><p className="mt-3 text-sm leading-6 text-slate-500">El contrato real calcula perfiles para una ubicación concreta; no existe un resumen agregado por ID libre de almacén.</p><div className="mt-6 grid gap-4 sm:grid-cols-2"><label><span className="text-sm font-semibold text-slate-700">Almacén ID</span><input type="text" value={draftWarehouseId} onChange={(event) => setDraftWarehouseId(event.target.value)} placeholder="UUID del almacén" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label><label><span className="text-sm font-semibold text-slate-700">Ubicación ID</span><input type="text" value={draftLocationId} onChange={(event) => setDraftLocationId(event.target.value)} placeholder="UUID de la ubicación" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label></div><Button className="mt-5" onClick={() => setScope({ warehouseId: draftWarehouseId.trim(), locationId: draftLocationId.trim() })} disabled={!draftWarehouseId.trim() || !draftLocationId.trim()}>Consultar proyección</Button></div>
            <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Lectura operativa</p><h2 className="mt-2 text-xl font-bold">Capacidad no es saldo</h2><p className="mt-3 text-sm leading-6 text-slate-300">La proyección combina máximo, margen de seguridad, ocupación operacional y reservas activas. Se usa para recomendar destinos, no para editar inventario.</p><div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4"><p className="text-xs text-slate-400">Fórmula de referencia</p><p className="mt-2 font-mono text-xs text-sky-300">libre = máximo − margen − ocupado − reservado</p></div></aside>
          </section>

          {capacity.isLoading && <LoadingSkeleton rows={5} />}
          {capacity.isError && <Alert variant="error">{getErrorMessage(capacity.error)}</Alert>}

          {capacity.data && (
            <>
              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de capacidad">{([
                ['layers' as const, 'Capacidad máxima', totals.maximum, 'bg-blue-50 text-blue-700'],
                ['package' as const, 'Ocupación operativa', totals.occupied, 'bg-violet-50 text-violet-700'],
                ['lock' as const, 'Reservado', totals.reserved, 'bg-orange-50 text-orange-700'],
                ['check' as const, 'Libre proyectado', totals.free, totals.free > 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'],
              ] as const).map(([icon, label, value, color]) => <div key={label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-950">{value.toLocaleString('es-PE')}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${color}`}><LogisticsIcon name={icon} size={19} aria-hidden="true" /></span></div></div>)}</section>

              {capacity.data.length === 0 ? <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="archive" size={24} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-slate-950">Sin perfiles de capacidad</h2><p className="mt-2 text-sm text-slate-500">La ubicación existe en el alcance consultado, pero todavía no tiene perfiles proyectados.</p></div> : <section><div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Perfiles calculados</p><h2 className="mt-1 text-xl font-bold text-slate-950">Proyección por dimensión</h2></div><div className="grid gap-4 xl:grid-cols-2">{capacity.data.map((row) => { const max = decimal(row.maximum_value); const free = decimal(row.projected_free_value); const utilization = max > 0 ? Math.min(100, Math.max(0, Math.round(((max - free) / max) * 100))) : 0; return <article key={row.capacity_profile_id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><h3 className="font-bold text-slate-950">{row.capacity_type.replaceAll('_', ' ')}</h3><p className="mt-1 text-xs text-slate-500">Calidad: {row.data_quality_status}</p></div><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">{utilization}% usado</span></div><div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${utilization >= 90 ? 'bg-red-500' : utilization >= 70 ? 'bg-orange-500' : 'bg-blue-600'}`} style={{ width: `${utilization}%` }} /></div><dl className="mt-5 grid grid-cols-3 gap-3 text-center"><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Máximo</dt><dd className="mt-1 font-bold text-slate-950">{row.maximum_value}</dd></div><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Reservado</dt><dd className="mt-1 font-bold text-slate-950">{row.active_reserved_value}</dd></div><div className="rounded-2xl bg-emerald-50 p-3"><dt className="text-xs text-emerald-700">Libre</dt><dd className="mt-1 font-bold text-emerald-950">{row.projected_free_value}</dd></div></dl></article> })}</div></section>}
            </>
          )}
        </>
      )}
    </div>
  )
}
