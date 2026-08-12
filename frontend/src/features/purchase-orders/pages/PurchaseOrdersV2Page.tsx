import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { purchaseOrdersV2Api } from '../api/purchaseOrdersV2Api'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui'
import {
  acknowledgementStatusLabel,
  approvalStatusLabel,
  dispatchStatusLabel,
  formatMoney,
  issuanceStatusLabel,
  purchaseOrderStatusLabel,
} from '../format'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import type { PurchaseOrderSummary } from '../types/phase034-contract'

type TabKey = 'drafts' | 'pending' | 'issued' | 'sent' | 'cancelled'

const PAGE_SIZE = 20
const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'drafts', label: 'Borradores' },
  { key: 'pending', label: 'Pendientes' },
  { key: 'issued', label: 'Emitidas' },
  { key: 'sent', label: 'Enviadas' },
  { key: 'cancelled', label: 'Canceladas' },
]

const STATUS_OPTIONS = [
  'DRAFT',
  'PENDING_APPROVAL',
  'RETURNED',
  'APPROVED',
  'ISSUED',
  'SENT',
  'ACKNOWLEDGED',
  'CANCELLED',
  'CLOSED',
] as const

const APPROVAL_OPTIONS = [
  'NOT_SUBMITTED',
  'PENDING',
  'APPROVED',
  'REJECTED',
  'RETURNED',
] as const

function tabQuery(tab: TabKey): {
  status?: string
  approval_status?: string
} {
  switch (tab) {
    case 'drafts':
      return { status: 'DRAFT' }
    case 'pending':
      return { approval_status: 'PENDING' }
    case 'issued':
      return { status: 'ISSUED' }
    case 'cancelled':
      return { status: 'CANCELLED' }
    case 'sent':
      return {}
  }
}

function matchesClientFilters(
  order: PurchaseOrderSummary,
  search: string,
  tab: TabKey,
): boolean {
  if (
    tab === 'sent' &&
    !['SENT', 'DELIVERED'].includes(order.dispatch_status)
  ) {
    return false
  }

  const normalized = search.trim().toLocaleLowerCase()
  if (!normalized) return true

  return [
    order.purchase_order_code,
    order.supplier_name,
    order.currency_code,
  ].some((value) => value?.toLocaleLowerCase().includes(normalized))
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-PE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function PurchaseOrdersV2Page() {
  const navigate = useNavigate()
  const permissions = useLogisticsPermissions()
  const canGenerate = permissions.hasPermission(
    LOGISTICS_PERMISSIONS.purchaseOrdersV2.generate,
  )

  const [tab, setTab] = useState<TabKey>('drafts')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [status, setStatus] = useState<string>('TAB')
  const [approvalStatus, setApprovalStatus] = useState<string>('TAB')
  const [page, setPage] = useState(1)
  const [items, setItems] = useState<PurchaseOrderSummary[]>([])
  const [hasNextPage, setHasNextPage] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const tabFilters = tabQuery(tab)
      const response = await purchaseOrdersV2Api.list({
        branch_id: permissions.context.branch_id,
        status: status === 'TAB' ? tabFilters.status : status,
        approval_status:
          approvalStatus === 'TAB'
            ? tabFilters.approval_status
            : approvalStatus,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      })
      setItems(response)
      setHasNextPage(response.length === PAGE_SIZE)
    } catch (error: unknown) {
      setItems([])
      setHasNextPage(false)
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudieron cargar las órdenes de compra.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [
    approvalStatus,
    page,
    permissions.context.branch_id,
    status,
    tab,
  ])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    setPage(1)
  }, [approvalStatus, status, tab])

  const visibleItems = useMemo(
    () =>
      items.filter((order) =>
        matchesClientFilters(order, debouncedSearch, tab),
      ),
    [debouncedSearch, items, tab],
  )

  return (
    <section className="space-y-4" aria-labelledby="purchase-orders-title">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
            Compras · Fase 034
          </p>
          <h1
            id="purchase-orders-title"
            className="mt-1 text-xl font-bold text-slate-950"
          >
            Órdenes de compra
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            Datos reales del servicio de procurement. Los importes mostrados
            provienen del backend y no se recalculan en el navegador.
          </p>
        </div>
        {canGenerate && (
          <button
            type="button"
            onClick={() =>
              navigate('/logistics/purchasing/purchase-orders/generate')
            }
            className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[#173a55] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D] focus:ring-offset-2"
          >
            Previsualizar desde decisión
          </button>
        )}
      </header>

      <div
        role="tablist"
        aria-label="Estado de las órdenes de compra"
        className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/70 p-1"
      >
        {TABS.map((item) => (
          <button
            key={item.key}
            role="tab"
            type="button"
            aria-selected={tab === item.key}
            onClick={() => {
              setTab(item.key)
              setStatus('TAB')
              setApprovalStatus('TAB')
            }}
            className={
              tab === item.key
                ? 'min-h-10 rounded-lg bg-white px-3 text-sm font-semibold text-[#1F4E6D] shadow-sm'
                : 'min-h-10 rounded-lg px-3 text-sm font-medium text-slate-600 hover:bg-white/80 hover:text-slate-900'
            }
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-[minmax(260px,1fr)_220px_220px]">
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-600">
            Buscar en esta página
          </span>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Código OC, proveedor o moneda"
            className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm outline-none transition focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-600">
            Estado
          </span>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="min-h-11 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TAB">Según pestaña</SelectItem>
              {STATUS_OPTIONS.map((value) => (
                <SelectItem key={value} value={value}>
                  {purchaseOrderStatusLabel(value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-600">
            Aprobación
          </span>
          <Select
            value={approvalStatus}
            onValueChange={setApprovalStatus}
          >
            <SelectTrigger className="min-h-11 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TAB">Según pestaña</SelectItem>
              {APPROVAL_OPTIONS.map((value) => (
                <SelectItem key={value} value={value}>
                  {approvalStatusLabel(value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {errorMessage ? (
          <div className="p-4">
            <ErrorState message={errorMessage} onRetry={() => void load()} />
          </div>
        ) : isLoading ? (
          <div className="p-4">
            <TableSkeleton />
          </div>
        ) : visibleItems.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="No hay órdenes para los filtros actuales"
              description="El servicio no devolvió órdenes en esta página y contexto operativo."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <caption className="sr-only">
                Órdenes de compra de la página {page}
              </caption>
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-3 py-3 text-left">OC</th>
                  <th scope="col" className="px-3 py-3 text-left">Proveedor</th>
                  <th scope="col" className="px-3 py-3 text-left">Moneda</th>
                  <th scope="col" className="px-3 py-3 text-right">Total</th>
                  <th scope="col" className="px-3 py-3 text-left">Estado</th>
                  <th scope="col" className="px-3 py-3 text-left">Aprobación</th>
                  <th scope="col" className="px-3 py-3 text-left">Emisión</th>
                  <th scope="col" className="px-3 py-3 text-left">Envío</th>
                  <th scope="col" className="px-3 py-3 text-left">Acuse</th>
                  <th scope="col" className="px-3 py-3 text-left">Actualización</th>
                  <th scope="col" className="px-3 py-3 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visibleItems.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-50/70">
                    <td className="px-3 py-3">
                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/logistics/purchasing/purchase-orders/${order.id}`,
                          )
                        }
                        className="min-h-10 font-mono text-xs font-bold text-[#1F4E6D] hover:underline focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
                      >
                        {order.purchase_order_code ?? 'Sin numerar'}
                      </button>
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {order.supplier_name ?? 'Proveedor sin nombre'}
                    </td>
                    <td className="px-3 py-3 text-xs">{order.currency_code}</td>
                    <td className="px-3 py-3 text-right font-mono text-xs">
                      {formatMoney(order.grand_total, order.currency_code)}
                    </td>
                    <td className="px-3 py-3">
                      <StatusPill tone="neutral">
                        {purchaseOrderStatusLabel(order.status)}
                      </StatusPill>
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {approvalStatusLabel(order.approval_status)}
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {issuanceStatusLabel(order.issuance_status)}
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {dispatchStatusLabel(order.dispatch_status)}
                    </td>
                    <td className="px-3 py-3 text-xs">
                      {acknowledgementStatusLabel(
                        order.acknowledgement_status,
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs text-slate-500">
                      {formatDate(order.updated_at)}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/logistics/purchasing/purchase-orders/${order.id}`,
                          )
                        }
                        className="min-h-10 rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Ver detalle
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
        <span>
          Página {page} · {visibleItems.length} elemento(s) visibles
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page === 1 || isLoading}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            className="min-h-10 rounded-lg border border-slate-200 px-3 font-semibold disabled:cursor-not-allowed disabled:opacity-40"
          >
            Anterior
          </button>
          <button
            type="button"
            disabled={!hasNextPage || isLoading}
            onClick={() => setPage((current) => current + 1)}
            className="min-h-10 rounded-lg border border-slate-200 px-3 font-semibold disabled:cursor-not-allowed disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </footer>
    </section>
  )
}
