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
import type { QuarantineZoneApi } from '../types/phase042-api'

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLocaleLowerCase('es-PE')
}

export function QuarantineZonesPage() {
  const { currentContext } = useLogisticsAccess()
  const warehouseId = currentContext.warehouse_id
  const [search, setSearch] = useState('')

  const zones = useQuery<QuarantineZoneApi[]>(
    ['quality-quarantine', 'zones', warehouseId],
    '/logistics/quarantine-zones',
    warehouseId ? { warehouse_id: warehouseId } : undefined,
    { enabled: Boolean(warehouseId) },
  )

  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('es-PE')
    if (!term) return zones.data ?? []
    return (zones.data ?? []).filter((row) => [row.code, row.name, row.status, row.warehouse_location_id].filter(Boolean).some((value) => String(value).toLocaleLowerCase('es-PE').includes(term)))
  }, [search, zones.data])

  const activeCount = (zones.data ?? []).filter((row) => row.status === 'ACTIVE').length
  const hazardousCount = (zones.data ?? []).filter((row) => row.hazardous_declared_capable).length

  return (
    <div className="space-y-6 pb-10">
      <PageHeader eyebrow="Fase 042 · Segregación física" title="Zonas de cuarentena" description="Revisa las posiciones autorizadas, capacidades declaradas y condiciones especiales del almacén." />
      <QualityQuarantinePhaseNav />

      {!warehouseId && <QualityQuarantineContextEmptyState title="Selecciona el almacén de las zonas" />}

      {warehouseId && (
        <>
          <section className="grid gap-4 sm:grid-cols-3" aria-label="Resumen de zonas">
            {([
              ['location' as const, 'Zonas activas', activeCount, 'bg-blue-50 text-blue-700'],
              ['layers' as const, 'Zonas configuradas', (zones.data ?? []).length, 'bg-violet-50 text-violet-700'],
              ['alert' as const, 'Aptas para peligrosos', hazardousCount, 'bg-orange-50 text-orange-700'],
            ] as const).map(([icon, title, value, tone]) => <article key={title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between gap-4"><div><p className="text-sm text-slate-500">{title}</p><p className="mt-2 text-3xl font-bold text-slate-950">{value}</p></div><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${tone}`}><LogisticsIcon name={icon} size={20} aria-hidden="true" /></span></div></article>)}
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end"><Input label="Buscar zona" placeholder="Código, nombre, estado o instrucción…" value={search} onChange={(event) => setSearch(event.target.value)} /><div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600"><span className="font-bold text-slate-950">{filtered.length}</span> zona(s) visibles</div></div></section>

          {zones.isLoading && <LoadingSkeleton rows={6} />}
          {zones.isError && <Alert variant="error">{getErrorMessage(zones.error)}</Alert>}

          {!zones.isLoading && !zones.isError && filtered.length === 0 && <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="location" size={24} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-slate-950">Sin zonas configuradas</h2><p className="mt-2 text-sm text-slate-500">El almacén aún no tiene configuraciones de cuarentena que coincidan con la búsqueda.</p></section>}

          {filtered.length > 0 && <section className="grid gap-4 xl:grid-cols-2">{filtered.map((row) => <article key={row.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-xs font-bold text-blue-700">{row.code}</p><h2 className="mt-2 text-lg font-bold text-slate-950">{row.name}</h2><p className="mt-1 text-xs text-slate-500">Ubicación {row.warehouse_location_id}</p></div><span className={`rounded-full px-3 py-1 text-xs font-bold ring-1 ${row.status === 'ACTIVE' ? 'bg-emerald-50 text-emerald-700 ring-emerald-100' : 'bg-slate-100 text-slate-700 ring-slate-200'}`}>{humanize(row.status)}</span></div><dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3"><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Prioridad</dt><dd className="mt-1 font-bold text-slate-950">{row.priority}</dd></div><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Almacén</dt><dd className="mt-1 truncate font-mono text-xs font-bold text-slate-950">{row.warehouse_id}</dd></div><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Peligrosos</dt><dd className="mt-1 font-bold text-slate-950">{row.hazardous_declared_capable ? 'Sí' : 'No'}</dd></div></dl></article>)}</section>}

          <Alert variant="info">El backend actual expone consulta y creación de zonas, pero no publica acciones de activar, bloquear o archivar; esta vista no simula esas mutaciones.</Alert>
        </>
      )}
    </div>
  )
}
