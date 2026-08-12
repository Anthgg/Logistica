import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'
import { InventoryLedgerContextEmptyState } from '../components/InventoryLedgerContextEmptyState'
import type {
  InventoryKardexResponseApi,
  InventoryKardexRunningQuantityRowApi,
} from '../types/inventory-ledger-api'

interface KardexFilters {
  search: string
  sku: string
  warehouse_id: string
  product_id: string
  base_unit_id: string
  occurred_from: string
  occurred_to: string
}

const EMPTY_FILTERS: KardexFilters = {
  search: '',
  sku: '',
  warehouse_id: '',
  product_id: '',
  base_unit_id: '',
  occurred_from: '',
  occurred_to: '',
}

function buildKardexParams(organizationId: string, filters: KardexFilters): Record<string, unknown> {
  return {
    organization_id: organizationId,
    page: 1,
    page_size: 50,
    sort_by: 'ledger_sequence',
    sort_direction: 'DESC',
    search: filters.search || undefined,
    sku: filters.sku || undefined,
    warehouse_id: filters.warehouse_id || undefined,
    product_id: filters.product_id || undefined,
    occurred_from: filters.occurred_from ? `${filters.occurred_from}T00:00:00Z` : undefined,
    occurred_to: filters.occurred_to ? `${filters.occurred_to}T23:59:59Z` : undefined,
  }
}

export function InventoryKardexPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext.organization_id
  const [draft, setDraft] = useState<KardexFilters>(EMPTY_FILTERS)
  const [applied, setApplied] = useState<KardexFilters>(EMPTY_FILTERS)

  const params = useMemo(
    () => (organizationId ? buildKardexParams(organizationId, applied) : undefined),
    [applied, organizationId],
  )

  const kardex = useQuery<InventoryKardexResponseApi>(
    ['inventory-kardex', organizationId, applied],
    '/logistics/inventory/kardex',
    params,
    { enabled: canView && Boolean(organizationId) },
  )

  const canCalculateRunning = Boolean(
    organizationId && draft.warehouse_id && draft.product_id && draft.base_unit_id,
  )

  const runningQty = useQuery<InventoryKardexRunningQuantityRowApi[]>(
    ['inventory-kardex', 'running', organizationId, applied.warehouse_id, applied.product_id, applied.base_unit_id],
    '/logistics/inventory/kardex/technical-running-quantity',
    organizationId && applied.warehouse_id && applied.product_id && applied.base_unit_id
      ? {
          organization_id: organizationId,
          warehouse_id: applied.warehouse_id,
          product_id: applied.product_id,
          base_unit_id: applied.base_unit_id,
        }
      : undefined,
    {
      enabled: canView && Boolean(
        organizationId && applied.warehouse_id && applied.product_id && applied.base_unit_id,
      ),
    },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Kardex técnico" />
        <Alert variant="error">No tienes permisos para consultar el kardex.</Alert>
      </div>
    )
  }

  const setField = (field: keyof KardexFilters, value: string) => {
    setDraft((current) => ({ ...current, [field]: value }))
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Consulta técnica"
        title="Kardex técnico"
        description="Reproduce el libro por producto, almacén, SKU y periodo sin alterar saldos."
        actions={
          <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger/exports')}>
            Preparar exportación
          </Button>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona la organización del kardex"
          description="La consulta técnica siempre se ejecuta dentro de un único ledger organizacional."
        />
      )}

      {organizationId && (
        <>
          <Alert variant="info">
            Esta vista reproduce movimientos del libro. El saldo operativo reconciliable corresponde a la Fase 045.
          </Alert>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm md:p-6" aria-labelledby="kardex-filters-title">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Consulta avanzada</p>
                <h2 id="kardex-filters-title" className="mt-1 text-xl font-bold text-slate-950">Dimensiones del kardex</h2>
                <p className="mt-1 text-sm text-slate-500">Completa solo los campos que necesites para reducir el libro.</p>
              </div>
              <button
                type="button"
                onClick={() => { setDraft(EMPTY_FILTERS); setApplied(EMPTY_FILTERS) }}
                className="text-sm font-semibold text-blue-700 hover:text-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                Limpiar filtros
              </button>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[
                ['search', 'Búsqueda general', 'Código MOV, fuente o correlation ID'],
                ['sku', 'SKU', 'SKU exacto o parcial'],
                ['warehouse_id', 'Almacén ID', 'UUID del almacén'],
                ['product_id', 'Producto ID', 'UUID del producto'],
                ['base_unit_id', 'Unidad base ID', 'Requerida para saldo corrido'],
              ].map(([field, label, placeholder]) => (
                <label key={field} className="block">
                  <span className="text-sm font-semibold text-slate-700">{label}</span>
                  <input
                    type="text"
                    value={draft[field as keyof KardexFilters]}
                    onChange={(event) => setField(field as keyof KardexFilters, event.target.value)}
                    placeholder={placeholder}
                    className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"
                  />
                </label>
              ))}

              <div className="grid grid-cols-2 gap-3">
                <label className="block">
                  <span className="text-sm font-semibold text-slate-700">Desde</span>
                  <input type="date" value={draft.occurred_from} onChange={(event) => setField('occurred_from', event.target.value)} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
                <label className="block">
                  <span className="text-sm font-semibold text-slate-700">Hasta</span>
                  <input type="date" value={draft.occurred_to} onChange={(event) => setField('occurred_to', event.target.value)} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" />
                </label>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button onClick={() => setApplied(draft)}>Aplicar filtros</Button>
              <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ${canCalculateRunning ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${canCalculateRunning ? 'bg-emerald-500' : 'bg-slate-400'}`} aria-hidden="true" />
                {canCalculateRunning ? 'Saldo corrido disponible al aplicar' : 'Completa almacén, producto y unidad para saldo corrido'}
              </span>
            </div>
          </section>

          {kardex.isLoading && <LoadingSkeleton rows={8} />}
          {kardex.isError && <Alert variant="error">{getErrorMessage(kardex.error)}</Alert>}

          {kardex.data && (
            <section className="space-y-4" aria-labelledby="kardex-results-title">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Libro reproducido</p><h2 id="kardex-results-title" className="mt-1 text-xl font-bold text-slate-950">{kardex.data.total.toLocaleString()} registro(s)</h2></div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Página {kardex.data.page}</span>
              </div>

              {kardex.data.items.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center shadow-sm">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600"><LogisticsIcon name="search" size={24} aria-hidden="true" /></div>
                  <h3 className="mt-5 font-bold text-slate-950">No hay coincidencias en el libro</h3>
                  <p className="mt-2 text-sm text-slate-500">Ajusta las dimensiones o consulta todos los movimientos.</p>
                </div>
              ) : (
                <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-sm">
                      <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">Secuencia</th><th className="px-5 py-3">Movimiento</th><th className="px-5 py-3">Producto</th><th className="px-5 py-3">Dirección</th><th className="px-5 py-3">Cantidad base</th><th className="px-5 py-3">Fecha</th></tr></thead>
                      <tbody className="divide-y divide-slate-100">
                        {kardex.data.items.map((row) => (
                          <tr key={`${row.movement_id}-${row.line_number ?? 0}`} className="cursor-pointer transition hover:bg-blue-50/40" onClick={() => navigate(`/logistics/inventory/ledger/movements/${row.movement_id}`)}>
                            <td className="px-5 py-4 font-semibold text-slate-900">#{row.ledger_sequence}</td>
                            <td className="px-5 py-4"><p className="font-semibold text-slate-900">{row.movement_code}</p><p className="mt-1 text-xs text-slate-500">{row.movement_type}</p></td>
                            <td className="px-5 py-4 font-mono text-xs text-slate-600">{row.product_id.slice(0, 12)}…</td>
                            <td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${row.quantity_direction === 'IN' ? 'bg-emerald-50 text-emerald-700' : row.quantity_direction === 'OUT' ? 'bg-orange-50 text-orange-700' : 'bg-blue-50 text-blue-700'}`}>{row.quantity_direction ?? 'INTERNAL'}</span></td>
                            <td className="px-5 py-4 font-semibold text-slate-900">{row.signed_base_quantity_display ?? row.base_quantity}</td>
                            <td className="px-5 py-4 text-slate-500">{new Date(row.occurred_at).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          )}

          {runningQty.isLoading && <LoadingSkeleton rows={4} />}
          {runningQty.isError && <Alert variant="error">{getErrorMessage(runningQty.error)}</Alert>}
          {runningQty.data && (
            <section className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
              <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 text-sky-300"><LogisticsIcon name="timeline" size={21} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-wide text-orange-300">Replay técnico</p><h2 className="mt-1 text-xl font-bold">Saldo corrido de referencia</h2></div></div>
              <div className="mt-5 space-y-2">
                {runningQty.data.map((row) => (
                  <div key={`${row.movement_id}-${row.line_number}`} className="grid gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm sm:grid-cols-[90px_1fr_140px_140px] sm:items-center">
                    <span className="text-slate-400">#{row.ledger_sequence}</span><span className="font-medium text-white">{row.movement_code}</span><span className={Number(row.signed_delta) >= 0 ? 'text-emerald-300' : 'text-orange-300'}>{Number(row.signed_delta) >= 0 ? '+' : ''}{row.signed_delta}</span><span className="font-semibold text-white">Saldo {row.running_quantity_reference}</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
