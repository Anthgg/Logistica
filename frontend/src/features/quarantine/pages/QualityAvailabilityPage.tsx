import { useMemo, useState } from 'react'
import { Alert } from '../../../components/common/Alert'
import { Input } from '../../../components/common/Input'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { QualityQuarantineContextEmptyState } from '../components/QualityQuarantineContextEmptyState'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { QualityAvailabilityApi } from '../types/phase042-api'

const CLASSES = ['ALL', 'AVAILABLE_FOR_PUTAWAY', 'BLOCKED_QUARANTINE', 'REJECTED_NOT_AVAILABLE', 'PENDING_EVALUATION', 'PARTIAL_RELEASE'] as const

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLocaleLowerCase('es-PE')
}

function classTone(value: string): string {
  if (value === 'AVAILABLE_FOR_PUTAWAY') return 'bg-emerald-50 text-emerald-700 ring-emerald-100'
  if (value === 'REJECTED_NOT_AVAILABLE') return 'bg-red-50 text-red-700 ring-red-100'
  if (value === 'BLOCKED_QUARANTINE') return 'bg-orange-50 text-orange-700 ring-orange-100'
  return 'bg-blue-50 text-blue-700 ring-blue-100'
}

export function QualityAvailabilityPage() {
  const { currentContext } = useLogisticsAccess()
  const warehouseId = currentContext.warehouse_id
  const [filter, setFilter] = useState<(typeof CLASSES)[number]>('ALL')
  const [search, setSearch] = useState('')

  const availability = useQuery<QualityAvailabilityApi[]>(
    ['quality-quarantine', 'availability', warehouseId],
    '/logistics/quality-availability',
    warehouseId ? { warehouse_id: warehouseId } : undefined,
    { enabled: Boolean(warehouseId) },
  )

  const summary = useMemo(() => {
    const rows = availability.data ?? []
    return {
      total: rows.length,
      available: rows.filter((row) => row.availability_class === 'AVAILABLE_FOR_PUTAWAY').length,
      blocked: rows.filter((row) => row.availability_class === 'BLOCKED_QUARANTINE').length,
      rejected: rows.filter((row) => row.availability_class === 'REJECTED_NOT_AVAILABLE').length,
    }
  }, [availability.data])

  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('es-PE')
    return (availability.data ?? []).filter((row) => {
      if (filter !== 'ALL' && row.availability_class !== filter) return false
      if (!term) return true
      return [row.product_id, row.allocation_id, row.quarantine_case_id, row.inspection_id, row.decision_id].filter(Boolean).some((value) => String(value).toLocaleLowerCase('es-PE').includes(term))
    })
  }, [availability.data, filter, search])

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 042 · Proyección operativa" title="Disponibilidad de calidad" description="Distingue inventario liberado, bloqueado, rechazado o pendiente antes de su ubicación." />
      <QualityQuarantinePhaseNav />

      {!warehouseId && <QualityQuarantineContextEmptyState title="Selecciona el almacén de la disponibilidad" />}

      {warehouseId && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de disponibilidad">
            {([
              ['layers' as const, 'Asignaciones', summary.total, 'bg-blue-50 text-blue-700'],
              ['check' as const, 'Para ubicación', summary.available, 'bg-emerald-50 text-emerald-700'],
              ['lock' as const, 'Bloqueadas', summary.blocked, 'bg-orange-50 text-orange-700'],
              ['x' as const, 'Rechazadas', summary.rejected, 'bg-red-50 text-red-700'],
            ] as const).map(([icon, title, value, tone]) => <article key={title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between gap-4"><div><p className="text-sm text-slate-500">{title}</p><p className="mt-2 text-3xl font-bold text-slate-950">{value}</p></div><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${tone}`}><LogisticsIcon name={icon} size={20} aria-hidden="true" /></span></div></article>)}
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm md:p-6"><div className="grid gap-4 xl:grid-cols-[1fr_auto] xl:items-end"><Input label="Buscar asignación" placeholder="Producto, recepción, caso o inspección…" value={search} onChange={(event) => setSearch(event.target.value)} /><div><p className="mb-2 text-sm font-semibold text-slate-700">Clase</p><div className="flex max-w-full gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1">{CLASSES.map((item) => <button key={item} type="button" onClick={() => setFilter(item)} className={`min-h-10 whitespace-nowrap rounded-xl px-3 text-xs font-semibold transition ${filter === item ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-600 hover:text-slate-950'}`}>{item === 'ALL' ? 'Todas' : humanize(item)}</button>)}</div></div></div></section>

          {availability.isLoading && <LoadingSkeleton rows={8} />}
          {availability.isError && <Alert variant="error">{getErrorMessage(availability.error)}</Alert>}

          {!availability.isLoading && !availability.isError && filtered.length === 0 && <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="package" size={24} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-slate-950">Sin proyecciones para este filtro</h2><p className="mt-2 text-sm text-slate-500">La proyección se genera desde las asignaciones de recepción del almacén.</p></section>}

          {filtered.length > 0 && <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-4">Producto / asignación</th><th className="px-5 py-4">Cantidad</th><th className="px-5 py-4">Clase</th><th className="px-5 py-4">Calidad</th><th className="px-5 py-4">Referencias</th></tr></thead><tbody className="divide-y divide-slate-100">{filtered.map((row) => <tr key={row.allocation_id} className="align-top transition hover:bg-slate-50"><td className="px-5 py-4"><p className="font-mono text-xs font-bold text-blue-700">{row.product_id}</p><p className="mt-1 font-mono text-xs text-slate-400">{row.allocation_id}</p></td><td className="px-5 py-4"><p className="font-bold text-slate-950">{row.quantity}</p><p className="mt-1 text-xs text-slate-500">Base: {row.base_quantity}</p></td><td className="px-5 py-4"><span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ring-1 ${classTone(row.availability_class)}`}>{humanize(row.availability_class)}</span></td><td className="px-5 py-4"><p className="font-semibold text-slate-800">{humanize(row.quality_status)}</p><p className="mt-1 text-xs text-slate-500">Unidad: {row.unit_id}</p></td><td className="px-5 py-4 text-xs text-slate-600"><p>Caso: {row.quarantine_case_id ?? '—'}</p><p className="mt-1">Inspección: {row.inspection_id ?? '—'}</p><p className="mt-1">Decisión: {row.decision_id ?? '—'}</p></td></tr>)}</tbody></table></div></section>}

          <Alert variant="info">El resumen se calcula en el cliente sobre la lista real del almacén; el backend no publica un endpoint `/summary` para esta proyección.</Alert>
        </>
      )}
    </div>
  )
}
