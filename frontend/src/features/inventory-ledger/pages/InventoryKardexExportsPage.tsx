import { useEffect, useMemo, useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'
import { InventoryLedgerContextEmptyState } from '../components/InventoryLedgerContextEmptyState'
import { inventoryLedgerExportsApi } from '../api/inventoryLedgerExportsApi'
import type { InventoryKardexExportApi } from '../types/inventory-ledger-api'

type ExportFormat = 'CSV' | 'XLSX' | 'PDF' | 'JSON'

interface ExportForm {
  format: ExportFormat
  timezone: string
  warehouse_id: string
  product_id: string
  sku: string
  occurred_from: string
  occurred_to: string
}

const INITIAL_FORM: ExportForm = {
  format: 'CSV',
  timezone: 'America/Lima',
  warehouse_id: '',
  product_id: '',
  sku: '',
  occurred_from: '',
  occurred_to: '',
}

const FORMAT_OPTIONS: Array<{ value: ExportFormat; label: string; description: string; icon: 'document' | 'list' | 'grid' }> = [
  { value: 'CSV', label: 'CSV', description: 'Datos tabulares ligeros', icon: 'list' },
  { value: 'XLSX', label: 'Excel', description: 'Libro para análisis operativo', icon: 'document' },
  { value: 'PDF', label: 'PDF', description: 'Reporte técnico legible', icon: 'document' },
  { value: 'JSON', label: 'JSON', description: 'Estructura para integración', icon: 'grid' },
]

const TERMINAL_STATUSES = new Set(['COMPLETED', 'FAILED', 'EXPIRED'])

function statusStyle(status: string): string {
  if (status === 'COMPLETED') return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
  if (status === 'FAILED') return 'bg-red-50 text-red-700 ring-red-200'
  if (status === 'EXPIRED') return 'bg-slate-100 text-slate-600 ring-slate-200'
  return 'bg-orange-50 text-orange-700 ring-orange-200'
}

function formatDate(value: string | null): string {
  if (!value) return 'Pendiente'
  return new Date(value).toLocaleString('es-PE')
}

export function InventoryKardexExportsPage() {
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const canExport = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.export)
  const organizationId = currentContext.organization_id
  const [form, setForm] = useState<ExportForm>(INITIAL_FORM)
  const [createdExport, setCreatedExport] = useState<InventoryKardexExportApi | null>(null)

  const filters = useMemo<Record<string, unknown>>(() => Object.fromEntries(
    Object.entries({
      warehouse_id: form.warehouse_id || undefined,
      product_id: form.product_id || undefined,
      sku: form.sku || undefined,
      occurred_from: form.occurred_from ? `${form.occurred_from}T00:00:00Z` : undefined,
      occurred_to: form.occurred_to ? `${form.occurred_to}T23:59:59Z` : undefined,
    }).filter(([, value]) => value !== undefined),
  ), [form])

  const exportStatus = useQuery<InventoryKardexExportApi>(
    ['inventory-ledger', 'exports', organizationId, createdExport?.id],
    createdExport ? `/logistics/inventory/kardex/exports/${createdExport.id}` : '',
    organizationId && createdExport ? { organization_id: organizationId } : undefined,
    {
      enabled: canView && Boolean(organizationId) && Boolean(createdExport),
      refetchIntervalMs: createdExport && !TERMINAL_STATUSES.has(createdExport.status) ? 3000 : null,
      refetchOnWindowFocus: true,
    },
  )

  useEffect(() => {
    if (exportStatus.data) setCreatedExport(exportStatus.data)
  }, [exportStatus.data])

  const createExport = useMutation<void, InventoryKardexExportApi>(
    () => inventoryLedgerExportsApi.createExport(organizationId ?? '', {
      format: form.format,
      timezone: form.timezone.trim() || 'America/Lima',
      filters,
    }),
    { onSuccess: (result) => setCreatedExport(result) },
  )

  const currentExport = exportStatus.data ?? createdExport
  const activeFilterCount = Object.keys(filters).length

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Exportaciones" />
        <Alert variant="error">No tienes permisos para ver exportaciones.</Alert>
      </div>
    )
  }

  const startExport = () => {
    setCreatedExport(null)
    createExport.mutate(undefined)
  }

  const downloadExport = () => {
    if (!organizationId || !currentExport) return
    window.location.assign(`/api${inventoryLedgerExportsApi.downloadPath(organizationId, currentExport.id)}`)
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Evidencia"
        title="Exportar kardex técnico"
        description="Genera archivos asíncronos y auditables con los filtros del libro de inventario."
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona la organización a exportar"
          description="El archivo se genera dentro del alcance operativo elegido y nunca combina datos de organizaciones distintas."
        />
      )}

      {organizationId && (
        <>
          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(310px,0.6fr)]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Nueva exportación</p>
                  <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">Configura el archivo</h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Elige el formato y reduce el alcance cuando necesites entregar una evidencia específica.</p>
                </div>
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                  <LogisticsIcon name="arrow-down" size={23} aria-hidden="true" />
                </span>
              </div>

              <fieldset className="mt-7">
                <legend className="text-sm font-semibold text-slate-800">Formato de salida</legend>
                <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {FORMAT_OPTIONS.map((option) => {
                    const selected = form.format === option.value
                    return (
                      <label key={option.value} className={`cursor-pointer rounded-2xl border p-4 transition focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 ${selected ? 'border-blue-300 bg-blue-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
                        <input
                          type="radio"
                          name="export-format"
                          value={option.value}
                          checked={selected}
                          onChange={() => setForm((current) => ({ ...current, format: option.value }))}
                          className="sr-only"
                        />
                        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${selected ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-600'}`}>
                          <LogisticsIcon name={option.icon} size={17} aria-hidden="true" />
                        </span>
                        <span className="mt-3 block text-sm font-bold text-slate-950">{option.label}</span>
                        <span className="mt-1 block text-xs leading-5 text-slate-500">{option.description}</span>
                      </label>
                    )
                  })}
                </div>
              </fieldset>

              <div className="mt-7 grid gap-4 sm:grid-cols-2">
                <label>
                  <span className="text-sm font-semibold text-slate-700">Almacén ID</span>
                  <input type="text" value={form.warehouse_id} onChange={(event) => setForm((current) => ({ ...current, warehouse_id: event.target.value }))} placeholder="Todos los almacenes" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">Producto ID</span>
                  <input type="text" value={form.product_id} onChange={(event) => setForm((current) => ({ ...current, product_id: event.target.value }))} placeholder="Todos los productos" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">SKU</span>
                  <input type="text" value={form.sku} onChange={(event) => setForm((current) => ({ ...current, sku: event.target.value }))} placeholder="Ej. PROD-001" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">Zona horaria</span>
                  <input type="text" value={form.timezone} onChange={(event) => setForm((current) => ({ ...current, timezone: event.target.value }))} placeholder="America/Lima" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">Movimientos desde</span>
                  <input type="date" value={form.occurred_from} onChange={(event) => setForm((current) => ({ ...current, occurred_from: event.target.value }))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
                <label>
                  <span className="text-sm font-semibold text-slate-700">Movimientos hasta</span>
                  <input type="date" value={form.occurred_to} onChange={(event) => setForm((current) => ({ ...current, occurred_to: event.target.value }))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
              </div>

              <div className="mt-7 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{activeFilterCount ? `${activeFilterCount} filtros aplicados` : 'Toda la organización'}</p>
                  <p className="mt-1 text-xs text-slate-500">La generación ocurre en segundo plano y puede tardar según el volumen.</p>
                </div>
                {canExport ? (
                  <Button onClick={startExport} isLoading={createExport.isPending} loadingLabel="Solicitando…">Generar exportación</Button>
                ) : (
                  <span className="rounded-xl bg-orange-50 px-3 py-2 text-xs font-semibold text-orange-700">Sin capacidad de exportación</span>
                )}
              </div>

              {createExport.error && <p className="mt-3 text-sm text-red-600" role="alert">{createExport.error}</p>}
            </div>

            <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-300">Qué incluye</p>
              <h2 className="mt-2 text-xl font-bold">Evidencia lista para auditoría</h2>
              <ul className="mt-6 space-y-5">
                {([
                  ['timeline' as const, 'Secuencia del ledger', 'Orden técnico y códigos de movimiento.'],
                  ['package' as const, 'Detalle operativo', 'Productos, cantidades, unidades y posiciones.'],
                  ['shield' as const, 'Referencia de integridad', 'Hashes parciales y estado de compensación.'],
                ] as const).map(([icon, title, description]) => (
                  <li key={title} className="flex gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sky-300"><LogisticsIcon name={icon} size={17} aria-hidden="true" /></span>
                    <div><p className="text-sm font-semibold">{title}</p><p className="mt-1 text-xs leading-5 text-slate-300">{description}</p></div>
                  </li>
                ))}
              </ul>
              <div className="mt-7 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-slate-300">El backend no expone un historial global de archivos. Esta pantalla sigue únicamente la exportación creada en la sesión actual.</div>
            </aside>
          </section>

          {exportStatus.isLoading && createdExport && <LoadingSkeleton rows={3} />}
          {exportStatus.isError && <Alert variant="error">{getErrorMessage(exportStatus.error)}</Alert>}

          {currentExport && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" aria-labelledby="export-status-title">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Exportación actual</p>
                  <h2 id="export-status-title" className="mt-2 text-xl font-bold text-slate-950">{currentExport.format} · {currentExport.id.slice(0, 8)}</h2>
                </div>
                <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-inset ${statusStyle(currentExport.status)}`}>
                  <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />{currentExport.status}
                </span>
              </div>

              <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Filas</dt><dd className="mt-2 text-xl font-bold text-slate-950">{currentExport.row_count.toLocaleString()}</dd></div>
                <div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Solicitada</dt><dd className="mt-2 text-sm font-semibold text-slate-900">{formatDate(currentExport.requested_at)}</dd></div>
                <div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Completada</dt><dd className="mt-2 text-sm font-semibold text-slate-900">{formatDate(currentExport.completed_at)}</dd></div>
                <div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Expira</dt><dd className="mt-2 text-sm font-semibold text-slate-900">{formatDate(currentExport.expires_at)}</dd></div>
              </dl>

              {currentExport.manifest_hash && <div className="mt-4 rounded-2xl border border-slate-200 px-4 py-3"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Hash del manifiesto</p><p className="mt-1 truncate font-mono text-xs text-slate-700">{currentExport.manifest_hash}</p></div>}
              {currentExport.warnings.length > 0 && <Alert variant="warning">La exportación terminó con {currentExport.warnings.length} advertencia(s).</Alert>}

              <div className="mt-5 flex flex-wrap gap-3">
                <Button onClick={downloadExport} disabled={currentExport.status !== 'COMPLETED'}><LogisticsIcon name="arrow-down" size={16} aria-hidden="true" />Descargar archivo</Button>
                {!TERMINAL_STATUSES.has(currentExport.status) && <span className="inline-flex items-center gap-2 text-sm text-slate-500"><span className="h-2 w-2 animate-pulse rounded-full bg-orange-500" aria-hidden="true" />Actualizando estado automáticamente</span>}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
