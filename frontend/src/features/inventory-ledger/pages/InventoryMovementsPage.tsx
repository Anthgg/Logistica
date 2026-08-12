import { useEffect, useMemo, useState } from 'react'
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

type Tab = 'ALL' | 'ENTRY' | 'EXIT' | 'TRANSFER' | 'RESERVATION' | 'QUALITY' | 'PUTAWAY' | 'COMPENSATION'

interface InventoryMovementSummaryApi {
  id: string
  movement_code: string
  ledger_sequence: number
  movement_family: string
  movement_type: string
  status: string
  occurred_at: string
  posted_at: string
  warehouse_summary: { warehouse_id?: string } | null
  product_count: number
  line_count: number
  integrity_status: string
}

interface InventoryMovementListResponseApi {
  items: InventoryMovementSummaryApi[]
  total: number
  page: number
  page_size: number
}

interface InventoryMovementListFiltersApi extends Record<string, unknown> {
  organization_id: string
  page: number
  page_size: number
  movement_family?: string
  movement_type?: string
  search?: string
}

const TAB_LABELS: Record<Tab, string> = {
  ALL: 'Todos',
  ENTRY: 'Entradas',
  EXIT: 'Salidas',
  TRANSFER: 'Traslados',
  RESERVATION: 'Reservas',
  QUALITY: 'Calidad',
  PUTAWAY: 'Putaway',
  COMPENSATION: 'Compensaciones',
}

const TAB_FILTERS: Record<Tab, Pick<InventoryMovementListFiltersApi, 'movement_family' | 'movement_type'>> = {
  ALL: {},
  ENTRY: { movement_family: 'INBOUND' },
  EXIT: { movement_family: 'OUTBOUND' },
  TRANSFER: { movement_family: 'INTERNAL_TRANSFER' },
  RESERVATION: { movement_family: 'RESERVATION' },
  QUALITY: { movement_family: 'QUALITY_TRANSITION' },
  PUTAWAY: { movement_type: 'PUTAWAY_COMPLETED' },
  COMPENSATION: { movement_family: 'COMPENSATION' },
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  PREPARED: 'bg-yellow-100 text-yellow-700',
  POSTED: 'bg-green-100 text-green-700',
  FAILED: 'bg-red-100 text-red-700',
  COMPENSATED: 'bg-purple-100 text-purple-700',
  CANCELLED: 'bg-gray-100 text-gray-500',
  DISPUTED: 'bg-orange-100 text-orange-700',
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Borrador',
  PREPARED: 'Preparado',
  POSTED: 'Publicado',
  FAILED: 'Fallido',
  COMPENSATED: 'Compensado',
  CANCELLED: 'Cancelado',
  DISPUTED: 'En disputa',
}

export function InventoryMovementsPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext.organization_id
  const [activeTab, setActiveTab] = useState<Tab>('ALL')
  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  useEffect(() => {
    const id = window.setTimeout(() => setDebouncedSearch(searchInput), 300)
    return () => window.clearTimeout(id)
  }, [searchInput])

  const filters = useMemo<InventoryMovementListFiltersApi | null>(() => {
    if (!organizationId) return null
    const result: InventoryMovementListFiltersApi = {
      organization_id: organizationId,
      page: 1,
      page_size: 50,
      ...TAB_FILTERS[activeTab],
    }
    if (debouncedSearch.trim()) result.search = debouncedSearch.trim()
    return result
  }, [activeTab, debouncedSearch, organizationId])

  const movements = useQuery<InventoryMovementListResponseApi>(
    ['inventory-movements', organizationId, activeTab, debouncedSearch],
    '/logistics/inventory/movements',
    filters ?? undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Movimientos de inventario" />
        <Alert variant="error">No tienes permisos para ver los movimientos.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044"
        title="Movimientos de inventario"
        description="Listado técnico de movimientos del libro. Sin saldo editable."
        actions={
          <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger')}>
            Volver al tablero
          </Button>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona el ledger que deseas consultar"
          description="Los movimientos se filtran por organización para conservar el aislamiento y la trazabilidad del libro."
        />
      )}

      {organizationId && (
        <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm md:p-5" aria-label="Filtros de movimientos">
          <label className="block">
            <span className="text-sm font-semibold text-slate-800">Buscar en el libro</span>
            <span className="relative mt-2 block">
              <LogisticsIcon name="search" size={18} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <input
                type="search"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Código MOV, SKU, fuente o correlation ID"
                className="min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 py-2.5 pl-11 pr-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50"
              />
            </span>
          </label>

          <div className="mt-4 flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Familias de movimiento">
            {(Object.keys(TAB_LABELS) as Tab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                role="tab"
                aria-selected={activeTab === tab}
                onClick={() => setActiveTab(tab)}
                className={`min-h-10 shrink-0 rounded-xl px-3.5 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-950'
                }`}
              >
                {TAB_LABELS[tab]}
              </button>
            ))}
          </div>
        </section>
      )}

      {movements.isLoading && <LoadingSkeleton rows={8} />}

      {movements.isError && (
        <Alert variant="error">{getErrorMessage(movements.error)}</Alert>
      )}

      {movements.data && (
        <section className="space-y-3" aria-labelledby="movement-results-title">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Resultado</p>
              <h2 id="movement-results-title" className="mt-1 text-xl font-bold text-slate-950">
                {movements.data.total.toLocaleString()} movimiento(s)
              </h2>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              Página {movements.data.page}
            </span>
          </div>
          {movements.data.items.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center shadow-sm">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
                <LogisticsIcon name="archive" size={24} aria-hidden="true" />
              </div>
              <h3 className="mt-5 font-bold text-slate-950">Sin movimientos para estos filtros</h3>
              <p className="mt-2 text-sm text-slate-500">Prueba otra familia o elimina el texto de búsqueda.</p>
            </div>
          ) : (
            movements.data.items.map((m) => (
              <article
                key={m.id}
                className="group flex cursor-pointer flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md sm:flex-row sm:items-center sm:justify-between"
                onClick={() => navigate(`/logistics/inventory/ledger/movements/${m.id}`)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                    <LogisticsIcon name="package" size={20} aria-hidden="true" />
                  </span>
                  <div className="min-w-0">
                    <h3 className="truncate font-semibold text-slate-950">{m.movement_code}</h3>
                    <p className="mt-1 truncate text-sm text-slate-500">
                      Secuencia #{m.ledger_sequence} · {m.movement_type} ·{' '}
                      {m.warehouse_summary?.warehouse_id
                        ? `Almacén ${m.warehouse_summary.warehouse_id.slice(0, 8)}`
                        : 'Sin almacén'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-between gap-3 text-sm sm:justify-end">
                  <span className="text-slate-500">
                    {new Date(m.occurred_at).toLocaleDateString()}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[m.status] ?? 'bg-gray-100 text-gray-700'}`}>
                    {STATUS_LABELS[m.status] ?? m.status}
                  </span>
                  {m.integrity_status !== 'OK' && (
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      m.integrity_status === 'FAILED' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {m.integrity_status}
                    </span>
                  )}
                  <LogisticsIcon name="arrow-right" size={17} className="text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-blue-600" aria-hidden="true" />
                </div>
              </article>
            ))
          )}
        </section>
      )}
    </div>
  )
}
