import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PageHeader } from '../../../components/common/PageHeader'
import { getErrorMessage } from '../../../utils/errors'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { QualityQuarantineContextEmptyState } from '../components/QualityQuarantineContextEmptyState'
import { QualityQuarantinePhaseNav } from '../components/QualityQuarantinePhaseNav'
import type { QualityAvailabilityApi, QualityQuarantineCaseSummaryApi, QuarantineZoneApi } from '../types/phase042-api'

function label(value: string): string {
  return value.replaceAll('_', ' ').toLocaleLowerCase('es-PE')
}

export function QualityQuarantineDashboardPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const warehouseId = currentContext.warehouse_id

  const cases = useQuery<QualityQuarantineCaseSummaryApi[]>(
    ['quality-quarantine', 'dashboard-cases', warehouseId],
    '/logistics/quality-quarantine-cases',
    warehouseId ? { warehouse_id: warehouseId } : undefined,
    { enabled: Boolean(warehouseId) },
  )
  const zones = useQuery<QuarantineZoneApi[]>(
    ['quality-quarantine', 'dashboard-zones', warehouseId],
    '/logistics/quarantine-zones',
    warehouseId ? { warehouse_id: warehouseId } : undefined,
    { enabled: Boolean(warehouseId) },
  )
  const availability = useQuery<QualityAvailabilityApi[]>(
    ['quality-quarantine', 'dashboard-availability', warehouseId],
    '/logistics/quality-availability',
    warehouseId ? { warehouse_id: warehouseId } : undefined,
    { enabled: Boolean(warehouseId) },
  )

  const summary = useMemo(() => {
    const rows = cases.data ?? []
    const available = availability.data ?? []
    return {
      open: rows.filter((row) => !['CLOSED', 'CANCELLED'].includes(row.status)).length,
      pendingQuality: rows.filter((row) => !row.quality_result).length,
      releasedCases: rows.filter((row) => ['RELEASED', 'EXECUTED'].includes(row.release_status)).length,
      released: available.filter((row) => row.availability_class === 'AVAILABLE_FOR_PUTAWAY').length,
      blocked: available.filter((row) => row.availability_class === 'BLOCKED_QUARANTINE').length,
      activeZones: (zones.data ?? []).filter((row) => row.status === 'ACTIVE').length,
    }
  }, [availability.data, cases.data, zones.data])

  const isLoading = cases.isLoading || zones.isLoading || availability.isLoading
  const firstError = cases.error ?? zones.error ?? availability.error

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 042 · Control de calidad"
        title="Cuarentena y liberación"
        description="Decide qué inventario puede avanzar, qué necesita inspección y qué debe permanecer segregado."
        actions={<Button size="small" onClick={() => navigate('/logistics/quality/quarantine/cases')}>Abrir casos</Button>}
      />
      <QualityQuarantinePhaseNav />

      {!warehouseId && <QualityQuarantineContextEmptyState />}

      {warehouseId && (
        <>
          <section className="relative overflow-hidden rounded-3xl bg-slate-950 px-6 py-8 text-white shadow-sm md:px-9 md:py-10">
            <div className="absolute -right-16 -top-24 h-72 w-72 rounded-full bg-blue-500/20 blur-3xl" aria-hidden="true" />
            <div className="relative grid gap-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">Pulso del almacén</p>
                <h2 className="mt-3 max-w-2xl text-3xl font-bold tracking-tight md:text-4xl">Cada liberación conserva su decisión y su evidencia.</h2>
                <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300 md:text-base">El resumen se deriva de los casos, zonas y proyecciones reales del almacén seleccionado; no depende de un endpoint de dashboard inexistente.</p>
                <div className="mt-6 flex flex-wrap gap-3"><Button onClick={() => navigate('/logistics/quality/quarantine/cases')}>Gestionar cola</Button><Button variant="secondary" onClick={() => navigate('/logistics/quality/availability')}>Ver disponibilidad</Button></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4"><p className="text-xs text-slate-400">Zonas activas</p><p className="mt-2 text-3xl font-bold">{summary.activeZones}</p></div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4"><p className="text-xs text-slate-400">Bloqueos vigentes</p><p className="mt-2 text-3xl font-bold text-orange-300">{summary.blocked}</p></div>
              </div>
            </div>
          </section>

          {isLoading && <LoadingSkeleton rows={6} />}
          {firstError && <Alert variant="error">{getErrorMessage(firstError)}</Alert>}

          {!isLoading && !firstError && (
            <>
              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores de cuarentena">
                {([
                  ['archive' as const, 'Casos abiertos', summary.open, 'Requieren seguimiento', 'bg-blue-50 text-blue-700'],
                  ['search' as const, 'Pendientes de resultado', summary.pendingQuality, 'Sin resultado de calidad', 'bg-violet-50 text-violet-700'],
                  ['clock' as const, 'Casos liberados', summary.releasedCases, 'Autorización ejecutada', 'bg-orange-50 text-orange-700'],
                  ['check' as const, 'Listos para ubicación', summary.released, 'Proyección liberada', 'bg-emerald-50 text-emerald-700'],
                ] as const).map(([icon, title, value, detail, tone]) => (
                  <article key={title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-sm text-slate-500">{title}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{value}</p><p className="mt-2 text-xs text-slate-500">{detail}</p></div><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${tone}`}><LogisticsIcon name={icon} size={20} aria-hidden="true" /></span></div></article>
                ))}
              </section>

              <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
                <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm md:p-6">
                  <div className="flex items-center justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Cola reciente</p><h2 className="mt-1 text-xl font-bold text-slate-950">Casos que requieren atención</h2></div><Button size="small" variant="ghost" onClick={() => navigate('/logistics/quality/quarantine/cases')}>Ver todos</Button></div>
                  {(cases.data ?? []).length === 0 ? <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-5 py-9 text-center"><p className="font-semibold text-slate-900">Sin casos en este almacén</p><p className="mt-2 text-sm text-slate-500">La cola se llenará cuando una recepción sea puesta en cuarentena.</p></div> : <div className="mt-5 divide-y divide-slate-100">{(cases.data ?? []).slice(0, 6).map((row) => <button key={row.id} type="button" onClick={() => navigate(`/logistics/quality/quarantine/${row.id}`)} className="flex min-h-16 w-full items-center justify-between gap-4 rounded-xl px-2 py-3 text-left transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"><div className="min-w-0"><p className="truncate font-mono text-xs font-bold text-blue-700">{row.quarantine_code}</p><p className="mt-1 truncate text-sm text-slate-600">Resultado: {row.quality_result ? label(row.quality_result) : 'pendiente'}</p></div><div className="text-right"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{label(row.status)}</span><p className="mt-1 text-xs text-slate-400">{row.severity.toLocaleLowerCase('es-PE')}</p></div></button>)}</div>}
                </div>
                <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-50 text-orange-700"><LogisticsIcon name="shield" size={22} aria-hidden="true" /></span><h2 className="mt-5 text-xl font-bold text-slate-950">Secuencia controlada</h2><ol className="mt-5 space-y-4 text-sm text-slate-600">{['Registrar o activar el caso', 'Materializar y ejecutar la inspección', 'Proponer y aprobar la disposición', 'Liberar, rechazar o mantener segregado'].map((step, index) => <li key={step} className="flex gap-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-950 text-xs font-bold text-white">{index + 1}</span><span className="pt-1">{step}</span></li>)}</ol></aside>
              </section>
            </>
          )}
        </>
      )}
    </div>
  )
}
