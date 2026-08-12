import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { putawayOrdersApi } from '../api/putawayOrdersApi'
import { PutawayPhaseNav } from '../components/PutawayPhaseNav'
import { PutawayContextEmptyState } from '../components/PutawayContextEmptyState'
import type { PutawayOrderApi } from '../types/putaway-api'

const SOURCES = [
  ['QUALITY_RELEASE', 'Liberación de calidad'], ['DIRECT_RELEASE', 'Liberación directa'],
  ['MANUAL_AUTHORIZED', 'Manual autorizada'], ['BATCH_RELEASE', 'Liberación por lote'],
  ['LEGACY_IMPORT', 'Importación heredada'],
] as const

export function CreatePutawayOrderPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.putaway.createOrder)
  const organizationId = currentContext.organization_id
  const [warehouseId, setWarehouseId] = useState(currentContext.warehouse_id ?? '')
  const [sourceType, setSourceType] = useState('QUALITY_RELEASE')
  const [priority, setPriority] = useState(0)

  const createOrder = useMutation<void, PutawayOrderApi>(
    () => putawayOrdersApi.createOrder({ warehouse_id: warehouseId.trim(), source_type: sourceType, priority }) as Promise<PutawayOrderApi>,
    { onSuccess: (result) => navigate(`/logistics/putaway/orders/${result.id}`) },
  )

  if (!canCreate) return <div className="space-y-4"><PageHeader title="Nueva orden de ubicación" /><Alert variant="error">No tienes permisos para crear órdenes de ubicación.</Alert></div>

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 043 · Orquestación" title="Nueva orden de ubicación" description="Crea el contenedor de trabajo; las tareas y recomendaciones se generan mediante el flujo autorizado." actions={<Button variant="secondary" onClick={() => navigate('/logistics/putaway/orders')}>Volver</Button>} />
      <PutawayPhaseNav />
      {!organizationId && <PutawayContextEmptyState title="Selecciona la organización de la orden" description="El almacén y las asignaciones se validan dentro del contexto operativo." />}
      {organizationId && (
        <section className="grid gap-6 lg:grid-cols-[1fr_0.65fr]">
          <form onSubmit={(event) => { event.preventDefault(); createOrder.mutate(undefined) }} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
            <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="package" size={21} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Datos de origen</p><h2 className="mt-1 text-xl font-bold text-slate-950">Define el alcance de trabajo</h2></div></div>
            <div className="mt-6 space-y-5"><label className="block"><span className="text-sm font-semibold text-slate-700">Almacén ID</span><input required type="text" value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)} placeholder="UUID del almacén" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label><label className="block"><span className="text-sm font-semibold text-slate-700">Fuente autorizada</span><select value={sourceType} onChange={(event) => setSourceType(event.target.value)} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50">{SOURCES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="block"><span className="text-sm font-semibold text-slate-700">Prioridad técnica</span><input type="number" min="0" value={priority} onChange={(event) => setPriority(Math.max(0, Number(event.target.value) || 0))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /><span className="mt-2 block text-xs text-slate-500">Un valor mayor coloca la orden antes en la cola.</span></label></div>
            {createOrder.error && <p className="mt-4 text-sm text-red-600" role="alert">{createOrder.error}</p>}
            <div className="mt-7 flex justify-end gap-3"><Button type="button" variant="secondary" onClick={() => navigate('/logistics/putaway/orders')}>Cancelar</Button><Button type="submit" isLoading={createOrder.isPending} loadingLabel="Creando…" disabled={!warehouseId.trim()}>Crear orden</Button></div>
          </form>
          <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Contrato real</p><h2 className="mt-2 text-xl font-bold">La orden no recibe líneas desde React</h2><p className="mt-3 text-sm leading-6 text-slate-300">El backend acepta almacén, fuente y prioridad. Las asignaciones, cantidades base y recomendaciones se construyen en servicios de dominio.</p><div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-slate-300">Esto evita inventar productos, cantidades o ubicaciones sin una liberación operativa verificable.</div></aside>
        </section>
      )}
    </div>
  )
}
