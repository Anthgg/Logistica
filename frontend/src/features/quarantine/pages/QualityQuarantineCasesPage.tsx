import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { QualityQuarantineContextEmptyState } from '../components/QualityQuarantineContextEmptyState'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { QualityQuarantineCaseSummaryApi } from '../types/phase042-api'

const STATUS_FILTERS = ['ALL', 'DRAFT', 'ACTIVE', 'UNDER_INSPECTION', 'DECISION_PENDING', 'RELEASED', 'REJECTED', 'CLOSED'] as const

function humanize(value: string): string {
  return value.replaceAll('_', ' ').toLocaleLowerCase('es-PE')
}

function statusTone(status: string): string {
  if (['RELEASED', 'CLOSED', 'APPROVED'].includes(status)) return 'bg-emerald-50 text-emerald-700 ring-emerald-100'
  if (['REJECTED', 'CANCELLED'].includes(status)) return 'bg-red-50 text-red-700 ring-red-100'
  if (status.includes('PENDING') || status === 'DRAFT') return 'bg-orange-50 text-orange-700 ring-orange-100'
  return 'bg-blue-50 text-blue-700 ring-blue-100'
}

export function QualityQuarantineCasesPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const warehouseId = currentContext.warehouse_id
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.quarantine.createQuarantine)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<(typeof STATUS_FILTERS)[number]>('ALL')

  const cases = useQuery<QualityQuarantineCaseSummaryApi[]>(
    ['quality-quarantine', 'cases', warehouseId],
    '/logistics/quality-quarantine-cases',
    warehouseId ? { warehouse_id: warehouseId } : undefined,
    { enabled: Boolean(warehouseId) },
  )

  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('es-PE')
    return (cases.data ?? []).filter((row) => {
      if (status !== 'ALL' && row.status !== status) return false
      if (!term) return true
      return [row.quarantine_code, row.status, row.severity, row.quality_result, row.release_status]
        .filter(Boolean)
        .some((value) => String(value).toLocaleLowerCase('es-PE').includes(term))
    })
  }, [cases.data, search, status])

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 042 · Expedientes"
        title="Casos de cuarentena"
        description="Consulta cada expediente, su inspección activa, la decisión de calidad y el estado de liberación."
        actions={canCreate ? <Button size="small" onClick={() => navigate('/logistics/quality/quarantine/new')}>Crear caso</Button> : undefined}
      />
      <QualityQuarantinePhaseNav />

      {!warehouseId && <QualityQuarantineContextEmptyState title="Selecciona el almacén de los casos" />}

      {warehouseId && (
        <>
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm md:p-6">
            <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
              <Input label="Buscar expediente" placeholder="Código, motivo, producto o recepción…" value={search} onChange={(event) => setSearch(event.target.value)} />
              <div><p className="mb-2 text-sm font-semibold text-slate-700">Estado</p><div className="flex max-w-full gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1">{STATUS_FILTERS.map((item) => <button key={item} type="button" onClick={() => setStatus(item)} className={`min-h-10 whitespace-nowrap rounded-xl px-3 text-xs font-semibold transition ${status === item ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-600 hover:text-slate-950'}`}>{item === 'ALL' ? 'Todos' : humanize(item)}</button>)}</div></div>
            </div>
          </section>

          {cases.isLoading && <LoadingSkeleton rows={8} />}
          {cases.isError && <Alert variant="error">{getErrorMessage(cases.error)}</Alert>}

          {!cases.isLoading && !cases.isError && filtered.length === 0 && (
            <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="archive" size={24} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-slate-950">No hay casos para este filtro</h2><p className="mt-2 text-sm text-slate-500">Prueba otro estado o limpia la búsqueda. El backend consulta por almacén y devuelve una lista directa.</p>{canCreate && <Button className="mt-6" onClick={() => navigate('/logistics/quality/quarantine/new')}>Crear caso</Button>}</section>
          )}

          {filtered.length > 0 && (
            <section className="grid gap-4 xl:grid-cols-2">
              {filtered.map((row) => (
                <article key={row.id} className="group rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md">
                  <div className="flex items-start justify-between gap-4"><div className="min-w-0"><p className="font-mono text-xs font-bold text-blue-700">{row.quarantine_code}</p><h2 className="mt-2 truncate text-lg font-bold text-slate-950">Expediente de cuarentena</h2><p className="mt-1 text-sm text-slate-500">Resultado: {row.quality_result ? humanize(row.quality_result) : 'pendiente'}</p></div><span className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold ring-1 ${statusTone(row.status)}`}>{humanize(row.status)}</span></div>
                  <dl className="mt-5 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3"><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Severidad</dt><dd className="mt-1 font-semibold text-slate-950">{humanize(row.severity)}</dd></div><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Calidad</dt><dd className="mt-1 font-semibold text-slate-950">{row.quality_result ? humanize(row.quality_result) : 'Sin resultado'}</dd></div><div className="rounded-2xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">Liberación</dt><dd className="mt-1 truncate font-semibold text-slate-950">{humanize(row.release_status)}</dd></div></dl>
                  <div className="mt-5 flex justify-end border-t border-slate-100 pt-4"><Button size="small" variant="ghost" onClick={() => navigate(`/logistics/quality/quarantine/${row.id}`)}>Abrir expediente</Button></div>
                </article>
              ))}
            </section>
          )}
        </>
      )}
    </div>
  )
}
